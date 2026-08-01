"""
MAS-8ENGINE │ config/settings.py
Application-level configuration using Pydantic Settings v2.

Loads environment variables with typed defaults for Z3, Redis, MCTS,
and API server configuration.
"""
from __future__ import annotations

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Centralized, type-safe application configuration."""

    # ── API Server ──────────────────────────────────────────────────
    api_host: str = Field(default="0.0.0.0", description="FastAPI bind host")
    api_port: int = Field(default=8000, description="FastAPI bind port")
    api_workers: int = Field(default=1, description="Uvicorn worker count")
    debug: bool = Field(default=False, description="Enable debug mode")

    # ── Redis (MCTS state persistence) ──────────────────────────────
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for MCTS state caching",
    )
    redis_ttl_seconds: int = Field(
        default=3600,
        description="TTL in seconds for cached MCTS states",
    )

    # ── MCTS / Tree of Thoughts ─────────────────────────────────────
    mcts_max_depth: int = Field(
        default=5,
        description="Maximum depth of the Tree of Thoughts exploration",
    )
    mcts_branching_factor: int = Field(
        default=3,
        description="Number of sub-hypotheses generated per ToT node",
    )
    mcts_exploration_constant: float = Field(
        default=1.414,
        description="UCB1 exploration constant (sqrt(2) by default)",
    )

    # ── Z3 SAT Solver ───────────────────────────────────────────────
    z3_timeout_ms: int = Field(
        default=30000,
        description="Z3 solver timeout in milliseconds",
    )

    # ── Nash Bargaining ─────────────────────────────────────────────
    nash_optimizer_max_iter: int = Field(
        default=1000,
        description="Maximum iterations for SciPy SLSQP optimizer",
    )
    nash_optimizer_tol: float = Field(
        default=1e-9,
        description="Convergence tolerance for Nash product maximization",
    )

    # ── NLP / ISO 704 ──────────────────────────────────────────────
    nlp_language: str = Field(
        default="es",
        description="Default language code for NLP processing",
    )

    # ── Ollama Local ────────────────────────────────────────────────
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Base URL for Ollama local LLM server",
    )
    ollama_model: str = Field(
        default="qwen3:8b",
        description="Default fallback model for Ollama inference",
    )
    ollama_model_ooda: str = Field(
        default="architect-omega:latest",
        description="OODA model for structural decision making & hypothesis generation",
    )
    ollama_model_sota: str = Field(
        default="qwen3:8b",
        description="SOTA model for natural language expert synthesis",
    )

    model_config = {
        "env_prefix": "MAS8_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


# Singleton instance — import this across the application
settings = Settings()
