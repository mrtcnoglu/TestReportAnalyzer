[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function Test-Executable {
    param(
        [Parameter(Mandatory)]
        [string]$Name,

        [switch]$Optional
    )

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        if ($Optional) {
            Write-Warning "Gerekli komut bulunamadı: $Name. İlgili adım atlanacak."
            return $false
        }

        throw "Gerekli komut bulunamadı: $Name"
    }

    return $true
}

function Resolve-NodeTooling {
    [OutputType([pscustomobject])]
    param()

    $nodeCommand = Get-Command node -ErrorAction SilentlyContinue
    $npmCommand = Get-Command npm -ErrorAction SilentlyContinue

    $nodePath = $null
    $npmPath = $null
    $resolvedViaFallback = $false

    if ($nodeCommand) {
        $nodePath = $nodeCommand.Path
        if (-not $nodePath) { $nodePath = $nodeCommand.Source }
    }

    if ($npmCommand) {
        $npmPath = $npmCommand.Path
        if (-not $npmPath) { $npmPath = $npmCommand.Source }
    }

    $candidateDirs = @()
    if ($nodePath) { $candidateDirs += (Split-Path $nodePath -Parent) }
    if ($npmPath) { $candidateDirs += (Split-Path $npmPath -Parent) }

    $programFiles = [System.Environment]::GetEnvironmentVariable("ProgramFiles")
    if ($programFiles) { $candidateDirs += (Join-Path $programFiles "nodejs") }

    $programFilesX86 = [System.Environment]::GetEnvironmentVariable("ProgramFiles(x86)")
    if ($programFilesX86) { $candidateDirs += (Join-Path $programFilesX86 "nodejs") }

    $localAppData = [System.Environment]::GetEnvironmentVariable("LocalAppData")
    if ($localAppData) { $candidateDirs += (Join-Path $localAppData "Programs\nodejs") }

    $appData = [System.Environment]::GetEnvironmentVariable("AppData")
    if ($appData) { $candidateDirs += (Join-Path $appData "npm") }

    foreach ($dir in ($candidateDirs | Where-Object { $_ } | Select-Object -Unique)) {
        if (-not (Test-Path $dir)) { continue }

        if (-not $nodePath) {
            foreach ($nodeName in @("node.exe", "node.cmd", "node")) {
                $candidate = Join-Path $dir $nodeName
                if (Test-Path $candidate) {
                    $nodePath = $candidate
                    $resolvedViaFallback = $true
                    break
                }
            }
        }

        if (-not $npmPath) {
            foreach ($npmName in @("npm.cmd", "npm.ps1", "npm.exe", "npm")) {
                $candidate = Join-Path $dir $npmName
                if (Test-Path $candidate) {
                    $npmPath = $candidate
                    $resolvedViaFallback = $true
                    break
                }
            }
        }

        if ($nodePath -and $npmPath) { break }
    }

    return [pscustomobject]@{
        NodePath = $nodePath
        NpmPath = $npmPath
        ResolvedViaFallback = $resolvedViaFallback
        NodeFoundViaCommand = [bool]$nodeCommand
        NpmFoundViaCommand = [bool]$npmCommand
    }
}

Write-Host "==> Sistem gereksinimleri doğrulanıyor..."
$pythonAvailable = Test-Executable -Name "python"
$nodeTooling = Resolve-NodeTooling
$nodeAvailable = [bool]$nodeTooling.NodePath
$npmAvailable = [bool]$nodeTooling.NpmPath
$npmExecutable = $nodeTooling.NpmPath

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

if ($nodeAvailable -and $npmAvailable) {
    if (-not $nodeTooling.NpmFoundViaCommand) {
        Write-Host "npm PATH değişkeninde bulunamadı; varsayılan Node.js kurulum klasöründen kullanılacak. PATH'in güncellenmesi için yeni bir terminal açmanız gerekebilir." -ForegroundColor Yellow
    }

    Write-Host "==> Frontend bağımlılıkları yükleniyor..."
    Push-Location $frontendDir
    try {
        & $npmExecutable install
    } finally {
        Pop-Location
    }

    Write-Host "Kurulum başarıyla tamamlandı."
} else {
    Write-Warning "Node.js veya npm bulunamadığı için frontend bağımlılıklarının kurulumu atlandı."
    Write-Warning "Node.js 18+ ve npm kurulduktan sonra frontend klasöründe 'npm install' komutunu manuel olarak çalıştırabilirsiniz."

    if (-not $nodeTooling.NodeFoundViaCommand -or -not $nodeTooling.NpmFoundViaCommand) {
        Write-Warning "Node.js veya npm'i yeni yüklediyseniz PATH değişikliklerinin uygulanması için PowerShell oturumunu yeniden başlatmayı deneyebilirsiniz."
    }

    Write-Host "Backend kurulum adımları başarıyla tamamlandı."
}
