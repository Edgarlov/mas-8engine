"""
MAS-8ENGINE │ horvitz_thompson_sampler.py
Implementación de Muestreo Adaptativo de Horvitz-Thompson e Invariante UCB1 para MCTS.
Extraído de las taxonomías de exploración de entornos opacos.
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple, Any
from pydantic import BaseModel, Field


class SampleNode(BaseModel):
    node_id: str
    value: float
    inclusion_prob: float = Field(gt=0.0, description="Probabilidad pi_k de inclusión en la muestra")
    visits: int = 0


class HorvitzThompsonResult(BaseModel):
    estimated_total: float
    sample_size: int
    variance_estimate: float
    confidence_interval_95: Tuple[float, float]


class HorvitzThompsonEstimator:
    """Estimador insesgado de Horvitz-Thompson para inspección de grafos opacos."""

    @staticmethod
    def estimate_total(samples: List[SampleNode]) -> HorvitzThompsonResult:
        if not samples:
            return HorvitzThompsonResult(
                estimated_total=0.0,
                sample_size=0,
                variance_estimate=0.0,
                confidence_interval_95=(0.0, 0.0)
            )

        # HT Estimator: Y_hat = sum(y_k / pi_k)
        total_est = sum(s.value / s.inclusion_prob for s in samples)
        n = len(samples)

        # Horvitz-Thompson Variance Approximation (Sen-Yates-Grundy)
        var_accum = 0.0
        for i in range(n):
            for j in range(i + 1, n):
                pi_i = samples[i].inclusion_prob
                pi_j = samples[j].inclusion_prob
                pi_ij = pi_i * pi_j  # Independent sampling assumption
                diff = (samples[i].value / pi_i) - (samples[j].value / pi_j)
                var_accum += ((pi_i * pi_j - pi_ij) / pi_ij) * (diff ** 2)

        var_est = max(0.0, var_accum)
        std_err = math.sqrt(var_est) if var_est > 0 else 0.0
        ci_lower = max(0.0, total_est - 1.96 * std_err)
        ci_upper = total_est + 1.96 * std_err

        return HorvitzThompsonResult(
            estimated_total=round(total_est, 4),
            sample_size=n,
            variance_estimate=round(var_est, 4),
            confidence_interval_95=(round(ci_lower, 4), round(ci_upper, 4))
        )


class UCB1Selector:
    """Selector de Nodos Upper Confidence Bound (UCB1) para Tree of Thoughts / MCTS."""

    @staticmethod
    def calculate_ucb1(
        node_avg_reward: float,
        node_visits: int,
        parent_total_visits: int,
        exploration_constant: float = 1.414
    ) -> float:
        if node_visits == 0:
            return float("inf")
        
        exploitation = node_avg_reward
        exploration = exploration_constant * math.sqrt(math.log(parent_total_visits) / node_visits)
        return exploitation + exploration

    @classmethod
    def select_best_node(
        cls,
        nodes: List[Dict[str, Any]],
        parent_total_visits: int,
        c: float = 1.414
    ) -> Optional[Dict[str, Any]]:
        if not nodes:
            return None

        best_score = -float("inf")
        best_node = None

        for n in nodes:
            score = cls.calculate_ucb1(
                node_avg_reward=n.get("avg_reward", 0.0),
                node_visits=n.get("visits", 0),
                parent_total_visits=parent_total_visits,
                exploration_constant=c
            )
            if score > best_score:
                best_score = score
                best_node = n

        return best_node
