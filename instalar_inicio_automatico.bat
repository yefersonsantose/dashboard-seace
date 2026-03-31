@echo off
echo.
echo  Instalando inicio automatico del Dashboard SEACE...
echo.

set SCRIPT="%~dp0iniciar_dashboard.bat"
set STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set SHORTCUT=%STARTUP%\Dashboard SEACE.bat

REM Copiar el script al folder de inicio de Windows
copy /y %SCRIPT% "%SHORTCUT%" > nul

if %ERRORLEVEL% == 0 (
    echo  ╔══════════════════════════════════════════════════════╗
    echo  ║  LISTO: El Dashboard se iniciara automaticamente     ║
    echo  ║  cada vez que enciendas tu PC.                       ║
    echo  ║                                                      ║
    echo  ║  Para desinstalarlo ejecuta:                         ║
    echo  ║  desinstalar_inicio_automatico.bat                   ║
    echo  ╚══════════════════════════════════════════════════════╝
) else (
    echo  ERROR: No se pudo instalar. Intenta ejecutar como Administrador.
)

echo.
pause
