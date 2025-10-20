[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $root 'backend'
$venvCandidates = @(
    (Join-Path $backendDir 'venv\Scripts\python.exe'),
    (Join-Path $backendDir '.venv\Scripts\python.exe')
)
$venvPython = $venvCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1

function Resolve-PythonLauncher {
    foreach ($name in 'py', 'python', 'python3') {
        $command = Get-Command $name -ErrorAction SilentlyContinue
        if ($command) {
            if ($command.Source) { return $command.Source }
            if ($command.Path)   { return $command.Path }
        }
    }

    throw 'Python yürütücüsü bulunamadı. Lütfen Python kurulumunu doğrulayın.'
}

if (-not $venvPython) {
    $venvTarget = Join-Path $backendDir 'venv'
    Write-Host "Python sanal ortamı oluşturuluyor: $venvTarget"
    $pythonLauncher = Resolve-PythonLauncher
    & $pythonLauncher -m venv $venvTarget
    $venvPython = $venvCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
    if (-not $venvPython) {
        throw "Sanal ortam oluşturulamadı: $venvTarget"
    }
}

$requirements = Join-Path $backendDir 'requirements.txt'
if (Test-Path $requirements) {
    Write-Host 'Backend bağımlılıkları yükleniyor...'
    & $venvPython -m pip install --upgrade pip
    & $venvPython -m pip install -r $requirements
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
