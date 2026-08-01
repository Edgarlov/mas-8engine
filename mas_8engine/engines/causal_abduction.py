from __future__ import annotations

import networkx as nx
from typing import Any, Dict, List, Optional, Set

from core.schemas import AbductiveDiagnosis, CausalIntervention


class CausalAbductionEngine:
    """
    Motor de Abducción Causal.
    Proporciona mecanismos para el diagnóstico abductivo y operaciones causales sobre grafos (do-calculus).
    """

    def abductive_diagnosis(
        self, observations: List[str], causal_map: Dict[str, List[str]]
    ) -> AbductiveDiagnosis:
        """
        Calcula el conjunto mínimo de causas que cubren las observaciones dadas utilizando
        una aproximación greedy para el problema de cobertura de conjuntos (set cover).
        """
        uncovered = set(observations)
        selected_causes: List[str] = []
        
        # Mapeo de causas a conjuntos de efectos
        cause_effects = {k: set(v) for k, v in causal_map.items()}

        while uncovered:
            best_cause = None
            best_cover_count = 0
            best_cover_set: Set[str] = set()

            for cause, effects in cause_effects.items():
                if cause in selected_causes:
                    continue
                cover = effects.intersection(uncovered)
                if len(cover) > best_cover_count:
                    best_cover_count = len(cover)
                    best_cause = cause
                    best_cover_set = cover

            if best_cause is None:
                break

            selected_causes.append(best_cause)
            uncovered -= best_cover_set

        return AbductiveDiagnosis(
            observations=observations,
            minimal_hypotheses=selected_causes,
            cardinality=len(selected_causes),
        )

    def apply_do_operator(self, graph: nx.DiGraph, intervention_var: str) -> CausalIntervention:
        """
        Aplica el operador do(X) de Pearl sobre una variable de intervención.
        Elimina todas las aristas entrantes a la variable de intervención.
        """
        mutated_graph = graph.copy()
        original_parents = list(mutated_graph.predecessors(intervention_var))
        
        mutated_graph.remove_edges_from([(parent, intervention_var) for parent in original_parents])
        
        return CausalIntervention(
            intervention_var=intervention_var,
            original_parents=original_parents,
            remaining_edges=mutated_graph.number_of_edges(),
            mutated_graph_nodes=list(mutated_graph.nodes)
        )

    def get_mutated_graph(self, graph: nx.DiGraph, intervention_var: str) -> nx.DiGraph:
        """
        Obtiene el grafo resultante tras aplicar el operador do(X).
        """
        mutated_graph = graph.copy()
        if intervention_var in mutated_graph:
            parents = list(mutated_graph.predecessors(intervention_var))
            mutated_graph.remove_edges_from([(parent, intervention_var) for parent in parents])
        return mutated_graph

    def backdoor_adjustment(self, graph: nx.DiGraph, treatment: str, outcome: str) -> List[Set[str]]:
        """
        Calcula conjuntos válidos de ajuste backdoor para identificar el efecto causal
        del tratamiento sobre el resultado. Retorna los ancestros/padres no descendientes.
        """
        descendants = set(nx.descendants(graph, treatment))
        descendants.add(treatment)
        
        ancestors = set(nx.ancestors(graph, treatment))
        parents = set(graph.predecessors(treatment))
        
        valid_parents = {p for p in parents if p not in descendants}
        
        possible_sets: List[Set[str]] = []
        if valid_parents:
            possible_sets.append(valid_parents)
            
        return possible_sets
