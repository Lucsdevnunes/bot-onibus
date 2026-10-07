@echo off
title Bot de Reserva Universitaria - Maurilandia
chcp 65001 > nul
cls
echo ======================================================================
echo       INICIANDO BOT DE RESERVA UNIVERSITARIA (MAURILANDIA/GO)
echo ======================================================================
echo.

cd /d "%~dp0"

echo Verificando Python...
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado no PATH do sistema.
    echo Por favor, instale o Python ou adicione-o as variaveis de ambiente.
    pause
    exit /b 1
)

echo Iniciando o agendador automatico...
echo Fuso horario: America/Sao_Paulo
echo Horarios: Seg a Qui (21:59:59) ^| Domingo (17:59:59)
echo.
echo Pressione Ctrl+C a qualquer momento para encerrar.
echo ----------------------------------------------------------------------
echo.

python main.py

echo.
echo ======================================================================
echo Processo finalizado.
echo ======================================================================
pause
