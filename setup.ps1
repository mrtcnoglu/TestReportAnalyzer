[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function Test-Executable {
    param(
        [Parameter(Mandatory)]
        [string]$Name
    )

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Gerekli komut bulunamadı: $Name"
    }
}

Write-Host "==> Sistem gereksinimleri doğrulanıyor..."
Test-Executable -Name "python"
Test-Executable -Name "node"
Test-Executable -Name "npm"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $root "backend"
$frontendDir = Join-Path $root "frontend"
$uploadsDir = Join-Path $backendDir "uploads"
$venvPath = Join-Path $backendDir "venv"
$venvPython = Join-Path $venvPath "Scripts/python.exe"

Write-Host "==> Python sanal ortamı hazırlanıyor..."
if (-not (Test-Path $venvPath)) {
    & python -m venv $venvPath
}

Write-Host "==> Backend bağımlılıkları yükleniyor..."
& $venvPython -m pip install --upgrade pip | Out-Null
& $venvPython -m pip install -r (Join-Path $backendDir "requirements.txt")

Write-Host "==> Veritabanı şeması uygulanıyor..."
Push-Location $backendDir
try {
    & $venvPython -c "from database import init_db; init_db()"
} finally {
    Pop-Location
}

Write-Host "==> Uploads klasörü oluşturuluyor..."
if (-not (Test-Path $uploadsDir)) {
    New-Item -ItemType Directory -Path $uploadsDir | Out-Null
}

Write-Host "==> Frontend bağımlılıkları yükleniyor..."
Push-Location $frontendDir
try {
    & npm install
} finally {
    Pop-Location
}

Write-Host "Kurulum başarıyla tamamlandı."
