# -*- coding: utf-8 -*-
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "   PDF İÇERİK ANALİZ ARACI" -ForegroundColor Yellow
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "" -ForegroundColor White

if (Test-Path "venv\Scripts\Activate.ps1") {
    .\venv\Scripts\Activate.ps1

    if ($args.Count -gt 0) {
        $pdfPath = $args[0]
        Write-Host "PDF analiz ediliyor: $pdfPath" -ForegroundColor Yellow
        python test_pdf_debug.py $pdfPath
    } else {
        Write-Host "Son yüklenen PDF analiz ediliyor..." -ForegroundColor Yellow
        python test_pdf_debug.py
    }
} else {
    Write-Host "HATA: Virtual environment bulunamadı!" -ForegroundColor Red
    Write-Host "Lütfen önce .\setup.ps1 çalıştırın" -ForegroundColor Yellow
}

Write-Host "" -ForegroundColor White
Write-Host "============================================" -ForegroundColor Cyan
