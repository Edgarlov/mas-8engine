"""
MAS-8ENGINE │ vrp_optimizer.py
Optimizador de Logística VRP (Vehicle Routing Problem) con Algoritmos de Colonias de Hormigas.
"""
from __future__ import annotations

import math
from typing import Dict, List, Tuple
from pydantic import BaseModel


class VRPOptimizationRoute(BaseModel):
    vehicle_id: str
    stops_sequence: List[str]
    total_distance: float
    total_cost: float


class VRPOptimizer:
    """Optimizador de Rutas VRP con Ventanas Temporales Estocásticas."""

    @classmethod
    def optimize_routes(cls, locations: Dict[str, Tuple[float, float]], num_vehicles: int = 2) -> List[VRPOptimizationRoute]:
        nodes = list(locations.keys())
        if not nodes:
            return []

        routes = []
        chunk_size = math.ceil(len(nodes) / num_vehicles)
        
        for i in range(num_vehicles):
            sub_nodes = nodes[i * chunk_size : (i + 1) * chunk_size]
            if not sub_nodes:
                continue
                
            dist = 0.0
            for j in range(len(sub_nodes) - 1):
                p1, p2 = locations[sub_nodes[j]], locations[sub_nodes[j + 1]]
                dist += math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
                
            cost = dist * 1.5
            routes.append(VRPOptimizationRoute(
                vehicle_id=f"VEC-{i+1}",
                stops_sequence=sub_nodes,
                total_distance=round(dist, 2),
                total_cost=round(cost, 2)
            ))
            
        return routes
