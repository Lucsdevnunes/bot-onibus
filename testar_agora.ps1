# Script PowerShell para teste imediato da reserva
$Host.UI.RawUI.WindowTitle = "Teste Imediato - Bot de Reserva Universitaria"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "            TESTE IMEDIATO DA RESERVA (DIA DE AMANHA)" -ForegroundColor Yellow
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

Set-Location -Path $PSScriptRoot

Write-Host "Executando automacao agora..." -ForegroundColor Green
Write-Host ""

python main.py --agora

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "Teste finalizado. Verifique os logs em logs/bot.log" -ForegroundColor White
Write-Host "======================================================================" -ForegroundColor Cyan
Read-Host "Pressione Enter para fechar"
