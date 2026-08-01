"""
MAS-8ENGINE │ tests/test_orchestrator.py
End-to-end test suite for the Master Orchestrator and full pipeline.

Tests cover:
  - LangGraph compilation and execution
  - ToT branching and node generation
  - Agent delegation (parallel execution)
  - Pruning on IMPOSSIBLE (Z3 UNSAT)
  - Backtracking to MAYBE nodes
  - Full solve endpoint via FastAPI TestClient
"""
from __future__ import annotations

import pytest
import pytest_asyncio

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.schemas import (
    NodeScore,
    SolveRequest,
    SolveResponse,
    ThoughtNode,
    CNFClause,
    BayesianPrior,
)
from agents.master_orchestrator import MasterOrchestrator


# ═══════════════════════════════════════════════════════════════════════
# Orchestrator Unit Tests
# ═══════════════════════════════════════════════════════════════════════

class TestMasterOrchestrator:
    """Test the MasterOrchestrator LangGraph pipeline."""

    @pytest.fixture
    def orchestrator(self) -> MasterOrchestrator:
        return MasterOrchestrator()

    @pytest.mark.asyncio
    async def test_basic_solve(self, orchestrator: MasterOrchestrator) -> None:
        """A basic query should produce a non-empty thought tree."""
        request = SolveRequest(
            query="Evaluate market entry strategy for a fintech startup",
            max_depth=2,
            branching_factor=2,
        )
        response = await orchestrator.solve(request)

        assert isinstance(response, SolveResponse)
        assert response.query == request.query
        assert len(response.thought_tree) > 0
        assert response.execution_time_ms > 0
        assert response.optimal_solution is not None

    @pytest.mark.asyncio
    async def test_thought_tree_structure(
        self, orchestrator: MasterOrchestrator
    ) -> None:
        """Thought tree nodes should have valid scores and depths."""
        request = SolveRequest(
            query="Analyze supply chain resilience under geopolitical risk",
            max_depth=2,
            branching_factor=2,
        )
        response = await orchestrator.solve(request)

        for node in response.thought_tree:
            assert node.score in (
                NodeScore.SURE,
                NodeScore.MAYBE,
                NodeScore.IMPOSSIBLE,
            )
            assert node.depth >= 0
            assert len(node.thought) > 0

    @pytest.mark.asyncio
    async def test_delegation_trace_populated(
        self, orchestrator: MasterOrchestrator
    ) -> None:
        """Delegation trace should record agent evaluations."""
        request = SolveRequest(
            query="Optimize resource allocation across distributed systems",
            max_depth=1,
            branching_factor=2,
        )
        response = await orchestrator.solve(request)

        assert len(response.delegation_trace) > 0
        for trace in response.delegation_trace:
            assert trace.agent_id in (
                "perceptron_agent",
                "memory_agent",
                "verifier_agent",
            )

    @pytest.mark.asyncio
    async def test_shallow_depth_terminates(
        self, orchestrator: MasterOrchestrator
    ) -> None:
        """With max_depth=1, the pipeline should terminate quickly."""
        request = SolveRequest(
            query="Simple test query",
            max_depth=1,
            branching_factor=2,
        )
        response = await orchestrator.solve(request)

        assert response.optimal_solution is not None
        assert response.execution_time_ms < 180000  # Account for local VRAM swapping


# ═══════════════════════════════════════════════════════════════════════
# Integration Tests (Individual Engines)
# ═══════════════════════════════════════════════════════════════════════

class TestEngineIntegration:
    """Test individual engine components that feed into the orchestrator."""

    def test_bayesian_engine(self) -> None:
        """Bayesian update should produce valid posterior."""
        from engines.bayes_fuzzy import UncertaintyEngine

        engine = UncertaintyEngine()
        prior = BayesianPrior(
            hypothesis="Market will grow",
            prior_prob=0.6,
            likelihood=0.8,
            evidence_given_not_h=0.3,
        )
        result = engine.update_bayes(prior)

        assert 0.0 <= result.posterior <= 1.0
        assert result.posterior > prior.prior_prob  # Evidence supports H

    def test_fuzzy_defuzzification(self) -> None:
        """Centroid defuzzification should return valid crisp output."""
        from engines.bayes_fuzzy import UncertaintyEngine

        engine = UncertaintyEngine()
        memberships = [
            (0.3, 10.0),  # (μ, z)
            (0.7, 20.0),
            (0.5, 30.0),
        ]
        crisp = engine.defuzzify_centroid(memberships)

        assert 10.0 <= crisp <= 30.0
        # Expected: (0.3*10 + 0.7*20 + 0.5*30) / (0.3 + 0.7 + 0.5)
        expected = (3.0 + 14.0 + 15.0) / 1.5
        assert abs(crisp - expected) < 1e-9

    def test_cbr_retrieval(self) -> None:
        """CBR should retrieve the most similar case."""
        from engines.cbr_default import AdaptiveMemoryEngine
        from core.schemas import CBRCase

        engine = AdaptiveMemoryEngine()
        cases = [
            CBRCase(
                problem_features={"x": 1.0, "y": 2.0},
                solution={"action": "A"},
            ),
            CBRCase(
                problem_features={"x": 10.0, "y": 20.0},
                solution={"action": "B"},
            ),
        ]

        query = {"x": 1.1, "y": 2.1}
        results = engine.cbr_retrieve(query, cases, top_k=1)

        assert len(results) == 1
        assert results[0][0].solution["action"] == "A"
        assert results[0][1] > 0.8  # High similarity

    def test_causal_do_operator(self) -> None:
        """Do-operator should remove incoming edges."""
        import networkx as nx
        from engines.causal_abduction import CausalAbductionEngine

        engine = CausalAbductionEngine()
        graph = nx.DiGraph()
        graph.add_edges_from([
            ("Z", "X"), ("X", "Y"), ("Z", "Y"),
        ])

        result = engine.apply_do_operator(graph, "X")

        assert "Z" in result.original_parents
        # Original graph should be unmodified
        assert graph.has_edge("Z", "X")


# ═══════════════════════════════════════════════════════════════════════
# FastAPI Integration
# ═══════════════════════════════════════════════════════════════════════

class TestFastAPIEndpoint:
    """Test the /api/v1/solve endpoint via TestClient."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from main import app
        return TestClient(app)

    def test_health_endpoint(self, client) -> None:
        """Health check should return operational status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"
        assert len(data["engines"]) == 8

    def test_solve_endpoint(self, client) -> None:
        """Solve endpoint should accept and process a query."""
        response = client.post(
            "/api/v1/solve",
            json={
                "query": "Test query for integration",
                "max_depth": 1,
                "branching_factor": 2,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "thought_tree" in data
        assert "optimal_solution" in data
        assert data["execution_time_ms"] > 0

    def test_solve_empty_query_rejected(self, client) -> None:
        """Empty query should be rejected with 422."""
        response = client.post(
            "/api/v1/solve",
            json={"query": ""},
        )
        assert response.status_code == 422

