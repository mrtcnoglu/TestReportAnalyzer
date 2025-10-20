param([string]$UiDir)

$ErrorActionPreference = 'Stop'
Write-Host 'React arayüzü http://127.0.0.1:3000 adresinde başlatılıyor...'

# 1) NPM yürütücüsünü bul: önce npm.cmd, yoksa npm
$npm = (Get-Command npm.cmd -ErrorAction SilentlyContinue)?.Source
if (-not $npm) {
  $npm = (Get-Command npm -ErrorAction Stop).Source
  $npmCmd = Join-Path (Split-Path $npm) 'npm.cmd'
  if (Test-Path $npmCmd) { $npm = $npmCmd }
}

# 2) UI dizini: varsayılan .\frontend, yoksa betik kökü
$root = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
if (-not $UiDir) {
  $UiDir = if (Test-Path (Join-Path $root 'frontend\package.json')) { Join-Path $root 'frontend' } else { $root }
}
Set-Location $UiDir

# 3) Bağımlılıklar: ci dene; hata olursa install
$ranCi = $false
if (Test-Path 'package-lock.json') {
  & $npm ci
  if ($LASTEXITCODE -eq 0) { $ranCi = $true }
}
if (-not $ranCi) {
  & $npm install
  if ($LASTEXITCODE -ne 0) { throw "npm install başarısız." }
}

# 4) package.json script seçimi
$pkg = Get-Content -Raw -Path 'package.json' | ConvertFrom-Json
$hasStart = $pkg.scripts.PSObject.Properties.Name -contains 'start'
$hasDev   = $pkg.scripts.PSObject.Properties.Name -contains 'dev'

if     ($hasStart) { & $npm run start }
elseif ($hasDev)   { & $npm run dev }
else               { throw "package.json içinde 'start' veya 'dev' script'i yok." }
