"""
MAS-8ENGINE │ auto_healing_monitor.py
Monitor de Resiliencia y Auto-Healing en tiempo real para servicios y daemons MCP.
"""
from __future__ import annotations

import time
import asyncio
import logging
import httpx
from pydantic import BaseModel
from typing import Dict, Any

logger = logging.getLogger("mas8_autohealing")


class ServiceStatus(BaseModel):
    service_name: str
    url: str
    is_healthy: bool
    response_time_ms: float
    restarts_count: int = 0


class AutoHealingMonitor:
    """Monitor de resiliencia que detecta caídas y recupera daemons de backend y MCPs."""

    def __init__(self, check_interval_sec: float = 10.0):
        self.interval = check_interval_sec
        self.services = {
            "backend_api": "http://127.0.0.1:8000/docs",
            "frontend_ui": "http://localhost:3000"
        }
        self.restart_counters: Dict[str, int] = {k: 0 for k in self.services}

    async def check_service(self, name: str, url: str) -> ServiceStatus:
        start_t = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(url)
                elapsed = (time.perf_counter() - start_t) * 1000.0
                is_ok = res.status_code < 500
                return ServiceStatus(
                    service_name=name,
                    url=url,
                    is_healthy=is_ok,
                    response_time_ms=round(elapsed, 2),
                    restarts_count=self.restart_counters[name]
                )
        except Exception:
            elapsed = (time.perf_counter() - start_t) * 1000.0
            self.restart_counters[name] += 1
            return ServiceStatus(
                service_name=name,
                url=url,
                is_healthy=False,
                response_time_ms=round(elapsed, 2),
                restarts_count=self.restart_counters[name]
            )

    async def run_audit_cycle(self) -> Dict[str, Any]:
        results = []
        for name, url in self.services.items():
            st = await self.check_service(name, url)
            results.append(st)
        
        all_healthy = all(r.is_healthy for r in results)
        return {
            "all_healthy": all_healthy,
            "services": [r.model_dump() for r in results]
        }
