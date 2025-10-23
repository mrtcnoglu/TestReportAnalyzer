# Requires: PowerShell 5+
# Basic health check for the AI integration.
param(
  [string]$BaseUrl = "http://127.0.0.1:5000"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function Invoke-HealthCheckHttp {
  param(
    [string]$Url
  )

  Write-Host "GET $Url"
  return Invoke-RestMethod -Uri $Url -Method GET -TimeoutSec 10
}

function Invoke-HealthCheckLocal {
  param(
    [string]$RepoRoot
  )

  $pythonCmd = Get-Command py -ErrorAction SilentlyContinue
  if (-not $pythonCmd) {
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
  }

  if (-not $pythonCmd) {
    throw 'Python yürütücüsü bulunamadı. Lütfen Python 3 kurulu olduğundan emin olun.'
  }

  $pythonExe = if ($pythonCmd.Source) { $pythonCmd.Source } else { $pythonCmd.Path }
  if (-not $pythonExe) {
    throw 'Python yürütücüsünün yolu belirlenemedi.'
  }

  $scriptContent = @'
import json
import sys

try:
    from backend.app import create_app
except ModuleNotFoundError as exc:
    sys.stderr.write(f"Backend uygulaması içe aktarılamadı: {exc}\n")
    sys.exit(1)

app = create_app()
with app.test_client() as client:
    response = client.get('/api/health/ai')
    if response.status_code >= 400:
        sys.stderr.write(
            f"Sağlık denetimi {response.status_code} döndürdü: {response.get_data(as_text=True)}\n"
        )
        sys.exit(1)

    data = response.get_json()
    if data is None:
        sys.stderr.write('Sağlık denetimi JSON yanıtı döndürmedi.\n')
        sys.exit(1)

    json.dump(data, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write('\n')
'@

  $tempFile = New-TemporaryFile
  try {
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($tempFile.FullName, $scriptContent, $utf8NoBom)

    $originalPythonPath = $env:PYTHONPATH
    try {
      if ([string]::IsNullOrWhiteSpace($originalPythonPath)) {
        $env:PYTHONPATH = $RepoRoot
      } else {
        $env:PYTHONPATH = "${RepoRoot}$([IO.Path]::PathSeparator)$originalPythonPath"
      }

      Push-Location $RepoRoot
      try {
        & $pythonExe $tempFile.FullName
        if ($LASTEXITCODE -ne 0) {
          throw "Yerel Flask sağlık kontrolü başarısız oldu (exit code: $LASTEXITCODE)."
        }
      }
      finally {
        Pop-Location
      }
    }
    finally {
      $env:PYTHONPATH = $originalPythonPath
      Remove-Item -LiteralPath $tempFile.FullName -ErrorAction SilentlyContinue
    }
  }

$url = "$BaseUrl/api/health/ai"

try {
  $response = Invoke-HealthCheckHttp -Url $url
  $response | ConvertTo-Json -Depth 5
} catch {
  Write-Warning "HTTP isteği başarısız oldu: $($_.Exception.Message)"
  Write-Host "Yerel Flask test istemcisi ile sağlık denetimi deneniyor..."

  $repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
  Invoke-HealthCheckLocal -RepoRoot $repoRoot
}
