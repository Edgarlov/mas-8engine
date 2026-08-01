"""
MAS-8ENGINE │ epistemic_os.py
Sistema Operativo Epistemológico Autónomo de Extracción Ontológica Universal ISO-704.
"""
from __future__ import annotations

from typing import Dict, List, Any
from pydantic import BaseModel
from pipeline.c_value_extractor import CValueExtractor, ExtractedTerm
from memory.graph_store import KnowledgeGraphEngine, TripleStatement


class EpistemicExtractionResult(BaseModel):
    terms_extracted: List[ExtractedTerm]
    triples_saved: int
    epistemic_status: str


class EpistemicOS:
    """Kernel Epistemológico Universal para Extracción Ontológica ISO-704."""

    @classmethod
    def process_unstructured_corpus(cls, corpus_text: str) -> EpistemicExtractionResult:
        # 1. Extracción de Términos C-Value
        terms = CValueExtractor.compute_c_values(corpus_text, min_freq=1)
        
        # 2. Construcción de Tripletas Ontológicas
        triples = []
        for i in range(min(len(terms), 5)):
            t = terms[i]
            triples.append(TripleStatement(
                subject=t.term,
                predicate="hasCValueScore",
                object_value=str(t.c_value)
            ))

        graph_engine = KnowledgeGraphEngine()
        saved_count = graph_engine.add_triples(triples)

        return EpistemicExtractionResult(
            terms_extracted=terms[:5],
            triples_saved=saved_count,
            epistemic_status="EPISTEMIC_EXTRACTION_SUCCESS"
        )
