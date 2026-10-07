@echo off
title Teste Imediato - Bot de Reserva Universitaria
chcp 65001 > nul
cls
echo ======================================================================
echo             TESTE IMEDIATO DA RESERVA (DIA DE AMANHA)
echo ======================================================================
echo.

cd /d "%~dp0"

echo Executando automacao agora...
echo.

python main.py --agora

echo.
echo ======================================================================
echo Teste finalizado. Verifique os logs em logs/bot.log
echo ======================================================================
pause
