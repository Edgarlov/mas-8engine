"""
MAS-8ENGINE │ agents/perceptron_agent.py
Agent 1: Perceptive Agent — Bayesian Inference, Fuzzy Logic, Do-Calculus.

Wraps UncertaintyEngine and CausalAbductionEngine into an async-capable
agent interface that processes ThoughtNodes and returns AgentResponses.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

from core.schemas import (
    AgentResponse,
    AgentRole,
    BayesianPrior,
    BayesianResult,
    FuzzySet,
    NodeScore,
    ThoughtNode,
)
from engines.bayes_fuzzy import UncertaintyEngine
from engines.causal_abduction import CausalAbductionEngine

import networkx as nx

logger = logging.getLogger(__name__)


class PerceptronAgent:
    """Agent 1 — Uncertainty quantification and causal intervention.

    Encapsulates:
      - Bayesian posterior updates
      - Fuzzy membership evaluation & Mamdani defuzzification
      - Pearl's Do-Calculus for causal intervention analysis
    """

    def __init__(self) -> None:
        self.role = AgentRole.PERCEPTRON
        self.uncertainty_engine = UncertaintyEngine()
        self.causal_engine = CausalAbductionEngine()

    async def evaluate(self, node: ThoughtNode) -> AgentResponse:
        """Asynchronously evaluate a ThoughtNode through all perceptive engines.

        The evaluation pipeline:
          1. Extract Bayesian priors from node payload (if present).
          2. Evaluate fuzzy memberships (if present).
          3. Perform causal analysis (if a causal graph is provided).
          4. Synthesize results into an AgentResponse with a NodeScore.
        """
        results: Dict[str, Any] = {}
        score = NodeScore.MAYBE

        try:
            # ── 1. Bayesian Update ──────────────────────────────────
            bayesian_data = node.payload.get("bayesian_priors", [])
            if bayesian_data:
                priors = [
                    BayesianPrior(**p) if isinstance(p, dict) else p
                    for p in bayesian_data
                ]
                bayesian_results = await asyncio.to_thread(
                    self.uncertainty_engine.batch_update_bayes, priors
                )
                results["bayesian_posteriors"] = [
                    r.model_dump() for r in bayesian_results
                ]
                # High-confidence assessment
                max_posterior = max(r.posterior for r in bayesian_results)
                if max_posterior >= 0.60:
                    score = NodeScore.SURE
                elif max_posterior < 0.15:
                    score = NodeScore.IMPOSSIBLE

            # ── 2. Fuzzy Evaluation ─────────────────────────────────
            fuzzy_data = node.payload.get("fuzzy_inputs", [])
            if fuzzy_data:
                memberships = [
                    (item["membership_degree"], item["crisp_value"])
                    for item in fuzzy_data
                ]
                crisp_output = await asyncio.to_thread(
                    self.uncertainty_engine.defuzzify_centroid, memberships
                )
                results["fuzzy_crisp_output"] = crisp_output
                if crisp_output >= 50.0 and score != NodeScore.IMPOSSIBLE:
                    score = NodeScore.SURE

            # ── 3. Causal Do-Calculus ───────────────────────────────
            causal_data = node.payload.get("causal_graph", None)
            intervention_var = node.payload.get("intervention_var", None)
            if causal_data and intervention_var:
                graph = nx.DiGraph()
                for src, targets in causal_data.items():
                    for tgt in targets:
                        graph.add_edge(src, tgt)

                intervention_result = await asyncio.to_thread(
                    self.causal_engine.apply_do_operator, graph, intervention_var
                )
                results["causal_intervention"] = intervention_result.model_dump()

            # ── 4. Abductive Diagnosis (if observations present) ────
            observations = node.payload.get("observations", [])
            causal_map = node.payload.get("causal_map", {})
            if observations and causal_map:
                diagnosis = await asyncio.to_thread(
                    self.causal_engine.abductive_diagnosis,
                    observations,
                    causal_map,
                )
                results["abductive_diagnosis"] = diagnosis.model_dump()

            status = "success"

        except Exception as exc:
            logger.error("PerceptronAgent evaluation failed: %s", exc)
            results["error"] = str(exc)
            status = "error"

        return AgentResponse(
            agent_id=self.role.value,
            status=status,
            data=results,
            score=score,
        )
