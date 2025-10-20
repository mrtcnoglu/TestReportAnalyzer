# -*- coding: utf-8 -*-
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "   AI PROVIDER DURUM KONTROLÜ" -ForegroundColor Yellow
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "" -ForegroundColor White

if (Test-Path "backend\.env") {
    Write-Host "✓ .env dosyası bulundu" -ForegroundColor Green
    Write-Host "" -ForegroundColor White
    
    $envContent = Get-Content "backend\.env" -Raw
    
    # Provider kontrolü
    if ($envContent -match "AI_PROVIDER=(.+)") {
        $provider = $matches[1].Trim()
        Write-Host "AI Provider: " -NoNewline
        Write-Host "$provider" -ForegroundColor Cyan
    }
    
    Write-Host "" -ForegroundColor White
    
    # Claude key kontrolü
    if ($envContent -match "ANTHROPIC_API_KEY=(.+)") {
        $key = $matches[1].Trim()
        if ($key -ne "" -and $key -ne "your_claude_api_key_here") {
            Write-Host "✓ Claude API Key: Ayarlanmış" -ForegroundColor Green
        } else {
            Write-Host "✗ Claude API Key: Ayarlanmamış" -ForegroundColor Red
        }
    }
    
    # OpenAI key kontrolü
    if ($envContent -match "OPENAI_API_KEY=(.+)") {
        $key = $matches[1].Trim()
        if ($key -ne "" -and $key -ne "your_openai_api_key_here") {
            Write-Host "✓ OpenAI API Key: Ayarlanmış" -ForegroundColor Green
        } else {
            Write-Host "✗ OpenAI API Key: Ayarlanmamış" -ForegroundColor Red
        }
    }
    
    Write-Host "" -ForegroundColor White
    Write-Host "Key'leri düzenlemek için:" -ForegroundColor Yellow
    Write-Host "notepad backend\.env" -ForegroundColor Cyan
    
} else {
    Write-Host "✗ .env dosyası bulunamadı!" -ForegroundColor Red
    Write-Host "" -ForegroundColor White
    Write-Host "Lütfen önce kurulum yapın:" -ForegroundColor Yellow
    Write-Host ".\setup.ps1" -ForegroundColor Cyan
}

Write-Host "" -ForegroundColor White
Write-Host "============================================" -ForegroundColor Cyan
