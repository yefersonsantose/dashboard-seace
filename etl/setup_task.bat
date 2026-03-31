@echo off
REM ============================================================
REM  Registra la tarea diaria en Windows Task Scheduler.
REM  Ejecutar UNA VEZ como Administrador.
REM
REM  La tarea se ejecuta todos los dias a las 06:00 AM.
REM  Para cambiar la hora edita el parametro /ST HH:MM
REM ============================================================

set TASK_NAME=SEACE_ETL_Diario
set SCRIPT_PATH=%~dp0run_daily.bat
set LOG_DIR=%~dp0logs

REM Crear directorio de logs si no existe
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM Eliminar tarea anterior si existe
schtasks /delete /tn "%TASK_NAME%" /f 2>nul

REM Crear nueva tarea diaria a las 06:00 AM
schtasks /create ^
  /tn "%TASK_NAME%" ^
  /tr "\"%SCRIPT_PATH%\"" ^
  /sc DAILY ^
  /st 06:00 ^
  /ru "%USERNAME%" ^
  /rl HIGHEST ^
  /f

if %ERRORLEVEL% == 0 (
    echo.
    echo Tarea programada creada exitosamente:
    echo   Nombre : %TASK_NAME%
    echo   Script : %SCRIPT_PATH%
    echo   Horario: Todos los dias a las 06:00 AM
    echo.
    echo Para verificar: schtasks /query /tn "%TASK_NAME%"
    echo Para ejecutar ahora: schtasks /run /tn "%TASK_NAME%"
    echo Para eliminar: schtasks /delete /tn "%TASK_NAME%"
) else (
    echo ERROR al crear la tarea. Ejecuta este script como Administrador.
)

pause
