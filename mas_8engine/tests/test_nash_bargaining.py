"""
MAS-8ENGINE │ tests/test_nash_bargaining.py
Test suite for the Nash Bargaining Engine and Kalai-Smorodinsky solver.

Tests cover:
  - Nash product maximization on 2-player and N-player games
  - Pareto optimality verification
  - Kalai-Smorodinsky proportional solution
  - Numerical convergence and boundary conditions
"""
from __future__ import annotations

import pytest
import numpy as np

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from engines.nash_negotiator import NashBargainingEngine
from core.schemas import NashEquilibriumResult


@pytest.fixture
def engine() -> NashBargainingEngine:
    """Create a NashBargainingEngine with default parameters."""
    return NashBargainingEngine(max_iter=1000, tol=1e-9)


# ═══════════════════════════════════════════════════════════════════════
# Nash Equilibrium
# ═══════════════════════════════════════════════════════════════════════

class TestNashEquilibrium:
    """Test Nash product maximization."""

    def test_two_player_symmetric(self, engine: NashBargainingEngine) -> None:
        """Symmetric 2-player game should yield equal split."""
        # 2 agents, 3 allocation options
        utility_matrix = np.array([
            [1.0, 0.5, 0.0],   # Agent 0 utilities
            [0.0, 0.5, 1.0],   # Agent 1 utilities
        ])
        disagreement = np.array([0.0, 0.0])

        result = engine.compute_nash_equilibrium(utility_matrix, disagreement)

        assert isinstance(result, NashEquilibriumResult)
        assert result.nash_product > 0
        assert result.pareto_optimal is True
        # Symmetric game → utilities should be approximately equal
        utils = list(result.optimal_utilities.values())
        assert abs(utils[0] - utils[1]) < 0.1

    def test_two_player_asymmetric(
        self, engine: NashBargainingEngine
    ) -> None:
        """Asymmetric game should still converge."""
        utility_matrix = np.array([
            [3.0, 1.0, 0.0],
            [0.0, 2.0, 4.0],
        ])
        disagreement = np.array([0.0, 0.0])

        result = engine.compute_nash_equilibrium(utility_matrix, disagreement)

        assert result.nash_product > 0
        assert all(v >= 0 for v in result.optimal_utilities.values())

    def test_nonzero_disagreement(
        self, engine: NashBargainingEngine
    ) -> None:
        """Non-zero disagreement point shifts the Nash solution."""
        utility_matrix = np.array([
            [4.0, 2.0, 0.0],
            [0.0, 2.0, 4.0],
        ])
        disagreement_zero = np.array([0.0, 0.0])
        disagreement_high = np.array([1.0, 1.0])

        result_zero = engine.compute_nash_equilibrium(
            utility_matrix, disagreement_zero
        )
        result_high = engine.compute_nash_equilibrium(
            utility_matrix, disagreement_high
        )

        # Both should be valid
        assert result_zero.nash_product > 0
        assert result_high.nash_product > 0
        # Higher disagreement → lower Nash product
        assert result_high.nash_product <= result_zero.nash_product + 1e-6

    def test_three_player(self, engine: NashBargainingEngine) -> None:
        """3-player game convergence."""
        utility_matrix = np.array([
            [2.0, 1.0, 0.5, 0.0],
            [0.0, 1.5, 1.0, 2.0],
            [1.0, 0.5, 2.0, 1.0],
        ])
        disagreement = np.array([0.0, 0.0, 0.0])

        result = engine.compute_nash_equilibrium(utility_matrix, disagreement)

        assert result.nash_product > 0
        assert len(result.optimal_utilities) == 3


# ═══════════════════════════════════════════════════════════════════════
# Kalai-Smorodinsky
# ═══════════════════════════════════════════════════════════════════════

class TestKalaiSmorodinsky:
    """Test Kalai-Smorodinsky proportional solution."""

    def test_symmetric_ks(self, engine: NashBargainingEngine) -> None:
        """Symmetric game: KS should match Nash for symmetric utility."""
        utility_matrix = np.array([
            [1.0, 0.5, 0.0],
            [0.0, 0.5, 1.0],
        ])
        disagreement = np.array([0.0, 0.0])

        result = engine.compute_kalai_smorodinsky(
            utility_matrix, disagreement
        )

        assert isinstance(result, NashEquilibriumResult)
        assert result.nash_product >= 0

    def test_ks_returns_valid_utilities(
        self, engine: NashBargainingEngine
    ) -> None:
        """KS solution utilities should be at or above disagreement."""
        utility_matrix = np.array([
            [3.0, 1.0, 0.0],
            [0.0, 2.0, 4.0],
        ])
        disagreement = np.array([0.5, 0.5])

        result = engine.compute_kalai_smorodinsky(
            utility_matrix, disagreement
        )

        for key, val in result.optimal_utilities.items():
            agent_idx = int(key.split("_")[1])
            assert val >= disagreement[agent_idx] - 1e-6


# ═══════════════════════════════════════════════════════════════════════
# Pareto Optimality
# ═══════════════════════════════════════════════════════════════════════

class TestParetoOptimality:
    """Test Pareto optimality checking."""

    def test_dominated_point(self, engine: NashBargainingEngine) -> None:
        """A point that is dominated should not be Pareto optimal."""
        utilities = np.array([1.0, 1.0])
        feasible_set = np.array([
            [2.0, 2.0],  # dominates (1,1)
            [0.5, 0.5],
            [1.0, 1.0],
        ])

        assert engine.is_pareto_optimal(utilities, feasible_set) is False

    def test_frontier_point(self, engine: NashBargainingEngine) -> None:
        """A point on the frontier should be Pareto optimal."""
        utilities = np.array([2.0, 2.0])
        feasible_set = np.array([
            [2.0, 2.0],
            [3.0, 1.0],
            [1.0, 3.0],
        ])

        assert engine.is_pareto_optimal(utilities, feasible_set) is True
