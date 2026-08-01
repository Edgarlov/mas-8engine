from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Set, Tuple

from core.schemas import CBRCase, DefaultRule


class AdaptiveMemoryEngine:
    """Motor de Memoria Adaptativa que integra Razonamiento Basado en Casos y Lógica por Defecto."""

    def __init__(self) -> None:
        self.case_base: List[CBRCase] = []
        self.fact_base: Set[str] = set()

    def cbr_retrieve(
        self, 
        query_features: Dict[str, float], 
        case_base: Optional[List[CBRCase]] = None, 
        top_k: int = 3, 
        weights: Optional[Dict[str, float]] = None
    ) -> List[Tuple[CBRCase, float]]:
        """
        Recupera los top_k casos más similares usando distancia euclidiana ponderada.
        Maneja características faltantes asumiendo 0.0.
        """
        cases = case_base if case_base is not None else self.case_base
        results: List[Tuple[CBRCase, float]] = []
        
        for case in cases:
            distance_sq = 0.0
            all_keys = set(query_features.keys()).union(case.problem_features.keys())
            
            for key in all_keys:
                w = weights.get(key, 1.0) if weights else 1.0
                q_val = query_features.get(key, 0.0)
                c_val = case.problem_features.get(key, 0.0)
                
                distance_sq += w * ((q_val - c_val) ** 2)
                
            d = math.sqrt(distance_sq)
            similarity = 1.0 / (1.0 + d)
            results.append((case, similarity))
            
        # Orden descendente por similitud
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def cbr_retain(self, new_case: CBRCase) -> None:
        """Añade un nuevo caso a la base de casos interna."""
        self.case_base.append(new_case)

    def apply_default_rule(self, fact_base: Set[str], rule: DefaultRule) -> Set[str]:
        """
        Aplica una regla de lógica por defecto:
        Si el prerrequisito está en fact_base y la negación de la justificación NO lo está,
        añade el consecuente a fact_base.
        """
        updated_facts = set(fact_base)
        
        if rule.prerequisite in updated_facts:
            negated_justification = f"NOT_{rule.justification}"
            if negated_justification not in updated_facts:
                updated_facts.add(rule.consequent)
                
        return updated_facts

    def retract_belief(self, fact_base: Set[str], invalidator: str, rules: List[DefaultRule]) -> Set[str]:
        """
        Retracción de creencias (AGM-style).
        Añade el invalidator y elimina consecuentes invalidados y sus dependencias en cascada.
        """
        updated_facts = set(fact_base)
        updated_facts.add(invalidator)
        
        retracted_consequents: Set[str] = set()
        
        # Invalidation directa
        for rule in rules:
            if invalidator == f"NOT_{rule.justification}":
                if rule.consequent in updated_facts:
                    updated_facts.remove(rule.consequent)
                    retracted_consequents.add(rule.consequent)
                    
        # Propagación en cascada de la retracción
        changed = True
        while changed:
            changed = False
            for rule in rules:
                if rule.prerequisite in retracted_consequents and rule.consequent in updated_facts:
                    updated_facts.remove(rule.consequent)
                    retracted_consequents.add(rule.consequent)
                    changed = True
                    
        return updated_facts
