"""
MAS-8ENGINE │ test_project12_redteaming.py
Pruebas unitarias para el Proyecto 12:
- Auditoría Adversaria Red Teaming (OWASP LLM01/LLM02)
- Simulación de Caos e Inyección de Fallos
"""
import pytest
from agents.red_teaming_agent import RedTeamingAgent
from engines.chaos_engine import ChaosEngine


def test_red_teaming_audit_suite():
    report = RedTeamingAgent.run_security_audit_suite()
    
    assert report.total_attacks == 5
    assert report.block_rate_pct >= 80.0
    assert report.successful_blocks >= 4
    assert len(report.detected_threats) > 0


@pytest.mark.asyncio
async def test_chaos_engine_injection():
    res = await ChaosEngine.inject_simulated_failure("backend_api")
    
    assert res.injection_type == "DAEMON_PORT_DISRUPTION"
    assert res.target_service == "backend_api"
    assert res.status_after is False  # Fallo inducido
    assert res.recovery_confirmed is True  # Servicio real restablecido
