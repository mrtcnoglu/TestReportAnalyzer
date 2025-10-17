[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendScript = Join-Path $root "start-backend.ps1"
$frontendScript = Join-Path $root "start-frontend.ps1"

Write-Host "==> Backend başlatılıyor..."
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", "`"$backendScript`""
Start-Sleep -Seconds 3

Write-Host "==> Frontend başlatılıyor..."
Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", "`"$frontendScript`""

Write-Host "Backend: http://127.0.0.1:5000"
Write-Host "Frontend: http://127.0.0.1:3000"
