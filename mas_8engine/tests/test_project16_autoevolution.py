"""
MAS-8ENGINE │ test_project16_autoevolution.py
Pruebas unitarias para el Proyecto 16:
- Análisis AST de Código Fuente
- Verificación Formal Z3 SAT de Invariantes en Refactorización
"""
import pytest
from engines.kernel_refactor_engine import KernelRefactorEngine


def test_ast_code_audit():
    sample_code = """
def calculate_metrics(a, b):
    result = a + b
    return result

class MemoryManager:
    def __init__(self):
        self.data = []
"""
    report = KernelRefactorEngine.audit_code_ast(sample_code, "sample.py")
    
    assert report.function_count == 2  # calculate_metrics + __init__
    assert report.class_count == 1
    assert report.total_nodes > 0
    assert report.complexity_score > 0.0


def test_z3_refactor_invariant_verification():
    orig_inv = ["INVARIANT_A_VALID", "INVARIANT_B_VALID"]
    refact_inv = ["INVARIANT_A_VALID", "INVARIANT_B_OPTIMIZED"]
    
    # Ambas invariantes no contienen contradicciones -> Z3 SAT
    is_valid = KernelRefactorEngine.verify_refactor_invariants_z3(orig_inv, refact_inv)
    assert is_valid is True
