from __future__ import annotations

import numpy as np
from scipy.optimize import minimize, OptimizeResult
from typing import Dict, Any, List

from core.schemas import NegotiationState, NashEquilibriumResult

class NashBargainingEngine:
    """
    Nash Bargaining Engine para resolución de asignación y maximización del producto de Nash.
    """
    def __init__(self, max_iter: int = 1000, tol: float = 1e-9) -> None:
        self.max_iter = max_iter
        self.tol = tol

    def compute_nash_equilibrium(self, utility_matrix: np.ndarray, disagreement_point: np.ndarray) -> NashEquilibriumResult:
        n_agents, m_allocations = utility_matrix.shape
        
        def objective(x: np.ndarray) -> float:
            u_x = utility_matrix @ x
            diff = u_x - disagreement_point
            # Clipping para evitar problemas numéricos y ceros en el producto
            diff = np.maximum(diff, 1e-12)
            return -float(np.prod(diff))
            
        x0 = np.ones(m_allocations) / m_allocations
        
        constraints = (
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0}
        )
        bounds = [(0.0, 1.0) for _ in range(m_allocations)]
        
        res: OptimizeResult = minimize(
            objective,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'maxiter': self.max_iter, 'ftol': self.tol}
        )
        
        optimal_x = res.x
        u_opt = utility_matrix @ optimal_x
        nash_product = -res.fun
        
        optimal_utilities: Dict[str, float] = {
            f"agent_{i}": float(u_opt[i]) for i in range(n_agents)
        }
        
        return NashEquilibriumResult(
            optimal_utilities=optimal_utilities,
            nash_product=float(nash_product),
            pareto_optimal=True
        )

    def compute_kalai_smorodinsky(self, utility_matrix: np.ndarray, disagreement_point: np.ndarray) -> NashEquilibriumResult:
        n_agents, m_allocations = utility_matrix.shape
        
        # Utopia point computation
        utopia_point = np.max(utility_matrix, axis=1)
        direction = utopia_point - disagreement_point
        
        norm = np.linalg.norm(direction)
        if norm < 1e-12:
            direction_norm = np.ones_like(direction) / n_agents
        else:
            direction_norm = direction / norm
            
        def constraint_fun(t_and_x: np.ndarray) -> np.ndarray:
            t = t_and_x[0]
            x = t_and_x[1:]
            u_x = utility_matrix @ x
            target = disagreement_point + t * direction_norm
            return u_x - target
            
        t_x0 = np.zeros(1 + m_allocations)
        t_x0[1:] = np.ones(m_allocations) / m_allocations
        
        constraints = [
            {'type': 'eq', 'fun': lambda tx: np.sum(tx[1:]) - 1.0},
            {'type': 'eq', 'fun': constraint_fun}
        ]
        
        bounds = [(0.0, None)] + [(0.0, 1.0) for _ in range(m_allocations)]
        
        res: OptimizeResult = minimize(
            lambda tx: -float(tx[0]),
            t_x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints,
            options={'maxiter': self.max_iter, 'ftol': self.tol}
        )
        
        optimal_x = res.x[1:]
        u_opt = utility_matrix @ optimal_x
        
        diff = np.maximum(u_opt - disagreement_point, 1e-12)
        nash_product = float(np.prod(diff))
        
        optimal_utilities: Dict[str, float] = {
            f"agent_{i}": float(u_opt[i]) for i in range(n_agents)
        }
        
        return NashEquilibriumResult(
            optimal_utilities=optimal_utilities,
            nash_product=nash_product,
            pareto_optimal=True
        )

    def is_pareto_optimal(self, utilities: np.ndarray, feasible_set: np.ndarray) -> bool:
        dominance_geq = np.all(feasible_set >= utilities, axis=1)
        dominance_gt = np.any(feasible_set > utilities, axis=1)
        dominated = np.any(dominance_geq & dominance_gt)
        return not bool(dominated)
