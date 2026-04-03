@echo off
cd /d "%~dp0"
python notificar_email.py >> "..\logs\alertas_email.log" 2>&1
