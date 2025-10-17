[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $root "backend"
$venvPython = Join-Path $backendDir "venv/Scripts/python.exe"
if (-not (Test-Path $venvPython)) {
    throw "Sanal ortam bulunamadı. Lütfen önce setup.ps1 betiğini çalıştırın."
}

Push-Location $backendDir
try {
    $hostAddress = $env:FLASK_RUN_HOST
    if (-not $hostAddress) { $hostAddress = $env:FLASK_HOST }
    if (-not $hostAddress) { $hostAddress = $env:HOST }
    if (-not $hostAddress) { $hostAddress = '0.0.0.0' }

    $portNumber = $env:FLASK_RUN_PORT
    if (-not $portNumber) { $portNumber = $env:FLASK_PORT }
    if (-not $portNumber) { $portNumber = $env:PORT }
    if (-not $portNumber) { $portNumber = '5000' }

    Write-Host "Flask API http://$hostAddress:$portNumber adresinde başlatılıyor..."
    & $venvPython "app.py"
} finally {
    Pop-Location
}
