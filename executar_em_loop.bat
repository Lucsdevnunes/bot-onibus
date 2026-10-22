@echo off
title Bot de Reserva - Maurilandia (Modo Ultra-Rapido Simultaneo)
chcp 65001 > nul
cls
echo ======================================================================
echo          BOT DE RESERVA UNIVERSITARIA - MAURILANDIA/GO
echo             MODO ULTRA-RAPIDO SIMULTANEO (PARALELO)
echo ======================================================================
echo.
echo  [CONFIGURACAO ATIVA]
echo  - Onibus: Exclusivo 0542 - Dheimes
echo  - Total de Passageiros: 10 Alunos
echo  - Tecnologia: Disparo Paralelo Concorrente (Multithreading)
echo  - Velocidade: Todas as reservas disparadas no mesmo milissegundo!
echo.
echo  ----------------------------------------------------------------------
echo  Escolha como deseja rodar:
echo.
echo   [1] TESTAR AGORA IMEDIATAMENTE (Execucao Manual Direta)
echo   [2] Modo Agendamento / Looping Automatico (Aguardar ate 21:58)
echo  ----------------------------------------------------------------------
echo.
set "opcao=1"
set /p "opcao=Digite a opcao desejada (1 ou 2) [Pressione ENTER para 1]: "

cd /d "%~dp0"

echo.
if "%opcao%"=="2" (
    echo Iniciando em Modo Agendamento Automatico...
    python main.py --loop
) else (
    echo Iniciando Teste Manual Imediato...
    python main.py --agora
)

echo.
echo ======================================================================
echo Processamento concluido. A janela do navegador permanecera aberta!
echo ======================================================================
pause
