"""
MAS-8ENGINE │ agents/memory_agent.py
Agent 2: Adaptive Memory Agent — Default Logic, CBR, Abductive Diagnosis.

Wraps AdaptiveMemoryEngine and CausalAbductionEngine (abduction path)
into an async-capable agent interface.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional, Set

from core.schemas import (
    AgentResponse,
    AgentRole,
    CBRCase,
    DefaultRule,
    NodeScore,
    ThoughtNode,
)
from engines.cbr_default import AdaptiveMemoryEngine
from engines.causal_abduction import CausalAbductionEngine

logger = logging.getLogger(__name__)


class MemoryAgent:
    """Agent 2 — Historical adaptation and non-monotonic reasoning.

    Encapsulates:
      - Case-Based Reasoning (4R cycle: Retrieve, Reuse, Revise, Retain)
      - Default Logic with AGM belief retraction
      - Abductive Diagnosis (Occam's Razor minimal cover)
    """

    def __init__(self) -> None:
        self.role = AgentRole.MEMORY
        self.memory_engine = AdaptiveMemoryEngine()
        self.causal_engine = CausalAbductionEngine()

    async def evaluate(self, node: ThoughtNode) -> AgentResponse:
        """Asynchronously evaluate a ThoughtNode through memory-based engines.

        The evaluation pipeline:
          1. CBR Retrieve — find similar historical cases.
          2. Default Logic — apply default rules and check for retractions.
          3. Abductive Diagnosis — find minimal explanations for anomalies.
          4. CBR Retain — store the new case for future retrieval.
        """
        results: Dict[str, Any] = {}
        score = NodeScore.MAYBE

        try:
            # ── 1. CBR Retrieve ─────────────────────────────────────
            query_features = node.payload.get("problem_features", {})
            case_base_raw = node.payload.get("case_base", [])

            if query_features:
                case_base = [
                    CBRCase(**c) if isinstance(c, dict) else c
                    for c in case_base_raw
                ] if case_base_raw else None

                weights = node.payload.get("feature_weights", None)

                retrieved = await asyncio.to_thread(
                    self.memory_engine.cbr_retrieve,
                    query_features,
                    case_base,
                    3,
                    weights,
                )
                results["cbr_retrieved"] = [
                    {"case": case.model_dump(), "similarity": sim}
                    for case, sim in retrieved
                ]

                # If a similar case exists, increase confidence
                if retrieved and retrieved[0][1] >= 0.5:
                    score = NodeScore.SURE

            # ── 2. Default Logic ────────────────────────────────────
            default_rules_raw = node.payload.get("default_rules", [])
            fact_base_raw = node.payload.get("fact_base", set())
            invalidators = node.payload.get("invalidators", [])

            if default_rules_raw:
                rules = [
                    DefaultRule(**r) if isinstance(r, dict) else r
                    for r in default_rules_raw
                ]
                fact_base: Set[str] = set(fact_base_raw)

                # Apply each default rule
                for rule in rules:
                    fact_base = await asyncio.to_thread(
                        self.memory_engine.apply_default_rule, fact_base, rule
                    )

                # Process invalidators (AGM retraction)
                for inv in invalidators:
                    fact_base = await asyncio.to_thread(
                        self.memory_engine.retract_belief,
                        fact_base,
                        inv,
                        rules,
                    )

                results["fact_base_after"] = sorted(fact_base)
                results["rules_applied"] = len(rules)
                results["retractions"] = len(invalidators)

            # ── 3. Abductive Diagnosis ──────────────────────────────
            observations = node.payload.get("observations", [])
            causal_map = node.payload.get("causal_map", {})

            if observations and causal_map:
                diagnosis = await asyncio.to_thread(
                    self.causal_engine.abductive_diagnosis,
                    observations,
                    causal_map,
                )
                results["abductive_diagnosis"] = diagnosis.model_dump()

                # If the minimal hypothesis set is very small, higher confidence
                if diagnosis.cardinality <= 1:
                    score = NodeScore.SURE

            # ── 4. CBR Retain (store new case) ──────────────────────
            new_solution = node.payload.get("proposed_solution", None)
            if query_features and new_solution:
                new_case = CBRCase(
                    problem_features=query_features,
                    solution=new_solution
                    if isinstance(new_solution, dict)
                    else {"value": new_solution},
                )
                await asyncio.to_thread(
                    self.memory_engine.cbr_retain, new_case
                )
                results["case_retained"] = new_case.model_dump()

            status = "success"

        except Exception as exc:
            logger.error("MemoryAgent evaluation failed: %s", exc)
            results["error"] = str(exc)
            status = "error"

        return AgentResponse(
            agent_id=self.role.value,
            status=status,
            data=results,
            score=score,
        )
