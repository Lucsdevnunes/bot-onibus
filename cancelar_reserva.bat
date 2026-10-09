@echo off
title Cancelar Reserva por Nome - Maurilandia
chcp 65001 > nul
cls
cd /d "%~dp0"
python cancelar_reserva.py
pause
