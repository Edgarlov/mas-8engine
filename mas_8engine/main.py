"""
MAS-8ENGINE │ main.py
FastAPI application exposing the POST /api/v1/solve endpoint.

Accepts complex systemic queries and returns the full JSON execution
trace including the Tree of Thoughts, agent delegation, pruning log,
and optimal solution.
"""
from __future__ import annotations

import logging
import sys

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings
from core.schemas import SolveRequest, SolveResponse
from agents.master_orchestrator import MasterOrchestrator

# ── Logging Configuration ───────────────────────────────────────────
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(name)-30s | %(levelname)-8s | %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("mas_8engine")

# ── FastAPI Application ─────────────────────────────────────────────
app = FastAPI(
    title="MAS-8ENGINE",
    description=(
        "Multi-Agent System with 8-Engine Reasoning Taxonomy: "
        "Bayesian Inference, Fuzzy Logic, Default Logic, CBR, "
        "Abductive Diagnosis, Z3 SAT/CDCL Verification, "
        "Pearl's Do-Calculus, and Meta-Cognitive Tree of Thoughts (MCTS)."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Orchestrator Singleton ──────────────────────────────────────────
orchestrator = MasterOrchestrator()


# ── Health Check ────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health_check() -> dict:
    """Health check endpoint returning system status."""
    return {
        "status": "operational",
        "system": "MAS-8ENGINE",
        "version": "1.0.0",
        "engines": [
            "bayesian_inference",
            "fuzzy_logic",
            "default_logic",
            "case_based_reasoning",
            "abductive_diagnosis",
            "z3_sat_cdcl",
            "pearl_do_calculus",
            "tree_of_thoughts_mcts",
        ],
        "agents": [
            "master_orchestrator",
            "perceptron_agent",
            "memory_agent",
            "verifier_agent",
        ],
    }


# ── Main Solve Endpoint ────────────────────────────────────────────
@app.post(
    "/api/v1/solve",
    response_model=SolveResponse,
    tags=["Reasoning"],
    summary="Execute multi-agent reasoning pipeline",
    description=(
        "Accepts a complex systemic query and processes it through the "
        "Tree of Thoughts / MCTS pipeline, delegating to Perceptron, "
        "Memory, and Verifier agents. Returns the full execution trace."
    ),
)
async def solve(request: SolveRequest) -> SolveResponse:
    """Process a complex systemic query through the MAS-8ENGINE pipeline."""
    logger.info("Received solve request: %s", request.query[:100])

    try:
        current_orchestrator = MasterOrchestrator()
        response = await current_orchestrator.solve(request)
        logger.info(
            "Solve completed in %.2f ms — nodes: %d, prunings: %d",
            response.execution_time_ms,
            len(response.thought_tree),
            len(response.pruning_log),
        )
        return response

    except Exception as exc:
        logger.error("Solve failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal reasoning error: {exc}",
        ) from exc


# ── Uvicorn Runner ──────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        workers=settings.api_workers,
        reload=settings.debug,
    )
