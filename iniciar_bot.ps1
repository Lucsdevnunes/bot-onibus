# Script PowerShell para iniciar o bot de agendamento continuo
$Host.UI.RawUI.WindowTitle = "Bot de Reserva Universitaria - Maurilandia"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "      INICIANDO BOT DE RESERVA UNIVERSITARIA (MAURILANDIA/GO)" -ForegroundColor Yellow
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

Set-Location -Path $PSScriptRoot

Write-Host "Iniciando agendador no fuso America/Sao_Paulo..." -ForegroundColor Green
Write-Host "Horarios: Seg a Qui (21:59:59) | Domingo (17:59:59)" -ForegroundColor White
Write-Host "Pressione Ctrl+C para encerrar." -ForegroundColor Gray
Write-Host "----------------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host ""

python main.py
