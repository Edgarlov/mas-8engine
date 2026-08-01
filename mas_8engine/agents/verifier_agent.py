"""
MAS-8ENGINE │ agents/verifier_agent.py
Agent 3: Tautological Verifier & Axiomatic Negotiator.

Wraps Z3SATVerifier, NashBargainingEngine, and ISO704Normalizer
into an async-capable agent interface. Returns IMPOSSIBLE on UNSAT
to trigger immediate pruning in the Master Orchestrator.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

import numpy as np

from core.schemas import (
    AgentResponse,
    AgentRole,
    CNFClause,
    NodeScore,
    ThoughtNode,
)
from engines.sat_verifier import Z3SATVerifier
from engines.nash_negotiator import NashBargainingEngine
from pipeline.iso_704_normalizer import ISO704Normalizer

logger = logging.getLogger(__name__)


class VerifierAgent:
    """Agent 3 — Formal verification, negotiation, and ontological normalization.

    Encapsulates:
      - Z3 SAT/CDCL satisfiability checking (returns IMPOSSIBLE on UNSAT)
      - Nash Bargaining for inter-agent resource allocation
      - ISO 704 normalization producing RDF/OWL triples
    """

    def __init__(self, z3_timeout_ms: int = 30000) -> None:
        self.role = AgentRole.VERIFIER
        self.sat_verifier = Z3SATVerifier(timeout_ms=z3_timeout_ms)
        self.nash_engine = NashBargainingEngine()
        self.normalizer = ISO704Normalizer()

    async def evaluate(self, node: ThoughtNode) -> AgentResponse:
        """Asynchronously evaluate a ThoughtNode through verification engines.

        The evaluation pipeline:
          1. SAT Verification — check logical consistency of propositions.
          2. Nash Bargaining — optimize inter-agent utility allocation.
          3. ISO 704 Normalization — produce ontological triples.
        """
        results: Dict[str, Any] = {}
        score = NodeScore.MAYBE
        cnf_proof: Optional[List[str]] = None

        try:
            # ── 1. SAT / CDCL Verification ─────────────────────────
            cnf_data = node.payload.get("cnf_clauses", [])
            propositions = node.payload.get("propositions", {})

            if cnf_data:
                clauses = [
                    CNFClause(**c) if isinstance(c, dict) else c
                    for c in cnf_data
                ]
                sat_result = await asyncio.to_thread(
                    self.sat_verifier.verify_cnf, clauses
                )
                results["sat_result"] = sat_result.model_dump()

                if sat_result.satisfiable:
                    score = NodeScore.SURE
                    cnf_proof = [
                        f"{var}={val}"
                        for var, val in (sat_result.model or {}).items()
                    ]
                else:
                    # UNSAT → IMPOSSIBLE → triggers pruning in Master
                    score = NodeScore.IMPOSSIBLE
                    cnf_proof = sat_result.conflict_clause or []
                    results["conflict_reason"] = (
                        "CNF formula is UNSATISFIABLE. "
                        "Conflict clause learned for backtracking."
                    )

            elif propositions:
                sat_result = await asyncio.to_thread(
                    self.sat_verifier.verify_propositions, propositions
                )
                results["sat_result"] = sat_result.model_dump()

                if sat_result.satisfiable:
                    score = NodeScore.SURE
                else:
                    score = NodeScore.IMPOSSIBLE

            # ── 2. Nash Bargaining ──────────────────────────────────
            utility_data = node.payload.get("utility_matrix", None)
            disagreement = node.payload.get("disagreement_point", None)

            if utility_data is not None and disagreement is not None:
                utility_matrix = np.array(utility_data, dtype=np.float64)
                disagreement_point = np.array(disagreement, dtype=np.float64)

                nash_result = await asyncio.to_thread(
                    self.nash_engine.compute_nash_equilibrium,
                    utility_matrix,
                    disagreement_point,
                )
                results["nash_equilibrium"] = nash_result.model_dump()

            # ── 3. ISO 704 Normalization ────────────────────────────
            text_to_normalize = node.payload.get("normalize_text", None)
            if text_to_normalize is None:
                # Normalize the thought itself as fallback
                text_to_normalize = node.thought

            norm_result = await asyncio.to_thread(
                self.normalizer.normalize_text, text_to_normalize
            )
            results["normalization"] = norm_result.model_dump()

            if score != NodeScore.IMPOSSIBLE:
                score = NodeScore.SURE

            status = "success" if score != NodeScore.IMPOSSIBLE else "pruned"

        except Exception as exc:
            logger.error("VerifierAgent evaluation failed: %s", exc)
            results["error"] = str(exc)
            status = "error"

        return AgentResponse(
            agent_id=self.role.value,
            status=status,
            data=results,
            cnf_proof=cnf_proof,
            score=score,
        )
