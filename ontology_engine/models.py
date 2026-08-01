"""
models.py — Estructuras de datos centrales del motor de ingeniería ontológica v2.0

Implements formal data model for:
  - Lexical nodes (SNC, atomic, imperative)
  - Ontology graph with MECE guarantees
  - Pipeline results per phase
  - SKOS/JSON-LD export structures

All identifiers follow IRI pattern: urn:nodo:{notation}
UUID v4 assigned for polysemy disambiguation.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


# ─────────────────────────────────────────────────────────────────────────────
# Enumeraciones
# ─────────────────────────────────────────────────────────────────────────────

class NodeRole(Enum):
    """Rol semántico del nodo en la jerarquía ontológica."""
    ROOT        = "root"          # Rama raíz (nivel 0)
    BRANCH      = "branch"        # Nodo intermedio
    ATOMIC      = "atomic"        # Nodo terminal indivisible (Level-k max)
    ORPHAN      = "orphan"        # Sin relación a raíz — candidato a purga


class RelationType(Enum):
    """Tipos de relación válidos para el grafo (no-huérfano)."""
    IS_A        = "IS-A"
    PART_OF     = "PART-OF"
    PRECEDES    = "PRECEDES"
    EQUIVALENT  = "EQUIVALENT"
    NARROWER    = "skos:narrower"
    BROADER     = "skos:broader"


class SyntacticPattern(Enum):
    """Patrones sintácticos detectados en Fase 1."""
    NOUN_ADJ            = auto()  # NOUN + ADJ
    NOUN_PREP_NOUN      = auto()  # NOUN + PREP + NOUN
    VERB_NOUN           = auto()  # VP_imp — post transmutación
    UNKNOWN             = auto()


# ─────────────────────────────────────────────────────────────────────────────
# Unidades Léxicas
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class LexicalUnit:
    """
    Unidad léxica bruta extraída del corpus.
    Resultado de Fase 1 (filtrado morfosintáctico).
    """
    surface_form: str                          # Forma superficial original
    pattern: SyntacticPattern                  # Patrón POS detectado
    pos_tags: list[str] = field(default_factory=list)   # Tags POS
    dependency_labels: list[str] = field(default_factory=list)
    confidence: float = 1.0                    # Confianza de extracción [0, 1]
    source_position: int = -1                  # Offset en corpus original


@dataclass
class Cluster:
    """
    Cluster de sintagmas semánticamente próximos.
    Resultado de Fase 2 (BFS + coseno).
    """
    cluster_id: str
    members: list[LexicalUnit] = field(default_factory=list)
    centroid_label: str = ""
    avg_cosine_similarity: float = 0.0
    branch_level: int = 0                      # Nivel en árbol BFS
    is_leaf: bool = False


@dataclass
class CanonicalForm:
    """
    Forma canónica normalizada.
    Resultado de Fase 3 (lematización + WSD + IRI).
    """
    lemma: str                                 # Lema preferente
    surface_variants: list[str] = field(default_factory=list)
    acronym_expansion: str | None = None       # Expansión Schwartz-Hearst
    iri: str = ""                              # urn:nodo:{notation}
    uuid: str = field(default_factory=lambda: str(uuid.uuid4()))
    sense_id: int = 0                          # Índice de sentido (WSD)
    iso_standard: str | None = None            # [ISO/IEEE/SNOMED] si aplica
    is_polysemous: bool = False
    alt_senses: list[CanonicalForm] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# Nodo del Grafo
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class OntologyNode:
    """
    Nodo en el grafo imperativo normalizado.
    Combina forma canónica + primitiva imperativa MECE.
    """
    notation: str                              # "1.1.2.1" — decimal jerárquico
    canonical: CanonicalForm
    imperative_label: str = ""                 # [Verbo_Imp] + [Obj_Téc] + [Estándar]
    role: NodeRole = NodeRole.BRANCH
    children: list[OntologyNode] = field(default_factory=list)
    parent_notation: str | None = None
    relations: list[tuple[RelationType, str]] = field(default_factory=list)

    # MECE metadata
    mece_valid: bool = True
    mece_violations: list[str] = field(default_factory=list)

    # SAT/CDCL metadata
    sat_literal: int = 0                       # Literal CNF asignado al nodo
    is_consistent: bool = True

    @property
    def iri(self) -> str:
        return f"urn:nodo:{self.notation}"

    @property
    def depth(self) -> int:
        return len(self.notation.split(".")) - 1

    @property
    def is_atomic(self) -> bool:
        return self.role == NodeRole.ATOMIC or len(self.children) == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "notation": self.notation,
            "iri": self.iri,
            "imperative_label": self.imperative_label,
            "lemma": self.canonical.lemma,
            "uuid": self.canonical.uuid,
            "iso_standard": self.canonical.iso_standard,
            "role": self.role.value,
            "mece_valid": self.mece_valid,
            "children": [c.to_dict() for c in self.children],
        }


# ─────────────────────────────────────────────────────────────────────────────
# Grafo Ontológico
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class OntologyGraph:
    """
    Grafo imperativo normalizado completo (resultado de Fase 4).
    Garantiza propiedades MECE sobre todos los nodos hermanos.
    """
    scheme_id: str = "urn:engine:ontologia:grafo-imperativo-v2"
    title: str = "Grafo Imperativo Normalizado de Minería Léxica"
    creator: str = "OntologyEngine v2.0"
    top_concepts: list[OntologyNode] = field(default_factory=list)

    def all_nodes(self) -> list[OntologyNode]:
        """BFS sobre todo el grafo para retornar todos los nodos."""
        result: list[OntologyNode] = []
        queue = list(self.top_concepts)
        while queue:
            node = queue.pop(0)
            result.append(node)
            queue.extend(node.children)
        return result

    def atomic_nodes(self) -> list[OntologyNode]:
        return [n for n in self.all_nodes() if n.is_atomic]

    def orphan_nodes(self) -> list[OntologyNode]:
        return [n for n in self.all_nodes() if n.role == NodeRole.ORPHAN]

    def get_by_notation(self, notation: str) -> OntologyNode | None:
        for node in self.all_nodes():
            if node.notation == notation:
                return node
        return None

    def stats(self) -> dict[str, int]:
        all_n = self.all_nodes()
        return {
            "total_nodes": len(all_n),
            "atomic_nodes": len(self.atomic_nodes()),
            "orphan_nodes": len(self.orphan_nodes()),
            "max_depth": max((n.depth for n in all_n), default=0),
            "top_concepts": len(self.top_concepts),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Resultados por Fase
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Phase1Result:
    lexical_units: list[LexicalUnit]
    filtered_count: int = 0
    noise_removed: int = 0


@dataclass
class Phase2Result:
    clusters: list[Cluster]
    similarity_matrix_shape: tuple[int, int] = (0, 0)
    tau_threshold: float = 0.25


@dataclass
class Phase3Result:
    canonical_forms: list[CanonicalForm]
    polysemous_count: int = 0
    acronyms_expanded: int = 0


@dataclass
class Phase4Result:
    graph: OntologyGraph
    mece_violations: list[str] = field(default_factory=list)
    imperative_nodes: int = 0


@dataclass
class ValidationResult:
    """Resultado del validador SAT/CDCL."""
    is_satisfiable: bool = True
    kb_consistent: bool = True
    orphans_purged: int = 0
    cnf_clauses: int = 0
    violations: list[str] = field(default_factory=list)
    belief_retractions: list[str] = field(default_factory=list)


@dataclass
class OntologyResult:
    """Resultado integral del pipeline completo."""
    corpus_input: str
    phase1: Phase1Result
    phase2: Phase2Result
    phase3: Phase3Result
    phase4: Phase4Result
    validation: ValidationResult
    jsonld_export: dict[str, Any]
    tree_render: str = ""
    processing_time_ms: float = 0.0

    def summary(self) -> str:
        stats = self.phase4.graph.stats()
        return (
            f"Pipeline v2.0 — {stats['total_nodes']} nodos "
            f"({stats['atomic_nodes']} atómicos, depth={stats['max_depth']}) | "
            f"SAT={'✓' if self.validation.is_satisfiable else '✗'} | "
            f"MECE violations={len(self.phase4.mece_violations)} | "
            f"Orphans purged={self.validation.orphans_purged}"
        )
