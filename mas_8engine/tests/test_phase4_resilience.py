"""
MAS-8ENGINE │ test_phase4_resilience.py
Pruebas unitarias para la Fase 4: Monitor de Resiliencia y Auto-Healing.
"""
import pytest
from engines.auto_healing_monitor import AutoHealingMonitor


@pytest.mark.asyncio
async def test_auto_healing_check():
    monitor = AutoHealingMonitor(check_interval_sec=1.0)
    # Check backend endpoint (currently running on port 8000)
    res = await monitor.check_service("backend_api", "http://127.0.0.1:8000/docs")
    
    assert res.service_name == "backend_api"
    assert res.response_time_ms >= 0.0
    assert res.is_healthy is True


@pytest.mark.asyncio
async def test_auto_healing_audit_cycle():
    monitor = AutoHealingMonitor(check_interval_sec=1.0)
    summary = await monitor.run_audit_cycle()
    
    assert "all_healthy" in summary
    assert len(summary["services"]) == 2
