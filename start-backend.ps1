[CmdletBinding()]
param()

# --- VENV OTOMASYONU (Windows) ---
$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoRoot

# Olası sanal ortam klasörleri
$venvCandidates = @('venv', '.venv')
$venvPath = $null
foreach ($c in $venvCandidates) {
    if (Test-Path (Join-Path $repoRoot $c)) { $venvPath = (Join-Path $repoRoot $c); break }
}

# Yoksa oluştur
if (-not $venvPath) {
    Write-Host "Sanal ortam bulunamadı. 'venv' oluşturuluyor..."
    & py -m venv (Join-Path $repoRoot 'venv')
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path (Join-Path $repoRoot 'venv'))) {
        throw "Sanal ortam oluşturulamadı. Sisteminizde 'py' yoksa Python 3 kurun."
    }
    $venvPath = (Join-Path $repoRoot 'venv')
}

# Aktif et
$activate = Join-Path $venvPath 'Scripts\Activate.ps1'
if (-not (Test-Path $activate)) { throw "Venv bulunuyor fakat Activate.ps1 yok: $activate" }
. $activate

# Gerekirse bağımlılıkları kur
if (Test-Path (Join-Path $repoRoot 'requirements.txt')) {
    pip install -r (Join-Path $repoRoot 'requirements.txt')
    if ($LASTEXITCODE -ne 0) { throw "pip install -r requirements.txt başarısız." }
}
# --- VENV OTOMASYONU SONU ---

$backendRequirements = Join-Path $repoRoot 'backend/requirements.txt'
if (Test-Path $backendRequirements) {
    pip install -r $backendRequirements
    if ($LASTEXITCODE -ne 0) { throw "pip install -r backend/requirements.txt başarısız." }
}

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$root = $repoRoot
$backendDir = Join-Path $root 'backend'

$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if ($pythonCmd -and $pythonCmd.Source) {
    $venvPython = $pythonCmd.Source
} elseif ($pythonCmd -and $pythonCmd.Path) {
    $venvPython = $pythonCmd.Path
} else {
    throw 'Aktif sanal ortamda python yürütücüsü bulunamadı.'
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

    Write-Host "Flask API http://${hostAddress}:${portNumber} adresinde başlatılıyor..."
    & $venvPython 'app.py'
}
finally {
    Pop-Location
}
