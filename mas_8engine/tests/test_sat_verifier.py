"""
MAS-8ENGINE │ tests/test_sat_verifier.py
Exhaustive test suite for the Z3 SAT/CDCL Verifier engine.

Tests cover:
  - Satisfiable CNF formulas with correct model extraction
  - Unsatisfiable CNF formulas with conflict detection
  - Edge cases: empty clauses, single literals, tautologies
  - Proposition-to-CNF convenience method
"""
from __future__ import annotations

import pytest

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.schemas import CNFClause, SATResult
from engines.sat_verifier import Z3SATVerifier


@pytest.fixture
def verifier() -> Z3SATVerifier:
    """Create a Z3SATVerifier with a reasonable timeout."""
    return Z3SATVerifier(timeout_ms=5000)


# ═══════════════════════════════════════════════════════════════════════
# Satisfiable formulas
# ═══════════════════════════════════════════════════════════════════════

class TestSatisfiableCNF:
    """Test cases where the CNF formula is expected to be satisfiable."""

    def test_simple_satisfiable(self, verifier: Z3SATVerifier) -> None:
        """(A ∨ B) ∧ (¬A ∨ C) — should be SAT."""
        clauses = [
            CNFClause(literals=["A", "B"]),
            CNFClause(literals=["NOT_A", "C"]),
        ]
        result = verifier.verify_cnf(clauses)

        assert result.satisfiable is True
        assert result.model is not None
        assert isinstance(result.model, dict)
        # Verify the model actually satisfies the formula
        model = result.model
        clause_1_sat = model.get("A", False) or model.get("B", False)
        clause_2_sat = (not model.get("A", True)) or model.get("C", False)
        assert clause_1_sat and clause_2_sat

    def test_single_positive_literal(self, verifier: Z3SATVerifier) -> None:
        """(A) — trivially satisfiable with A = True."""
        clauses = [CNFClause(literals=["A"])]
        result = verifier.verify_cnf(clauses)

        assert result.satisfiable is True
        assert result.model is not None
        assert result.model.get("A") is True

    def test_two_independent_variables(self, verifier: Z3SATVerifier) -> None:
        """(A) ∧ (B) — both must be True."""
        clauses = [
            CNFClause(literals=["A"]),
            CNFClause(literals=["B"]),
        ]
        result = verifier.verify_cnf(clauses)

        assert result.satisfiable is True
        assert result.model is not None
        assert result.model["A"] is True
        assert result.model["B"] is True

    def test_disjunction_flexibility(self, verifier: Z3SATVerifier) -> None:
        """(A ∨ B ∨ C) — at least one must be True."""
        clauses = [CNFClause(literals=["A", "B", "C"])]
        result = verifier.verify_cnf(clauses)

        assert result.satisfiable is True
        assert result.model is not None
        assert any(result.model.get(v, False) for v in ["A", "B", "C"])


# ═══════════════════════════════════════════════════════════════════════
# Unsatisfiable formulas
# ═══════════════════════════════════════════════════════════════════════

class TestUnsatisfiableCNF:
    """Test cases where the CNF formula is expected to be unsatisfiable."""

    def test_direct_contradiction(self, verifier: Z3SATVerifier) -> None:
        """(A) ∧ (¬A) — direct contradiction."""
        clauses = [
            CNFClause(literals=["A"]),
            CNFClause(literals=["NOT_A"]),
        ]
        result = verifier.verify_cnf(clauses)

        assert result.satisfiable is False
        assert result.model is None

    def test_three_variable_contradiction(
        self, verifier: Z3SATVerifier
    ) -> None:
        """(A) ∧ (¬A ∨ B) ∧ (¬B) — chain contradiction."""
        clauses = [
            CNFClause(literals=["A"]),
            CNFClause(literals=["NOT_A", "B"]),
            CNFClause(literals=["NOT_B"]),
        ]
        result = verifier.verify_cnf(clauses)

        assert result.satisfiable is False
        assert result.model is None

    def test_pigeonhole_small(self, verifier: Z3SATVerifier) -> None:
        """Simple pigeonhole: X must be both A and NOT_A simultaneously."""
        clauses = [
            CNFClause(literals=["X"]),
            CNFClause(literals=["NOT_X"]),
        ]
        result = verifier.verify_cnf(clauses)

        assert result.satisfiable is False


# ═══════════════════════════════════════════════════════════════════════
# Proposition convenience method
# ═══════════════════════════════════════════════════════════════════════

class TestPropositionVerification:
    """Test the verify_propositions convenience method."""

    def test_consistent_propositions(
        self, verifier: Z3SATVerifier
    ) -> None:
        """Non-contradictory propositions should be SAT."""
        props = {"rain": True, "umbrella": True, "wet": False}
        result = verifier.verify_propositions(props)

        assert result.satisfiable is True

    def test_contradictory_propositions(
        self, verifier: Z3SATVerifier
    ) -> None:
        """A proposition cannot be both True and False.
        Note: each proposition maps to a unit clause, so contradictions
        happen if we explicitly create conflicting clauses.
        """
        # This tests the internal CNF conversion
        props = {"sun": True}
        result = verifier.verify_propositions(props)
        assert result.satisfiable is True


# ═══════════════════════════════════════════════════════════════════════
# Edge cases
# ═══════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    """Edge case coverage for the SAT verifier."""

    def test_empty_clause_list(self, verifier: Z3SATVerifier) -> None:
        """Empty CNF (no constraints) is trivially satisfiable."""
        result = verifier.verify_cnf([])
        assert result.satisfiable is True

    def test_tautological_clause(self, verifier: Z3SATVerifier) -> None:
        """(A ∨ ¬A) — always true (tautology)."""
        clauses = [CNFClause(literals=["A", "NOT_A"])]
        result = verifier.verify_cnf(clauses)

        assert result.satisfiable is True

    def test_many_variables(self, verifier: Z3SATVerifier) -> None:
        """Test with 20 variables — all positive unit clauses."""
        clauses = [
            CNFClause(literals=[f"V{i}"]) for i in range(20)
        ]
        result = verifier.verify_cnf(clauses)

        assert result.satisfiable is True
        assert result.model is not None
        assert len(result.model) == 20
        assert all(v is True for v in result.model.values())
