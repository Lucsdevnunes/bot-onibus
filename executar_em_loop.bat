@echo off
title Bot de Reserva - Maurilandia (Modo Looping Inteligente)
chcp 65001 > nul
cls
echo ======================================================================
echo          BOT DE RESERVA UNIVERSITARIA - MAURILANDIA/GO
echo                     MODO LOOPING INTELIGENTE
echo ======================================================================
echo.
echo  [REGRAS ATIVAS]
echo  - Data da viagem: SEMPRE o dia seguinte (amanha)
echo  - Onibus: Exclusivo 0542 - Dheimes
echo  - Alocacao: 8 alunos com busca por proximidade
echo  - Refresh continuo: Recarrega ate o site abrir as vagas
echo  - Atualizacao de mapa: Refresh no site apos cada cadastro
echo.
echo  [OCASIOES DE PARADA DO PROGRAMA]
echo  1. Todos os 8 alunos forem marcados com SUCESSO.
echo  2. As vagas do onibus 0542 acabarem (Onibus Lotado).
echo  3. O relogio atingir o horario limite (22:30).
echo.
echo  Pressione Ctrl+C para interromper manualmente a qualquer momento.
echo ----------------------------------------------------------------------
echo.

cd /d "%~dp0"

python main.py --loop

echo.
echo ======================================================================
echo Processamento concluido. A tela do navegador permanecera aberta.
echo ======================================================================
pause
