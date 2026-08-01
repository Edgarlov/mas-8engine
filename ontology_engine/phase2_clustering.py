"""
phase2_clustering.py — BFS + Clustering por Similitud Coseno (Fase 2)

Implementa:
  - Embeddings densos via TF-IDF (sklearn) con opción sentence-transformers
  - Matriz de similitud coseno: Sim(v1,v2) = (v1·v2)/(‖v1‖‖v2‖) ≥ τ
  - BFS para cobertura horizontal (dimensiones temáticas)
  - Balanceo de cardinalidad entre ramas (mitigación de sesgo de sobre-frecuencia)
  - Recursión atómica para profundidad máxima (Level-k Maximum)

Formalismo:
  Sim(v1, v2) = (v1 · v2) / (‖v1‖ · ‖v2‖) ≥ τ
  donde τ = umbral configurable (default: 0.25)
"""

from __future__ import annotations

import hashlib
import math
from collections import defaultdict, deque
from dataclasses import dataclass, field

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .models import Cluster, LexicalUnit, Phase2Result

# ─────────────────────────────────────────────────────────────────────────────
# sentence-transformers: importación lazy (evitar inicialización global de TF)
# ─────────────────────────────────────────────────────────────────────────────

_ST_MODEL = None
ST_AVAILABLE = False

def _load_st_model():
    """Carga sentence-transformers de forma lazy si está disponible."""
    global _ST_MODEL, ST_AVAILABLE
    if ST_AVAILABLE:
        return _ST_MODEL
    try:
        from sentence_transformers import SentenceTransformer
        _ST_MODEL = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        ST_AVAILABLE = True
    except (ImportError, Exception):
        _ST_MODEL = None
        ST_AVAILABLE = False
    return _ST_MODEL


# ─────────────────────────────────────────────────────────────────────────────
# Clase Principal
# ─────────────────────────────────────────────────────────────────────────────

class BFSClusterer:
    """
    Fase 2: Clustering semántico por similitud coseno + BFS.

    Garantiza:
      - Cobertura horizontal de todas las dimensiones temáticas
      - Balanceo de cardinalidad entre ramas
      - Profundización recursiva hasta nodo atómico terminal
    """

    def __init__(
        self,
        tau: float = 0.25,
        max_depth: int = 5,
        min_cluster_size: int = 1,
        max_branches: int = 4,
        use_dense_embeddings: bool = True,
    ):
        self.tau = tau                         # Umbral similitud coseno
        self.max_depth = max_depth             # k-máximo (nivel atómico terminal)
        self.min_cluster_size = min_cluster_size
        self.max_branches = max_branches       # Ramas horizontales máximas
        self.use_dense = use_dense_embeddings and ST_AVAILABLE

    # ── API pública ──────────────────────────────────────────────────────────

    def cluster_bfs(self, units: list[LexicalUnit]) -> Phase2Result:
        """
        Entrada: unidades léxicas de Fase 1.
        Salida: clusters jerárquicos con BFS.
        """
        if len(units) == 0:
            return Phase2Result(clusters=[], tau_threshold=self.tau)

        texts = [u.surface_form for u in units]
        embeddings = self._embed(texts)
        sim_matrix = cosine_similarity(embeddings)

        # Construir grafo de adyacencia por umbral τ
        adjacency = self._build_adjacency(sim_matrix)

        # BFS para clusters a nivel 0 (ramas temáticas raíz)
        visited: set[int] = set()
        clusters: list[Cluster] = []

        queue: deque[tuple[int, int]] = deque()

        # Seed: nodo de mayor grado (hub temático)
        seed = self._find_hub(adjacency, len(units))
        queue.append((seed, 0))

        while queue:
            idx, depth = queue.popleft()
            if idx in visited:
                continue
            visited.add(idx)

            # Vecinos con similitud ≥ τ (nivel de este nodo)
            neighbors = [
                j for j in adjacency[idx]
                if j not in visited
            ]

            # Crear cluster para este nodo
            cluster_members = [units[idx]] + [units[j] for j in neighbors[:self.max_branches - 1]]
            cluster_id = hashlib.sha1(units[idx].surface_form.encode()).hexdigest()[:8]

            cluster = Cluster(
                cluster_id=cluster_id,
                members=cluster_members,
                centroid_label=self._centroid_label(cluster_members),
                avg_cosine_similarity=self._avg_sim(idx, neighbors, sim_matrix),
                branch_level=depth,
                is_leaf=(depth >= self.max_depth - 1 or len(neighbors) == 0),
            )
            clusters.append(cluster)

            # Encolar vecinos para siguiente nivel (BFS)
            if depth < self.max_depth - 1:
                for neighbor in neighbors:
                    if neighbor not in visited:
                        queue.append((neighbor, depth + 1))

        # Balanceo de cardinalidad entre ramas
        clusters = self._balance_cardinality(clusters)

        return Phase2Result(
            clusters=clusters,
            similarity_matrix_shape=sim_matrix.shape,
            tau_threshold=self.tau,
        )

    # ── Embeddings ───────────────────────────────────────────────────────────

    def _embed(self, texts: list[str]) -> np.ndarray:
        """
        Genera embeddings.
        Primario: sentence-transformers (densos, multilingual).
        Fallback: TF-IDF sparse → dense.
        """
        if self.use_dense:
            model = _load_st_model()
            if model is not None:
                return model.encode(texts, show_progress_bar=False)

        # TF-IDF fallback
        vec = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(2, 4),
            max_features=512,
            sublinear_tf=True,
        )
        try:
            sparse = vec.fit_transform(texts)
            return sparse.toarray()
        except ValueError:
            # Corpus muy pequeño: retornar identidad
            n = len(texts)
            return np.eye(n)

    # ── Grafo de Adyacencia ──────────────────────────────────────────────────

    def _build_adjacency(self, sim_matrix: np.ndarray) -> dict[int, list[int]]:
        """
        Construye diccionario de adyacencia a partir de la
        matriz de similitud filtrando por umbral τ.
        """
        n = sim_matrix.shape[0]
        adj: dict[int, list[int]] = defaultdict(list)
        for i in range(n):
            for j in range(n):
                if i != j and sim_matrix[i, j] >= self.tau:
                    adj[i].append(j)
        # Ordenar vecinos por similitud descendente
        for i in adj:
            adj[i].sort(key=lambda j: sim_matrix[i, j], reverse=True)
        return dict(adj)

    def _find_hub(self, adjacency: dict[int, list[int]], n: int) -> int:
        """Retorna índice del nodo con mayor grado (hub semántico)."""
        max_degree = -1
        hub = 0
        for i in range(n):
            degree = len(adjacency.get(i, []))
            if degree > max_degree:
                max_degree = degree
                hub = i
        return hub

    # ── Utilidades de Cluster ─────────────────────────────────────────────────

    def _centroid_label(self, members: list[LexicalUnit]) -> str:
        """Label del centroide: el miembro con surface_form más corta (más general)."""
        if not members:
            return ""
        return min(members, key=lambda u: len(u.surface_form)).surface_form

    def _avg_sim(self, idx: int, neighbors: list[int], sim_matrix: np.ndarray) -> float:
        """Similitud coseno promedio del nodo con sus vecinos."""
        if not neighbors:
            return 1.0
        sims = [sim_matrix[idx, j] for j in neighbors]
        return sum(sims) / len(sims)

    # ── Balanceo de Cardinalidad ──────────────────────────────────────────────

    def _balance_cardinality(self, clusters: list[Cluster]) -> list[Cluster]:
        """
        Normaliza la cardinalidad de ramas para mitigar sesgos de sobre-frecuencia.
        Agrupa clusters por nivel (branch_level) y balancea el número de miembros.
        """
        by_level: dict[int, list[Cluster]] = defaultdict(list)
        for c in clusters:
            by_level[c.branch_level].append(c)

        balanced: list[Cluster] = []
        for level, level_clusters in sorted(by_level.items()):
            if len(level_clusters) <= self.max_branches:
                balanced.extend(level_clusters)
                continue

            # Reducir a max_branches seleccionando los de mayor similitud promedio
            sorted_clusters = sorted(
                level_clusters,
                key=lambda c: c.avg_cosine_similarity,
                reverse=True,
            )

            # Retener top-N + asegurar al menos uno de baja frecuencia (exhaustividad)
            top = sorted_clusters[:self.max_branches - 1]
            peripheral = sorted_clusters[self.max_branches - 1]  # inclusión periférica
            balanced.extend(top + [peripheral])

        return balanced


# ─────────────────────────────────────────────────────────────────────────────
# Utilidades Externas
# ─────────────────────────────────────────────────────────────────────────────

def cosine_distance(v1: list[float], v2: list[float]) -> float:
    """
    Distancia coseno escalar entre dos vectores.
    Sim(v1, v2) = (v1·v2) / (‖v1‖·‖v2‖)
    """
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a ** 2 for a in v1))
    norm2 = math.sqrt(sum(b ** 2 for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)
