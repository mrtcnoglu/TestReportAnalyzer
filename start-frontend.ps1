[CmdletBinding()]
param(
  [string]$UiDir
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host 'React arayüzü http://127.0.0.1:3000 adresinde başlatılıyor...'

try {
  $npmExecutable = (Get-Command npm -ErrorAction Stop | Select-Object -First 1 -ExpandProperty Path)
}
catch {
  throw "npm komutu bulunamadı. Lütfen Node.js ve npm kurulumunu doğrulayın."
}

if (-not $npmExecutable) {
  throw "npm komutu bulunamadı. Lütfen Node.js ve npm kurulumunu doğrulayın."
}

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $UiDir) {
  $frontend = Join-Path $scriptRoot 'frontend'
  $UiDir = if (Test-Path (Join-Path $frontend 'package.json')) { $frontend } else { $scriptRoot }
}

$pkgPath = Join-Path $UiDir 'package.json'
if (-not (Test-Path $pkgPath)) {
  throw "package.json bulunamadı: $pkgPath"
}

Push-Location $UiDir
try {
  if (Test-Path (Join-Path $UiDir 'package-lock.json')) {
    & $npmExecutable ci
  }
  else {
    & $npmExecutable install
  }

  $pkg = Get-Content -Raw -Path $pkgPath | ConvertFrom-Json
  $scriptNames = if ($pkg.scripts) { $pkg.scripts.PSObject.Properties.Name } else { @() }
  $hasStart = $scriptNames -contains 'start'
  $hasDev = $scriptNames -contains 'dev'

  if ($hasStart) {
    & $npmExecutable run start
  }
  elseif ($hasDev) {
    & $npmExecutable run dev
  }
  else {
    throw "package.json içinde 'start' veya 'dev' script'i yok."
  }
}
finally {
  Pop-Location
}
