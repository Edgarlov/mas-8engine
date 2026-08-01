"""
__init__.py — Ontology Engine v2.0

Motor de Ingeniería Ontológica y Minería Léxica de Resolución Atómica.

Basado en: ESPECIFICACION_INGENIERIA_ONTOLOGICA.md
Versión: 2.0
"""

from .models import (
    CanonicalForm,
    Cluster,
    LexicalUnit,
    NodeRole,
    OntologyGraph,
    OntologyNode,
    OntologyResult,
    Phase1Result,
    Phase2Result,
    Phase3Result,
    Phase4Result,
    RelationType,
    SyntacticPattern,
    ValidationResult,
)
from .pipeline import OntologyEnginePipeline, PipelineConfig

__all__ = [
    "OntologyEnginePipeline",
    "PipelineConfig",
    "OntologyGraph",
    "OntologyNode",
    "OntologyResult",
    "CanonicalForm",
    "LexicalUnit",
    "Cluster",
    "ValidationResult",
    "NodeRole",
    "RelationType",
    "SyntacticPattern",
    "Phase1Result",
    "Phase2Result",
    "Phase3Result",
    "Phase4Result",
]

__version__ = "2.0.0"
__spec__ = "ESPECIFICACION_INGENIERIA_ONTOLOGICA.md v2.0"
