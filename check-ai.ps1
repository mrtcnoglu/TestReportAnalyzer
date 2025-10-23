# check-ai.ps1
# Amaç: Backend AI sağlık bilgisini /api/health/ai'den alıp JSON yazdırmak.
# Windows PowerShell 5.1 uyumlu. UTF-8 (BOM'suz) ve CRLF ile kaydedin.

[CmdletBinding()]
param(
    [string]$BaseUrl = "http://127.0.0.1:5000"  # Gerekirse değiştir
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

function Invoke-HealthCheckLocal {
    param([Parameter(Mandatory=$true)][string]$Url)

    try {
        $resp = Invoke-RestMethod -Uri $Url -Method GET
        if ($null -eq $resp) { throw "Boş yanıt alındı." }
        return $resp
    }
    catch {
        $msg = $_.Exception.Message
        $detail = $null
        try {
            $webEx = $_.Exception
            if ($webEx.Response -and $webEx.Response.GetResponseStream) {
                $reader = New-Object System.IO.StreamReader($webEx.Response.GetResponseStream())
                $detail = $reader.ReadToEnd()
            }
        } catch {}
        return [pscustomobject]@{
            ok     = $false
            error  = $msg
            detail = $detail
            url    = $Url
        }
    }
}

function Write-Json {
    param([Parameter(Mandatory=$true)]$Object)
    $Object | ConvertTo-Json -Depth 8
}

try {
    # TLS 1.2 zorla (bazı kurumsal ağlarda gerekli olabilir)
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12
} catch {}

$healthUrl = ($BaseUrl.TrimEnd('/')) + "/api/health/ai"
Write-Host "GET $healthUrl"

$result = Invoke-HealthCheckLocal -Url $healthUrl
Write-Json -Object $result
