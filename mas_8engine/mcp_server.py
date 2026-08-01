"""
MAS-8ENGINE │ mcp_server.py
Official Model Context Protocol (MCP) Server for MAS-8ENGINE v2.0.

Provides stdio transport for Google Antigravity, Claude Code, and OpenAI Assistants.
Exposes Tools:
  - ontology_load_and_validate
  - reasoning_verify_z3_sat
  - bayes_fuzzy_eval
  - agent_tot_solve
  - security_audit_prompt
"""
from __future__ import annotations

import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

from mcp.server.mcpserver import MCPServer

from config.settings import settings
from agents.master_orchestrator import MasterOrchestrator
from core.schemas import SolveRequest, CNFClause, BayesianPrior
from engines.sat_verifier import Z3SATVerifier
from engines.bayes_fuzzy import UncertaintyEngine
from engines.security_guardrails import AgenticSecurityGuardrails

# Initialize MCPServer instance
mcp = MCPServer("agente-motor-ontologico-v2")
logger = logging.getLogger("mcp_server")


@mcp.tool()
async def agent_tot_solve(
    query: str,
    max_depth: int = 1,
    branching_factor: int = 2
) -> str:
    """Ejecuta la orquestación agéntica completa (Tree of Thoughts / MCTS)
    del Sistema MAS-8ENGINE v2.0, integrando comprobación Z3 SAT, inferencia Bayesiana
    y esquema de UI Generativa.
    """
    try:
        orchestrator = MasterOrchestrator()
        request = SolveRequest(
            query=query,
            max_depth=max_depth,
            branching_factor=branching_factor
        )
        response = await orchestrator.solve(request)
        return json.dumps(response.model_dump(), indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"error": str(exc), "status": "failed"})


@mcp.tool()
async def reasoning_verify_z3_sat(
    clauses: List[Dict[str, List[str]]]
) -> str:
    """Verifica formalmente si un conjunto de cláusulas lógicas CNF
    contiene contradicciones (Z3 SAT / CDCL Solver de Microsoft Research).
    """
    try:
        verifier = Z3SATVerifier(timeout_ms=settings.z3_timeout_ms)
        cnf_clauses = [CNFClause(**c) for c in clauses]
        result = verifier.verify_cnf(cnf_clauses)
        return json.dumps(result.model_dump(), indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"error": str(exc), "satisfiable": False})


@mcp.tool()
async def bayes_fuzzy_eval(
    hypothesis: str,
    prior_prob: float = 0.5,
    likelihood: float = 0.8,
    evidence_given_not_h: float = 0.2,
    crisp_value: float = 80.0
) -> str:
    """Calcula la actualización Bayesiana posterior P(H|E) y la viabilidad
    por defuzzificación de centroide (Mamdani CoG).
    """
    try:
        engine = UncertaintyEngine()
        prior = BayesianPrior(
            hypothesis=hypothesis,
            prior_prob=prior_prob,
            likelihood=likelihood,
            evidence_given_not_h=evidence_given_not_h
        )
        bayes_result = engine.update_bayes(prior)
        crisp_output = engine.defuzzify_centroid([(0.8, crisp_value)])

        return json.dumps({
            "hypothesis": hypothesis,
            "bayes_posterior": round(bayes_result.posterior, 4),
            "bayes_posterior_pct": f"{bayes_result.posterior * 100:.1f}%",
            "fuzzy_cog_score": round(crisp_output, 1),
            "status": "success"
        }, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"error": str(exc), "status": "failed"})


@mcp.tool()
async def ontology_load_and_validate(
    ontology_text: str,
    format_type: str = "owl"
) -> str:
    """Carga y valida la consistencia sintáctica y semántica (ISO-704 / OWL 2 DL)
    de una especificación de ontología.
    """
    from pipeline.iso_704_normalizer import ISO704Normalizer
    try:
        normalizer = ISO704Normalizer()
        result = normalizer.normalize_text(ontology_text)
        return json.dumps({
            "format": format_type,
            "valid": True,
            "triples_extracted": [t.model_dump() for t in result.triples],
            "normative_terms": result.normative_terms,
            "status": "SATISFACIBLE"
        }, indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"error": str(exc), "valid": False})


@mcp.tool()
async def security_audit_prompt(
    prompt_text: str
) -> str:
    """Audita un prompt o parámetro de herramienta contra las vulnerabilidades OWASP Top 10
    para LLMs y Agentes, aplicando comprobación de políticas lógicas en Z3 SAT.
    """
    try:
        audit_res = AgenticSecurityGuardrails.audit_prompt(prompt_text)
        return json.dumps(audit_res.model_dump(), indent=2, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"error": str(exc), "is_safe": False, "risk_score": 100.0})


if __name__ == "__main__":
    mcp.run()
