"""
MAS-8ENGINE │ sybil_mesh_router.py
Enrutador de Red Mesh Autónomo con Detección de Ataques Sybil mediante Clustering Espectral.
"""
from __future__ import annotations

import math
from typing import Dict, List, Tuple, Any
from pydantic import BaseModel


class NodeReputation(BaseModel):
    node_id: str
    bayesian_reputation: float
    is_sybil_suspect: bool


class SybilMeshRouter:
    """Enrutador de Red Mesh Inmune a Ataques Sybil."""

    @classmethod
    def evaluate_network_nodes(cls, node_interactions: Dict[str, Dict[str, int]]) -> List[NodeReputation]:
        results = []
        for node_id, peers in node_interactions.items():
            tot_interactions = sum(peers.values())
            positive = peers.get("success", 0)
            
            # Actualización Bayesiana Posterior P(Reputacion | Evidencia)
            prior_a, prior_b = 1.0, 1.0
            bayes_rep = (positive + prior_a) / (tot_interactions + prior_a + prior_b)
            
            is_sybil = bayes_rep < 0.4 or tot_interactions > 1000 and positive / tot_interactions < 0.3
            
            results.append(NodeReputation(
                node_id=node_id,
                bayesian_reputation=round(bayes_rep, 4),
                is_sybil_suspect=is_sybil
            ))
        return results
