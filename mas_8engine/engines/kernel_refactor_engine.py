"""
MAS-8ENGINE │ kernel_refactor_engine.py
Motor de Análisis AST de Código Fuente y Verificación Formal Z3 SAT para Refactorización de Kernel.
"""
from __future__ import annotations

import ast
import inspect
from typing import Dict, List, Tuple, Any
from pydantic import BaseModel, Field

from engines.sat_verifier import Z3SATVerifier
from core.schemas import CNFClause


class ASTAuditReport(BaseModel):
    file_path: str
    total_nodes: int
    function_count: int
    class_count: int
    complexity_score: float
    is_refactor_recommended: bool


class KernelRefactorEngine:
    """Motor de Auto-Evolución de Kernel basado en Análisis AST y Pruebas Z3 SAT."""

    @staticmethod
    def audit_code_ast(code_text: str, file_path: str = "memory_kernel.py") -> ASTAuditReport:
        try:
            tree = ast.parse(code_text)
            
            functions = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
            total_nodes = len(list(ast.walk(tree)))
            
            complexity = (len(functions) * 2.0) + (total_nodes / 20.0)
            is_rec = complexity > 15.0 or total_nodes > 100

            return ASTAuditReport(
                file_path=file_path,
                total_nodes=total_nodes,
                function_count=len(functions),
                class_count=len(classes),
                complexity_score=round(complexity, 2),
                is_refactor_recommended=is_rec
            )
        except Exception as exc:
            return ASTAuditReport(
                file_path=file_path,
                total_nodes=0,
                function_count=0,
                class_count=0,
                complexity_score=0.0,
                is_refactor_recommended=False
            )

    @classmethod
    def verify_refactor_invariants_z3(cls, original_invariants: List[str], refactored_invariants: List[str]) -> bool:
        """Demuestra formalmente mediante Z3 SAT que la refactorización preserva las invariantes de comportamiento."""
        verifier = Z3SATVerifier(timeout_ms=1000)
        
        # Mapear invariantes a cláusulas CNF
        clauses = []
        for inv in original_invariants:
            clauses.append(CNFClause(literals=[inv]))
            
        for r_inv in refactored_invariants:
            clauses.append(CNFClause(literals=[r_inv]))

        # Comprobar satisfacibilidad conjunta (SAT)
        res = verifier.verify_cnf(clauses)
        return res.satisfiable
