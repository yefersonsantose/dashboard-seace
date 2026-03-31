@echo off
echo.
echo  Deteniendo Dashboard SEACE...

REM Cerrar ventanas por título
taskkill /f /fi "WINDOWTITLE eq SEACE-Backend*" > nul 2>&1
taskkill /f /fi "WINDOWTITLE eq SEACE-Frontend*" > nul 2>&1

REM Matar proceso en puerto 8000 (backend)
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING" 2^>nul') do (
    taskkill /f /pid %%a > nul 2>&1
)

REM Matar proceso en puerto 3000 (frontend)
for /f "tokens=5" %%a in ('netstat -aon ^| find ":3000" ^| find "LISTENING" 2^>nul') do (
    taskkill /f /pid %%a > nul 2>&1
)

echo  Dashboard detenido correctamente.
timeout /t 2 /nobreak > nul
