@echo off
title Parar Bot de Reserva
chcp 65001 > nul
cls
echo Encerrando processos do Bot de Reserva e Python...
taskkill /F /IM python.exe /T > nul 2>&1
taskkill /F /IM chromedriver.exe /T > nul 2>&1
taskkill /F /IM msedgedriver.exe /T > nul 2>&1
echo.
echo [OK] Bot e navegadores associados foram encerrados com sucesso!
echo.
pause
