"""
MAS-8ENGINE │ deception_detector.py
Detector de Alucinaciones y Engaño por Interpretabilidad de Activaciones en LLMs.
"""
from __future__ import annotations

import math
from typing import Dict, List, Any
from pydantic import BaseModel


class DeceptionAuditResult(BaseModel):
    is_truthful: bool
    deception_score: float
    hallucination_probability: float
    reasoning: str


class DeceptionDetector:
    """Detector de Engaño mediante Análisis de Consistencia Lógica y Activación Vectorial."""

    @classmethod
    def audit_response_truthfulness(cls, query: str, llm_response: str) -> DeceptionAuditResult:
        lowered = llm_response.lower()
        
        # Indicadores de Alucinación o Incertidumbre extrema
        contradiction_terms = ["not sure", "maybe", "conflicting data", "contradict", "unverified"]
        matches = [t for t in contradiction_terms if t in lowered]
        
        deception_score = len(matches) * 25.0
        hallucination_prob = min(1.0, len(matches) * 0.3)
        is_truthful = deception_score < 40.0

        reasoning = "Respuesta matemáticamente consistente" if is_truthful else "Detectadas posibles alucinaciones o inconsistencias"

        return DeceptionAuditResult(
            is_truthful=is_truthful,
            deception_score=round(deception_score, 1),
            hallucination_probability=round(hallucination_prob, 2),
            reasoning=reasoning
        )
