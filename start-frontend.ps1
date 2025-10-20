param([string]$UiDir)

$ErrorActionPreference = 'Stop'
Write-Host 'React arayüzü http://127.0.0.1:3000 adresinde başlatılıyor...'

# 1) NPM yürütücüsünü bul: önce npm.cmd, yoksa npm (Windows PowerShell uyumlu)
$npmCmdInfo = Get-Command npm.cmd -ErrorAction SilentlyContinue
if ($npmCmdInfo) {
  $npm = $npmCmdInfo.Source
} else {
  $npmInfo = Get-Command npm -ErrorAction Stop
  $npm = $npmInfo.Source

  # Windows ortamında, `npm` aslında `npm.cmd`'i işaret edebilir; varsa onu kullan.
  $possibleCmd = Join-Path (Split-Path $npm) 'npm.cmd'
  if (Test-Path $possibleCmd) {
    $npm = $possibleCmd
  }
}

# 2) UI dizini: varsayılan .\frontend, yoksa betik kökü
$root = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
if (-not $UiDir) {
  $UiDir = if (Test-Path (Join-Path $root 'frontend\package.json')) { Join-Path $root 'frontend' } else { $root }
}
Set-Location $UiDir

# 3) Bağımlılıklar
if (Test-Path 'package-lock.json') {
  & $npm ci
} else {
  & $npm install
}

# 4) package.json script seçimi
$pkg = Get-Content -Raw -Path 'package.json' | ConvertFrom-Json
$hasStart = $pkg.scripts.PSObject.Properties.Name -contains 'start'
$hasDev   = $pkg.scripts.PSObject.Properties.Name -contains 'dev'

if     ($hasStart) { & $npm run start }
elseif ($hasDev)   { & $npm run dev }
else               { throw "package.json içinde 'start' veya 'dev' script'i yok." }
