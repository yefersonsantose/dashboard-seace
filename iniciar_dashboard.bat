@echo off
title Dashboard SEACE
echo.
echo  ╔══════════════════════════════════════╗
echo  ║     SEACE Dashboard - Iniciando      ║
echo  ╚══════════════════════════════════════╝
echo.

REM ── Verificar si ya está corriendo ───────────────────────────
netstat -ano | find ":8000" | find "LISTENING" > nul 2>&1
if %ERRORLEVEL% == 0 (
    echo  [OK] Dashboard ya esta corriendo.
    timeout /t 2 /nobreak > nul
    start "" "http://localhost:3000"
    exit /b 0
)

REM ── Iniciar Backend (FastAPI) ─────────────────────────────────
echo  [1/3] Iniciando Backend API...
start /min "SEACE-Backend" cmd /k "cd /d ""%~dp0backend"" && python -m uvicorn app.main:app --port 8000"

REM Esperar que el backend arranque
timeout /t 5 /nobreak > nul

REM ── Iniciar Frontend (Next.js) ────────────────────────────────
echo  [2/3] Iniciando Frontend...
start /min "SEACE-Frontend" cmd /k "cd /d ""%~dp0frontend"" && npm run dev"

REM Esperar que el frontend compile y arranque
echo  [3/3] Esperando que el frontend compile (15 segundos)...
timeout /t 15 /nobreak > nul

REM ── Abrir navegador ──────────────────────────────────────────
echo.
echo  ╔══════════════════════════════════════╗
echo  ║  Dashboard listo en:                 ║
echo  ║  http://localhost:3000               ║
echo  ╚══════════════════════════════════════╝
echo.
start "" "http://localhost:3000"
