@echo off
title Enviar Bot para o GitHub
chcp 65001 > nul
cls
echo ======================================================================
echo                  ENVIANDO BOT PARA O GITHUB ACTIONS
echo ======================================================================
echo.

cd /d "C:\Users\Lucas Nunes\Desktop\bot_reserva"

echo Enviando arquivos para o repositorio do GitHub...
echo (Se abrir uma janela do navegador, clique em 'Sign in with browser' para autorizar)
echo.

git remote set-url origin https://github.com/Lucsdevnunes/bot-onibus.git
git push -u origin main

echo.
echo ======================================================================
echo Processo concluido! Verifique a aba 'Actions' no seu GitHub:
echo https://github.com/Lucsdevnunes/bot-onibus/actions
echo ======================================================================
pause
