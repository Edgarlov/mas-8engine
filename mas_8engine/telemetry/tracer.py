"""
MAS-8ENGINE │ tracer.py
Decoradores y métricas de Observabilidad y Telemetría para Herramientas MCP y Motores Matemáticos.
"""
from __future__ import annotations

import time
import functools
import logging
from typing import Any, Callable, Dict, List
from pydantic import BaseModel

logger = logging.getLogger("mas8_telemetry")


class MetricEvent(BaseModel):
    tool_name: str
    execution_time_ms: float
    status: str
    error_message: str = ""


class TelemetryTracer:
    """Registrador de métricas de trazabilidad y rendimiento en tiempo real."""
    
    events: List[MetricEvent] = []

    @classmethod
    def trace_tool(cls, tool_name: str):
        def decorator(func: Callable):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                start_t = time.perf_counter()
                status = "SUCCESS"
                err_msg = ""
                try:
                    res = await func(*args, **kwargs)
                    return res
                except Exception as exc:
                    status = "FAILED"
                    err_msg = str(exc)
                    raise exc
                finally:
                    elapsed = (time.perf_counter() - start_t) * 1000.0
                    event = MetricEvent(
                        tool_name=tool_name,
                        execution_time_ms=round(elapsed, 2),
                        status=status,
                        error_message=err_msg
                    )
                    cls.events.append(event)
                    logger.info(f"[TELEMETRÍA] {tool_name} | Latencia: {elapsed:.2f}ms | Estado: {status}")
            return wrapper
        return decorator

    @classmethod
    def get_summary(cls) -> Dict[str, Any]:
        if not cls.events:
            return {"total_events": 0, "avg_latency_ms": 0.0, "success_rate": 100.0}

        tot = len(cls.events)
        avg_lat = sum(e.execution_time_ms for e in cls.events) / tot
        successes = sum(1 for e in cls.events if e.status == "SUCCESS")
        
        return {
            "total_events": tot,
            "avg_latency_ms": round(avg_lat, 2),
            "success_rate_pct": round((successes / tot) * 100.0, 1)
        }
