@echo off
title Modo Looping - Bot de Reserva Universitaria
chcp 65001 > nul
cls
echo ======================================================================
echo          EXECUTANDO EM LOOPING CONTINUO ATE OBTER SUCESSO
echo ======================================================================
echo.

cd /d "%~dp0"

echo Iniciando tentativas consecutivas...
echo O bot so vai parar quando a reserva der SUCESSO!
echo A tela ficara aberta no final para sua conferencia.
echo.
echo Pressione Ctrl+C para interromper a qualquer momento.
echo ----------------------------------------------------------------------
echo.

python main.py --loop

echo.
pause
