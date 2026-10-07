# Script PowerShell para executar em repetição contínua até dar SUCESSO
$Host.UI.RawUI.WindowTitle = "Modo Looping - Bot de Reserva Universitaria"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "         EXECUTANDO EM LOOPING CONTINUO ATE OBTER SUCESSO" -ForegroundColor Yellow
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

Set-Location -Path $PSScriptRoot

Write-Host "Iniciando tentativas consecutivas..." -ForegroundColor Green
Write-Host "O bot so vai parar quando a reserva der SUCESSO!" -ForegroundColor White
Write-Host "A tela permanecera aberta no final para sua conferencia." -ForegroundColor White
Write-Host "Pressione Ctrl+C para encerrar." -ForegroundColor Gray
Write-Host "----------------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host ""

python main.py --loop
