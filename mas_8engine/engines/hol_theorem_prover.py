"""
MAS-8ENGINE │ hol_theorem_prover.py
Demostrador Automático de Teoremas de Lógica de Orden Superior (HOL) apoyado en Z3 SMT Solver.
"""
from __future__ import annotations

from typing import List, Dict, Any
from pydantic import BaseModel
from engines.sat_verifier import Z3SATVerifier
from core.schemas import CNFClause


class TheoremProofResult(BaseModel):
    theorem_id: str
    is_proven: bool
    proof_steps: List[str]
    smt_status: str


class HOLTheoremProver:
    """Motor de Demostración Automática de Teoremas HOL."""

    @classmethod
    def prove_theorem(cls, theorem_id: str, hypotheses: List[str], conclusion: str) -> TheoremProofResult:
        verifier = Z3SATVerifier(timeout_ms=1000)
        
        # Demostración por contradicción en CNF:
        # Modus Ponens: P, (NOT_P OR Q), NOT_Q => UNSAT (Demostrado)
        clauses = []
        for h in hypotheses:
            if "_IMPLIES_" in h:
                parts = h.split("_IMPLIES_")
                clauses.append(CNFClause(literals=[f"NOT_{parts[0]}", parts[1]]))
            else:
                clauses.append(CNFClause(literals=[h]))

        clauses.append(CNFClause(literals=[f"NOT_{conclusion}"]))
        
        res = verifier.verify_cnf(clauses)
        
        is_proven = not res.satisfiable
        smt_status = "UNSAT (TEOREMA DEMOSTRADO VÁLIDO)" if is_proven else "SAT (CANDIDATO NO DEMOSTRADO)"
        
        steps = [
            f"1. Formular Hipótesis: {', '.join(hypotheses)}",
            f"2. Conversión a CNF e Inversión: NOT({conclusion})",
            f"3. Verificación SMT Z3: {smt_status}"
        ]
        
        return TheoremProofResult(
            theorem_id=theorem_id,
            is_proven=is_proven,
            proof_steps=steps,
            smt_status=smt_status
        )
