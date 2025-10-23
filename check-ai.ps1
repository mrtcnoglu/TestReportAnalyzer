# Requires: PowerShell 5+
# Basic health check for the AI integration.
param(
  [string]$BaseUrl = "http://127.0.0.1:5000"
)

try {
  $url = "$BaseUrl/api/health/ai"
  Write-Host "GET $url"
  $response = Invoke-RestMethod -Uri $url -Method GET -TimeoutSec 10
  $response | ConvertTo-Json -Depth 5
} catch {
  Write-Error $_.Exception.Message
  exit 1
}
