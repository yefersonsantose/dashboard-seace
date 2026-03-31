@echo off
title Actualizacion SEACE
color 0A
echo ============================================
echo   ACTUALIZACION DE DATOS - DASHBOARD SEACE
echo ============================================
echo.
echo Iniciando descarga desde SEACE (OCDS)...
echo Esto puede tomar varios minutos.
echo.

cd /d "%~dp0etl"

:: Verificar que Python este disponible
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no encontrado. Verifica la instalacion.
    pause
    exit /b 1
)

:: Ejecutar ETL del año actual
python run.py --year %date:~-4%

echo.
if errorlevel 1 (
    color 0C
    echo ERROR: El ETL termino con errores. Revisa los logs en etl\logs\
) else (
    color 0A
    echo LISTO: Datos actualizados correctamente.
)

echo.
echo Presiona cualquier tecla para cerrar...
pause >nul
