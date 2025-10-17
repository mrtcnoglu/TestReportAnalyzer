[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$frontendDir = Join-Path $root "frontend"

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
        NpmFoundViaCommand = [bool]$npmCommand
    }
}

$nodeTooling = Resolve-NodeTooling
$npmExecutable = $nodeTooling.NpmPath

if (-not $npmExecutable) {
    throw "npm komutu bulunamadı. Lütfen Node.js ve npm'in kurulu olduğundan emin olun ve gerekirse setup.ps1 betiğini yeniden çalıştırın."
}

if (-not $nodeTooling.NpmFoundViaCommand) {
    Write-Host "npm PATH değişkeninde bulunamadı; varsayılan Node.js kurulum klasöründen kullanılacak. PATH'in güncellenmesi için yeni bir terminal açmanız gerekebilir." -ForegroundColor Yellow
}

Push-Location $frontendDir
try {
    Write-Host "React arayüzü http://127.0.0.1:3000 adresinde başlatılıyor..."
    & $npmExecutable start
} finally {
    Pop-Location
}
