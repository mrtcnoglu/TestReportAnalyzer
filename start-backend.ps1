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
    Write-Host "Flask API http://127.0.0.1:5000 adresinde başlatılıyor..."
    & $venvPython "app.py"
} finally {
    Pop-Location
}
