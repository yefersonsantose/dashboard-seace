@echo off
set SHORTCUT=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Dashboard SEACE.bat

if exist "%SHORTCUT%" (
    del /f "%SHORTCUT%"
    echo  Inicio automatico eliminado correctamente.
) else (
    echo  El inicio automatico no estaba instalado.
)
timeout /t 2 /nobreak > nul
