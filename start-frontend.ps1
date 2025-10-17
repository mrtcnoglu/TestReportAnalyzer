[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$frontendDir = Join-Path $root "frontend"

Push-Location $frontendDir
try {
    Write-Host "React arayüzü http://127.0.0.1:3000 adresinde başlatılıyor..."
    & npm start
} finally {
    Pop-Location
}
