@echo off
title Actualizador Automatico de Programas - Windows
chcp 65001 >nul
cd /d "%~dp0"
echo =================================================================
echo   Iniciando Actualizador Automatico de Programas (Windows)
echo =================================================================
python app.py
pause
