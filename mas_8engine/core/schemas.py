"""
MAS-8ENGINE │ core/schemas.py
Strict Pydantic v2 domain models for the multi-agent reasoning taxonomy.

Every schema is immutable (frozen), fully typed, and serializable to JSON
for inter-agent message passing and FastAPI response rendering.
"""
from __future__ import annotations

import uuid
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field


# ═══════════════════════════════════════════════════════════════════════
# 1. Enumerations
# ═══════════════════════════════════════════════════════════════════════

class NodeScore(str, Enum):
    """Meta-cognitive evaluation score for a Tree-of-Thoughts node.

    SURE       — Logically verified and consistent (SAT).
    MAYBE      — Plausible but unverified; candidate for further exploration.
    IMPOSSIBLE — Contradictory (UNSAT); triggers immediate pruning.
    """
    SURE = "SURE"
    MAYBE = "MAYBE"
    IMPOSSIBLE = "IMPOSSIBLE"


class AgentRole(str, Enum):
    """Canonical identifiers for each agent in the MAS hierarchy."""
    MASTER = "master_orchestrator"
    PERCEPTRON = "perceptron_agent"
    MEMORY = "memory_agent"
    VERIFIER = "verifier_agent"


# ═══════════════════════════════════════════════════════════════════════
# 2. Tree of Thoughts
# ═══════════════════════════════════════════════════════════════════════

class ThoughtNode(BaseModel):
    """A single node in the Tree of Thoughts (ToT) search tree.

    Each node holds a partial hypothesis (thought), its evaluation score,
    and an optional payload with engine-specific data attachments.
    """
    model_config = ConfigDict(frozen=True)

    id: str = Field(
        default_factory=lambda: uuid.uuid4().hex[:12],
        description="Unique node identifier",
    )
    parent_id: Optional[str] = Field(
        default=None,
        description="Parent node ID (None for root)",
    )
    thought: str = Field(
        ...,
        min_length=1,
        description="Natural-language hypothesis or partial solution",
    )
    score: NodeScore = Field(
        default=NodeScore.MAYBE,
        description="Meta-cognitive evaluation score",
    )
    evaluation: str = Field(
        default="",
        description="Textual justification for the assigned score",
    )
    depth: int = Field(
        default=0,
        ge=0,
        description="Depth level in the ToT tree (root = 0)",
    )
    payload: Dict[str, Any] = Field(
        default_factory=dict,
        description="Engine-specific data attachments",
    )


# ═══════════════════════════════════════════════════════════════════════
# 3. Bayesian Inference
# ═══════════════════════════════════════════════════════════════════════

class BayesianPrior(BaseModel):
    """Input schema for Bayesian probability update.

    Encodes: P(H|E) = P(E|H)·P(H) / [P(E|H)·P(H) + P(E|¬H)·(1−P(H))]
    """
    model_config = ConfigDict(frozen=True)

    hypothesis: str = Field(
        ...,
        description="Natural-language hypothesis label",
    )
    prior_prob: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Prior probability P(H)",
    )
    likelihood: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Likelihood P(E|H)",
    )
    evidence_given_not_h: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="P(E|¬H) — probability of evidence given NOT hypothesis",
    )


class BayesianResult(BaseModel):
    """Output of a Bayesian update."""
    model_config = ConfigDict(frozen=True)

    hypothesis: str
    prior: float
    likelihood: float
    evidence_given_not_h: float
    posterior: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Posterior probability P(H|E)",
    )
    evidence_total: float = Field(
        ...,
        description="Total evidence P(E)",
    )


# ═══════════════════════════════════════════════════════════════════════
# 4. Fuzzy Logic
# ═══════════════════════════════════════════════════════════════════════

class FuzzySet(BaseModel):
    """A single fuzzy membership evaluation."""
    model_config = ConfigDict(frozen=True)

    variable_name: str = Field(
        ...,
        description="Name of the linguistic variable",
    )
    crisp_value: float = Field(
        ...,
        description="Original crisp numeric value",
    )
    membership_degree: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Degree of membership μ(x) ∈ [0, 1]",
    )
    label: str = Field(
        ...,
        description="Linguistic label (e.g., 'low', 'medium', 'high')",
    )


# ═══════════════════════════════════════════════════════════════════════
# 5. SAT / CNF Logic
# ═══════════════════════════════════════════════════════════════════════

class CNFClause(BaseModel):
    """A clause in Conjunctive Normal Form (CNF).

    Each literal is a string: positive (e.g. 'A') or negated (e.g. 'NOT_A').
    A clause is a disjunction (OR) of its literals.
    The full CNF formula is a conjunction (AND) of all clauses.
    """
    model_config = ConfigDict(frozen=True)

    literals: List[str] = Field(
        ...,
        min_length=1,
        description="List of literals forming the disjunction",
    )


class SATResult(BaseModel):
    """Result of a Z3 SAT satisfiability check."""
    model_config = ConfigDict(frozen=True)

    satisfiable: bool = Field(
        ...,
        description="True if the CNF formula is satisfiable",
    )
    model: Optional[Dict[str, bool]] = Field(
        default=None,
        description="Satisfying variable assignment (if SAT)",
    )
    conflict_clause: Optional[List[str]] = Field(
        default=None,
        description="Learned conflict clause (if UNSAT)",
    )


# ═══════════════════════════════════════════════════════════════════════
# 6. Nash Bargaining / Negotiation
# ═══════════════════════════════════════════════════════════════════════

class NegotiationState(BaseModel):
    """State snapshot for axiomatic bargaining between agents."""
    model_config = ConfigDict(frozen=True)

    agent_utilities: Dict[str, float] = Field(
        ...,
        description="Current utility values per agent",
    )
    disagreement_point: Dict[str, float] = Field(
        ...,
        description="Disagreement (threat) point per agent",
    )
    pareto_optimal: bool = Field(
        default=False,
        description="Whether the current allocation is Pareto-optimal",
    )


class NashEquilibriumResult(BaseModel):
    """Result of Nash bargaining optimization."""
    model_config = ConfigDict(frozen=True)

    optimal_utilities: Dict[str, float] = Field(
        ...,
        description="Utility allocation at Nash equilibrium",
    )
    nash_product: float = Field(
        ...,
        description="Value of the Nash product at equilibrium",
    )
    pareto_optimal: bool = Field(
        default=True,
        description="Whether the solution lies on the Pareto frontier",
    )


# ═══════════════════════════════════════════════════════════════════════
# 7. Causal / Abductive
# ═══════════════════════════════════════════════════════════════════════

class CausalIntervention(BaseModel):
    """Result of a Pearl do-calculus intervention."""
    model_config = ConfigDict(frozen=True)

    intervention_var: str
    original_parents: List[str] = Field(default_factory=list)
    remaining_edges: int = Field(default=0)
    mutated_graph_nodes: List[str] = Field(default_factory=list)


class AbductiveDiagnosis(BaseModel):
    """Result of abductive inference (Occam's Razor minimal cover)."""
    model_config = ConfigDict(frozen=True)

    observations: List[str]
    minimal_hypotheses: List[str]
    cardinality: int = Field(ge=0)


# ═══════════════════════════════════════════════════════════════════════
# 8. Default Logic / CBR
# ═══════════════════════════════════════════════════════════════════════

class DefaultRule(BaseModel):
    """A default logic rule: α : β / γ

    prerequisite (α): must be provable from the fact base.
    justification (β): must be consistent (¬β not in fact base).
    consequent (γ): the conclusion drawn if both conditions hold.
    """
    model_config = ConfigDict(frozen=True)

    prerequisite: str = Field(..., description="α — prerequisite fact")
    justification: str = Field(..., description="β — consistency assumption")
    consequent: str = Field(..., description="γ — derived conclusion")


class CBRCase(BaseModel):
    """A case in the Case-Based Reasoning memory store."""
    model_config = ConfigDict(frozen=True)

    case_id: str = Field(
        default_factory=lambda: uuid.uuid4().hex[:12],
    )
    problem_features: Dict[str, float] = Field(
        ...,
        description="Numeric feature vector of the problem",
    )
    solution: Dict[str, Any] = Field(
        ...,
        description="Solution that was applied",
    )
    outcome: Optional[str] = Field(
        default=None,
        description="Observed outcome after applying the solution",
    )


# ═══════════════════════════════════════════════════════════════════════
# 9. ISO 704 / Ontological Normalization
# ═══════════════════════════════════════════════════════════════════════

class RDFTriple(BaseModel):
    """An RDF/OWL-compatible triple [Subject, Predicate, Object]."""
    model_config = ConfigDict(frozen=True)

    subject: str
    predicate: str
    object: str


class NormalizationResult(BaseModel):
    """Output of ISO 704 linguistic normalization."""
    model_config = ConfigDict(frozen=True)

    original_text: str
    cleaned_text: str
    pos_tags: List[Tuple[str, str]] = Field(
        default_factory=list,
        description="List of (token, POS-tag) pairs",
    )
    noun_phrases: List[str] = Field(default_factory=list)
    triples: List[RDFTriple] = Field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════
# 10. Inter-Agent Communication
# ═══════════════════════════════════════════════════════════════════════

class AgentResponse(BaseModel):
    """Standardized response envelope from any subordinate agent."""
    model_config = ConfigDict(frozen=True)

    agent_id: str = Field(
        ...,
        description="Canonical agent identifier (AgentRole value)",
    )
    status: str = Field(
        ...,
        description="Execution status (e.g., 'success', 'error', 'pruned')",
    )
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Engine-specific result payload",
    )
    cnf_proof: Optional[List[str]] = Field(
        default=None,
        description="CNF proof trace from verifier (if applicable)",
    )
    score: NodeScore = Field(
        default=NodeScore.MAYBE,
        description="Evaluated score for the thought under analysis",
    )


# ═══════════════════════════════════════════════════════════════════════
# 11. API Request / Response Envelope
# ═══════════════════════════════════════════════════════════════════════

class SolveRequest(BaseModel):
    """Inbound request to the /api/v1/solve endpoint."""
    query: str = Field(
        ...,
        min_length=1,
        description="Complex systemic query to solve",
    )
    max_depth: Optional[int] = Field(
        default=None,
        ge=1,
        le=10,
        description="Override default MCTS max depth",
    )
    branching_factor: Optional[int] = Field(
        default=None,
        ge=2,
        le=10,
        description="Override default branching factor",
    )


class SolveResponse(BaseModel):
    """Outbound response from the /api/v1/solve endpoint."""
    query: str
    thought_tree: List[ThoughtNode] = Field(default_factory=list)
    delegation_trace: List[AgentResponse] = Field(default_factory=list)
    pruning_log: List[Dict[str, Any]] = Field(default_factory=list)
    optimal_solution: Optional[str] = Field(default=None)
    generative_ui_schema: Optional[Dict[str, Any]] = Field(default=None)
    execution_time_ms: float = Field(default=0.0)
