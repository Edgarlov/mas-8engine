@echo off
TITLE Sistema Agente-Motor Ontologico v2.0 & Servidores MCP
echo ======================================================================
echo    SISTEMA AGENTICO Y MOTOR ONTOLOGICO v2.0 - INICIO AUTOMATICO (4 MCPs)
echo ======================================================================
echo.

echo [1/3] Verificando estado de Ollama Local...
curl -s http://localhost:11434/api/version > nul
if %errorlevel% neq 0 (
    echo [ADVERTENCIA] Ollama no responde en http://localhost:11434. Asegurese de que Ollama este ejecutandose.
) else (
    echo [OK] Ollama activo en puerto 11434.
)

echo.
echo [2/3] Iniciando Backend FastAPI (MAS-8ENGINE) en http://127.0.0.1:8000 ...
start "Backend MAS-8ENGINE" /D "C:\Users\edgar\Desktop\agentes\mas_8engine" .venv\Scripts\python.exe main.py

echo.
echo [3/3] Iniciando Frontend Generativo (Next.js) en http://localhost:3000 ...
start "Frontend Agéntico" /D "C:\Users\edgar\Desktop\agentes\frontend_agentic" npm run dev

echo.
echo ======================================================================
echo  SISTEMA Y 4 SERVIDORES MCP ACTIVADOS AUTOMATICAMENTE:
echo    1. agente-motor-ontologico-v2  (mas_8engine.mcp_server)
echo    2. sequential-thinking         (@modelcontextprotocol/server-sequential-thinking)
echo    3. filesystem                  (@modelcontextprotocol/server-filesystem)
echo    4. notebooklm                  (notebooklm-mcp v0.9.4)
echo
echo  Acceda a la interfaz web en: http://localhost:3000
echo ======================================================================
pause
