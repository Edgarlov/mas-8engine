"""
MAS-8ENGINE │ security_guardrails.py
Motor de Seguridad, Desinfección y Políticas Formales Z3 para Agentes de IA.
Alineado con OWASP Top 10 para LLMs, MITRE ATLAS y NIST AI RMF 1.0.
"""
from __future__ import annotations

import re
from typing import Dict, List, Tuple
from pydantic import BaseModel, Field

from engines.sat_verifier import Z3SATVerifier
from core.schemas import CNFClause


class SecurityAuditResult(BaseModel):
    is_safe: bool
    risk_score: float = Field(ge=0.0, le=100.0, description="Puntuación de riesgo 0-100")
    threat_category: str
    detected_patterns: List[str]
    sanitized_input: str
    z3_policy_status: str


class AgenticSecurityGuardrails:
    """Motor de Guardrails de Seguridad para el Sistema Agéntico MAS-8ENGINE."""

    # Patrones de Prompt Injection y Jailbreaking (OWASP LLM01)
    PROMPT_INJECTION_PATTERNS = [
        r"ignore\s+previous\s+instructions",
        r"ignore\s+all\s+prior\s+prompts",
        r"system\s+override",
        r"dan\s+mode",
        r"sudo\s+mode",
        r"bypass\s+security",
        r"reveal\s+system\s+prompt",
        r"disregard\s+safety\s+rules",
        r"eval\(",
        r"exec\(",
        r"import\s+os;\s*os\.system",
        r"rm\s+-rf"
    ]

    # Caracteres peligrosos de inyección de comandos Shell (OWASP LLM02)
    SHELL_INJECTION_CHARS = re.compile(r'[;&|`$><]')

    @classmethod
    def sanitize_input(cls, text: str) -> Tuple[str, List[str]]:
        detected = []
        lowered = text.lower()
        
        for pattern in cls.PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, lowered):
                detected.append(f"INJECTION_PATTERN: {pattern}")
                
        if cls.SHELL_INJECTION_CHARS.search(text):
            detected.append("SHELL_METACHARACTERS_DETECTED")
            
        # Desinfección: neutralización de metacaracteres peligrosos
        sanitized = cls.SHELL_INJECTION_CHARS.sub('', text)
        return sanitized, detected

    @classmethod
    def verify_formal_security_policy(cls, text: str) -> str:
        """Verifica mediante Z3 SAT que la entrada no viole los axiomas de seguridad."""
        verifier = Z3SATVerifier(timeout_ms=1000)
        lowered = text.lower()
        
        # Clausulas de Invariante de Seguridad
        # Si se solicita acceso no autorizado o RCE, la política debe ser UNSATISFACIBLE
        has_unauthorized_req = "override" in lowered or "bypass" in lowered or "eval(" in lowered
        
        clauses = [
            CNFClause(literals=["AGENT_AUTHORIZATION_VALID"]),
            CNFClause(literals=["NOT_UNAUTHORIZED_ACCESS"])
        ]
        
        if has_unauthorized_req:
            # Añadir contradicción forzada: AUTHORIZATION_VALID AND NOT_AUTHORIZATION_VALID
            clauses.append(CNFClause(literals=["NOT_AGENT_AUTHORIZATION_VALID"]))
            
        res = verifier.verify_cnf(clauses)
        return "SATISFACIBLE (POLÍTICA APROBADA)" if res.satisfiable else "UNSAT (POLÍTICA DE SEGURIDAD VIOLADA)"

    @classmethod
    def audit_prompt(cls, prompt_text: str) -> SecurityAuditResult:
        sanitized, detected = cls.sanitize_input(prompt_text)
        policy_status = cls.verify_formal_security_policy(prompt_text)
        
        risk_score = 0.0
        if detected:
            risk_score += 40.0 * len(detected)
        if "UNSAT" in policy_status:
            risk_score += 60.0

        risk_score = min(100.0, risk_score)
        is_safe = risk_score < 50.0 and "UNSAT" not in policy_status
        
        threat_cat = "OWASP LLM01: Prompt Injection" if detected else ("OWASP LLM05: Policy Violation" if not is_safe else "SECURE")

        return SecurityAuditResult(
            is_safe=is_safe,
            risk_score=round(risk_score, 1),
            threat_category=threat_cat,
            detected_patterns=detected,
            sanitized_input=sanitized,
            z3_policy_status=policy_status
        )
