@echo off
title Instalar Alertas Email SEACE - 6 PM diario
color 0B
echo.
echo  ============================================================
echo   Instalando alerta diaria de convocatorias SEACE por email
echo   Hora de envio: 18:00 (6:00 PM) todos los dias
echo  ============================================================
echo.

set RUTA=%~dp0
set TAREA=AlertasEmailSEACE
set SCRIPT="%RUTA%etl\notificar_email.py"
set LOG="%RUTA%logs\alertas_email.log"

REM Eliminar tarea anterior si existe
schtasks /delete /tn "%TAREA%" /f > nul 2>&1

REM Crear tarea programada diaria a las 18:00
schtasks /create ^
  /tn "%TAREA%" ^
  /tr "cmd /c cd /d \"%RUTA%etl\" && python notificar_email.py >> \"%RUTA%logs\alertas_email.log\" 2>&1" ^
  /sc DAILY ^
  /st 18:00 ^
  /f

if %ERRORLEVEL% == 0 (
    color 0A
    echo.
    echo  [OK] Alerta instalada correctamente.
    echo.
    echo  Se enviara un correo a las 6:00 PM cada dia con las
    echo  convocatorias nuevas que contengan las palabras clave
    echo  configuradas en alertas_config.json
    echo.
    echo  IMPORTANTE: Antes de que funcione debes configurar
    echo  tu contrasena de aplicacion Gmail en el archivo .env
    echo  Ver instrucciones en: INSTRUCCIONES_EMAIL.txt
    echo.
    echo  Para probar ahora mismo ejecuta:
    echo    cd etl
    echo    python notificar_email.py --test
    echo.
) else (
    color 0C
    echo.
    echo  [ERROR] No se pudo instalar la tarea.
    echo  Intenta ejecutar como Administrador.
)

echo  Presiona cualquier tecla para cerrar...
pause > nul
