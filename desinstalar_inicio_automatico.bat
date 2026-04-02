@echo off
title Desinstalar Inicio Automatico - SEACE Dashboard
color 0C
echo.
echo  Desinstalando inicio automatico del Dashboard SEACE...
echo.

set TAREA=DashboardSEACE

REM Eliminar tarea programada
schtasks /delete /tn "%TAREA%" /f > nul 2>&1

REM Eliminar acceso directo del Startup antiguo (por si acaso)
set SHORTCUT=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Dashboard SEACE.bat
if exist "%SHORTCUT%" del /f "%SHORTCUT%"

echo  El Dashboard SEACE ya NO se iniciara automaticamente.
echo.
echo  Presiona cualquier tecla para cerrar...
pause > nul
