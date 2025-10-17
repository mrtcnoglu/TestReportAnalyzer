[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function Stop-ProcessSafe {
    param(
        [Parameter(Mandatory)]
        [string]$Name
    )

    $processes = Get-Process -Name $Name -ErrorAction SilentlyContinue
    if ($processes) {
        $processes | Stop-Process -Force
    }
}

Write-Host "==> Python ve Node.js süreçleri sonlandırılıyor..."
Stop-ProcessSafe -Name "python"
Stop-ProcessSafe -Name "pythonw"
Stop-ProcessSafe -Name "node"

Write-Host "Tüm süreçler sonlandırıldı."
