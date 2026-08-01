from __future__ import annotations

import z3
from typing import List, Dict, Any, Optional

from core.schemas import CNFClause, SATResult

class Z3SATVerifier:
    """
    Z3-based SMT/SAT verifier for CNF structures.
    """
    def __init__(self, timeout_ms: int = 30000) -> None:
        self.timeout_ms = timeout_ms

    def verify_cnf(self, clauses: List[CNFClause]) -> SATResult:
        solver = z3.Solver()
        solver.set("timeout", self.timeout_ms)
        
        variables: Dict[str, z3.BoolRef] = {}
        
        # Extract all unique variable names
        for clause in clauses:
            for lit in clause.literals:
                var_name = lit[4:] if lit.startswith("NOT_") else lit
                if var_name not in variables:
                    variables[var_name] = z3.Bool(var_name)
                    
        z3_clauses = []
        for clause in clauses:
            z3_literals = []
            for lit in clause.literals:
                var_name = lit[4:] if lit.startswith("NOT_") else lit
                if lit.startswith("NOT_"):
                    z3_literals.append(z3.Not(variables[var_name]))
                else:
                    z3_literals.append(variables[var_name])
            
            if z3_literals:
                z3_clauses.append(z3.Or(*z3_literals))
            else:
                z3_clauses.append(z3.BoolVal(False))
                
        # Assert z3.And of all clauses into a z3.Solver()
        if z3_clauses:
            solver.add(z3.And(*z3_clauses))
            
        result = solver.check()
        
        if result == z3.sat:
            model = solver.model()
            model_dict: Dict[str, bool] = {}
            for var_name, z3_var in variables.items():
                val = model.evaluate(z3_var, model_completion=True)
                model_dict[var_name] = bool(z3.is_true(val))
            return SATResult(satisfiable=True, model=model_dict, conflict_clause=None)
        else:
            # Without tracking, unsat_core is empty. 
            # Implemented fallback empty list as requested.
            return SATResult(satisfiable=False, model=None, conflict_clause=[])

    def verify_propositions(self, propositions: Dict[str, bool]) -> SATResult:
        clauses: List[CNFClause] = []
        for var, val in propositions.items():
            lit = var if val else f"NOT_{var}"
            clauses.append(CNFClause(literals=[lit]))
        return self.verify_cnf(clauses)
