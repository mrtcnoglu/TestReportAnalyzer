# PDF Test Raporu Debug Talimatları

## Adım 1: PDF İçeriğini Kontrol Et
```powershell
cd backend
.\check-pdf.ps1
```

**Ne görmeli:**
- ✅ TEXT İÇERİK: Okunabilir text var
- ✅ ANAHTAR KELİME ANALİZİ: Pass/Fail kelimeleri bulundu
- ❌ TEXT İÇERİK YOK: PDF grafik/resim içeriyor (desteklenmiyor)

## Adım 2: Sonuçlara Göre Aksiyon

### Senaryo A: "TEXT İÇERİK YOK"
→ PDF'iniz resim tabanlı, OCR gerekiyor  
→ Alternatif: PDF'i text-based olarak yeniden export edin

### Senaryo B: Text var ama "ANAHTAR KELİME: Yok"
→ Test sonuçları farklı kelimelerle yazılmış  
→ `pdf_analyzer.py`'deki PASS_PATTERN ve FAIL_PATTERN'e o kelimeleri ekleyin

### Senaryo C: Kelimeler bulundu ama test sayısı 0
→ Format tanınmıyor  
→ Test output'u buraya gönderin, pattern'leri güncelleyelim

## Adım 3: Custom Pattern Ekleme

`backend/pdf_analyzer.py` dosyasını açın:
```python
# Mevcut pattern'lerin sonuna ekleyin:
PASS_PATTERN = r'(PASS|...|ÖzelKelime)'
FAIL_PATTERN = r'(FAIL|...|BaşkaKelime)'
```

Kaydedin ve uygulamayı yeniden başlatın.

## Adım 4: Destek

Hala çözülmediyse:
1. check-pdf.ps1 çıktısını kaydedin
2. Örnek PDF'i paylaşın (hassas bilgi varsa maskeleyin)
3. GitHub Issue açın
