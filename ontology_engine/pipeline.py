"""
pipeline.py — Orquestador Principal del Engine Ontológico v2.0

Implementa:
  - Coordinación secuencial de las 4 fases del pipeline
  - Gestión de configuración via PipelineConfig
  - Integración con SAT/CDCL validator y SKOSExporter
  - Métricas de rendimiento por fase
  - Renderizado de árbol ASCII

Flujo:
  corpus → Phase1 → Phase2 → Phase3 → Phase4 → Validation → Export
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Optional

from .exporter import SKOSExporter
from .models import OntologyResult, Phase4Result
from .phase1_filter import MorphosyntacticFilter
from .phase2_clustering import BFSClusterer
from .phase3_canonical import Canonicalizer
from .phase4_graph import ImperativeGraphBuilder
from .sat_validator import SATCDCLValidator


# ─────────────────────────────────────────────────────────────────────────────
# Configuración
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PipelineConfig:
    """Configuración unificada del pipeline."""
    # Fase 1
    min_confidence: float = 0.5
    lang: str = "es"

    # Fase 2
    tau: float = 0.25           # Umbral similitud coseno
    max_depth: int = 5           # k-máximo (Level-k Maximum)
    max_branches: int = 4        # Ramas horizontales máx
    use_dense_embeddings: bool = True

    # Fase 3
    iri_prefix: str = "urn:nodo:"
    context_window: int = 5

    # Fase 4
    use_spec_tree: bool = True   # Usar árbol del spec o construir desde corpus

    # Exportación
    json_ld_indent: int = 2
    output_format: str = "jsonld"  # "jsonld" | "turtle" | "flat"

    # General
    verbose: bool = False


# ─────────────────────────────────────────────────────────────────────────────
# Clase Principal
# ─────────────────────────────────────────────────────────────────────────────

class OntologyEnginePipeline:
    """
    Motor de Ingeniería Ontológica v2.0

    Implementa el pipeline completo de minería léxica y estructuración
    ontológica según la especificación formal:
      ESPECIFICACION_INGENIERIA_ONTOLOGICA.md

    Flujo:
      1. MorphosyntacticFilter   — Extracción SNC
      2. BFSClusterer            — Clustering semántico
      3. Canonicalizer           — Normalización + WSD + IRI
      4. ImperativeGraphBuilder  — MECE + renderizado imperativo
      5. SATCDCLValidator        — Consistencia lógica
      6. SKOSExporter            — JSON-LD SKOS
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()
        self._init_components()

    def _init_components(self):
        cfg = self.config
        self.phase1 = MorphosyntacticFilter(
            min_confidence=cfg.min_confidence,
            lang=cfg.lang,
        )
        self.phase2 = BFSClusterer(
            tau=cfg.tau,
            max_depth=cfg.max_depth,
            max_branches=cfg.max_branches,
            use_dense_embeddings=cfg.use_dense_embeddings,
        )
        self.phase3 = Canonicalizer(
            context_window=cfg.context_window,
            iri_prefix=cfg.iri_prefix,
        )
        self.phase4 = ImperativeGraphBuilder(
            use_spec_tree=cfg.use_spec_tree,
        )
        self.validator = SATCDCLValidator()
        self.exporter = SKOSExporter(language=cfg.lang)

    # ── API pública ──────────────────────────────────────────────────────────

    def process(self, corpus: str) -> OntologyResult:
        """
        Procesa corpus arbitrario a través del pipeline completo.

        Args:
            corpus: Texto de entrada (cualquier dominio técnico)

        Returns:
            OntologyResult con grafo, validación, árbol y JSON-LD
        """
        t0 = time.perf_counter()

        if self.config.verbose:
            print(f"[PIPELINE v2.0] Procesando corpus ({len(corpus)} chars)...")

        # ── Fase 1: Filtrado Morfosintáctico ──────────────────────────────────
        t1 = time.perf_counter()
        r1 = self.phase1.extract_snc(corpus)
        if self.config.verbose:
            print(f"  [P1] {r1.filtered_count} SNC extraídos, {r1.noise_removed} ruido eliminado ({(time.perf_counter()-t1)*1000:.1f}ms)")

        # ── Fase 2: BFS Clustering ────────────────────────────────────────────
        t2 = time.perf_counter()
        r2 = self.phase2.cluster_bfs(r1.lexical_units)
        if self.config.verbose:
            print(f"  [P2] {len(r2.clusters)} clusters generados, tau={r2.tau_threshold} ({(time.perf_counter()-t2)*1000:.1f}ms)")

        # ── Fase 3: Canonicalización ──────────────────────────────────────────
        t3 = time.perf_counter()
        r3 = self.phase3.canonicalize(r2.clusters, corpus)
        if self.config.verbose:
            print(f"  [P3] {len(r3.canonical_forms)} formas canónicas, {r3.polysemous_count} polisémicos, {r3.acronyms_expanded} acrónimos ({(time.perf_counter()-t3)*1000:.1f}ms)")

        # ── Fase 4: Grafo Imperativo ──────────────────────────────────────────
        t4 = time.perf_counter()
        r4 = self.phase4.build_graph(r3.canonical_forms)
        if self.config.verbose:
            print(f"  [P4] {r4.graph.stats()['total_nodes']} nodos, {len(r4.mece_violations)} violaciones MECE ({(time.perf_counter()-t4)*1000:.1f}ms)")

        # ── Validación SAT/CDCL ───────────────────────────────────────────────
        t5 = time.perf_counter()
        validation = self.validator.validate(r4.graph)
        if self.config.verbose:
            print(f"  [SAT] {'OK SATISFIABLE' if validation.is_satisfiable else 'FAIL UNSAT'}, {validation.cnf_clauses} clausulas CNF ({(time.perf_counter()-t5)*1000:.1f}ms)")

        # ── Exportación JSON-LD ───────────────────────────────────────────────
        jsonld = self.exporter.to_jsonld(r4.graph)

        # ── Renderizado árbol ASCII ───────────────────────────────────────────
        tree_render = self.phase4.render_tree(r4.graph, use_imperative=True)

        total_ms = (time.perf_counter() - t0) * 1000

        result = OntologyResult(
            corpus_input=corpus,
            phase1=r1,
            phase2=r2,
            phase3=r3,
            phase4=r4,
            validation=validation,
            jsonld_export=jsonld,
            tree_render=tree_render,
            processing_time_ms=total_ms,
        )

        if self.config.verbose:
            print(f"\n[RESULT] {result.summary()}")
            print(f"[TIME]   {total_ms:.1f}ms total\n")

        return result

    # ── Utilidades ────────────────────────────────────────────────────────────

    def get_spec_graph(self) -> OntologyResult:
        """
        Retorna el grafo del spec sin procesar corpus adicional.
        Útil para exportar el árbol canónico del spec.
        """
        r4 = self.phase4.build_graph([])
        validation = self.validator.validate(r4.graph)
        jsonld = self.exporter.to_jsonld(r4.graph)
        tree_render = self.phase4.render_tree(r4.graph)

        from .models import Phase1Result, Phase2Result, Phase3Result
        return OntologyResult(
            corpus_input="[SPEC TREE]",
            phase1=Phase1Result(lexical_units=[]),
            phase2=Phase2Result(clusters=[]),
            phase3=Phase3Result(canonical_forms=[]),
            phase4=r4,
            validation=validation,
            jsonld_export=jsonld,
            tree_render=tree_render,
        )

    def validate_only(self, json_data: dict) -> dict[str, Any]:
        """Valida un JSON-LD existente sin reprocessar corpus."""
        graph = self.exporter.from_jsonld(json_data)
        validation = self.validator.validate(graph)
        return {
            "is_satisfiable": validation.is_satisfiable,
            "kb_consistent": validation.kb_consistent,
            "orphans_purged": validation.orphans_purged,
            "cnf_clauses": validation.cnf_clauses,
            "violations": validation.violations,
            "belief_retractions": validation.belief_retractions,
        }

    def export_format(self, result: OntologyResult, fmt: str = "jsonld") -> str:
        """
        Exporta el resultado en el formato solicitado.

        Args:
            fmt: "jsonld" | "turtle" | "tree" | "flat"
        """
        import json
        if fmt == "jsonld":
            return self.exporter.to_json_string(result.phase4.graph)
        elif fmt == "turtle":
            return self.exporter.to_turtle(result.phase4.graph)
        elif fmt == "tree":
            return result.tree_render
        elif fmt == "flat":
            return json.dumps(
                self.exporter.to_flat_list(result.phase4.graph),
                ensure_ascii=False,
                indent=2,
            )
        else:
            raise ValueError(f"Formato desconocido: {fmt}. Use jsonld|turtle|tree|flat")
