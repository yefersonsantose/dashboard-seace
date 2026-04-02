@echo off
title Instalar Inicio Automatico - SEACE Dashboard
color 0B
echo.
echo  Instalando Dashboard SEACE como tarea automatica de Windows...
echo.

set RUTA=%~dp0
set VBS="%RUTA%iniciar_silencioso.vbs"
set TAREA=DashboardSEACE

REM Eliminar tarea anterior si existe
schtasks /delete /tn "%TAREA%" /f > nul 2>&1

REM Crear tarea programada que se ejecuta al iniciar sesion (sin ventana)
schtasks /create /tn "%TAREA%" /tr "wscript.exe %VBS%" /sc ONLOGON /rl HIGHEST /f

if %ERRORLEVEL% == 0 (
    color 0A
    echo.
    echo  ============================================================
    echo   LISTO: El Dashboard SEACE se iniciara automaticamente
    echo   cada vez que enciendas tu PC (sin necesitar Claude).
    echo.
    echo   Para iniciarlo ahora, haz doble clic en:
    echo     iniciar_silencioso.vbs
    echo.
    echo   Para desinstalarlo ejecuta:
    echo     desinstalar_inicio_automatico.bat
    echo  ============================================================
    echo.
) else (
    color 0C
    echo  ERROR: No se pudo instalar.
    echo  Intenta hacer clic derecho y "Ejecutar como Administrador".
)

echo  Presiona cualquier tecla para cerrar...
pause > nul
