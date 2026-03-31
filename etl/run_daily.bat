@echo off
REM ============================================================
REM  SEACE Dashboard — Actualización diaria automática
REM  Descarga el archivo del año actual desde el portal OCDS
REM  y actualiza la base de datos SQLite.
REM
REM  Para registrar en Windows Task Scheduler ejecuta:
REM    setup_task.bat
REM ============================================================

cd /d "%~dp0"

echo [%DATE% %TIME%] Iniciando ETL diario SEACE... >> logs\scheduler.log

python run.py --year %DATE:~6,4%

if %ERRORLEVEL% == 0 (
    echo [%DATE% %TIME%] ETL completado exitosamente. >> logs\scheduler.log
) else (
    echo [%DATE% %TIME%] ERROR: ETL finalizo con codigo %ERRORLEVEL% >> logs\scheduler.log
)
