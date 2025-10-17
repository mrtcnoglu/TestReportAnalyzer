[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$frontendDir = Join-Path $root "frontend"

$npmCommand = Get-Command npm -ErrorAction SilentlyContinue
if (-not $npmCommand) {
    throw "npm komutu bulunamadı. Lütfen Node.js ve npm'in kurulu olduğundan emin olun ve gerekirse setup.ps1 betiğini yeniden çalıştırın."
}

$npmExecutable = $npmCommand.Path
if (-not $npmExecutable) {
    $npmExecutable = $npmCommand.Source
}

Push-Location $frontendDir
try {
    Write-Host "React arayüzü http://127.0.0.1:3000 adresinde başlatılıyor..."
    & $npmExecutable start
} finally {
    Pop-Location
}
