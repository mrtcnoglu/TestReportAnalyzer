# TestReportAnalyzer

## Proje Tanımı
TestReportAnalyzer, otomatik test raporlarını analiz ederek başarısız testlerin kök nedenlerini ve önerilen düzeltmeleri hızlıca ortaya çıkaran bir masaüstü/web hibrit uygulamasıdır. Uygulama PDF formatındaki test raporlarını alır, metin içeriklerini çözümler ve sonuçları kullanıcı dostu bir arayüzde sunar. Böylece QA ekipleri, başarısızlıkları incelemek için harcadıkları zamanı azaltır ve aksiyon alınması gereken alanları önceliklendirir.

## Özellikler
- PDF test raporlarının yüklenmesi ve metin tabanlı analiz edilmesi.
- PASS/FAIL sonuçlarının otomatik sayımı ve rapor özeti oluşturma.
- Her başarısız test için hata mesajı, olası neden ve önerilen çözümün çıkarılması.
- Raporların listelenmesi, sıralanması ve filtrelenmesi.
- Detay sayfasında test bazlı inceleme ve başarısız testlerin ayrı listelenmesi.
- Raporların sistemden silinebilmesi.

## Teknoloji Stack
- **Backend:** Python 3, Flask, SQLite, pdfplumber / PyPDF2, python-dateutil
- **Frontend:** React, React Router, Axios, React Scripts
- **Komut Dosyaları:** Windows PowerShell

## Gereksinimler
- Windows 10/11 üzerinde PowerShell 5.1 veya PowerShell 7+
- Python 3.11+
- Node.js 18+ ve npm
- PDF analizinde kullanılan kütüphaneler için temel C++ yapı araçları (gerekmesi halinde)

## Kurulum
Tüm adımlar PowerShell içerisinde uygulanmalıdır.

> **PowerShell Execution Policy Hatası mı Alıyorsunuz?**
>
> Bazı Windows kurulumlarında varsayılan Execution Policy ayarı, depo içindeki PowerShell betiklerinin (ör. `setup.ps1`)
> çalıştırılmasını engelleyebilir ve `running scripts is disabled on this system` hatası dönebilir. Bu durumda komutları yalnızca
> mevcut oturum için yetkilendirmek amacıyla aşağıdaki komutu çalıştırabilirsiniz:
>
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
> ```
>
> Ardından kurulum adımlarına kaldığınız yerden devam edebilirsiniz. Kalıcı bir değişiklik yapılmadığından bilgisayarınızın
> genel güvenlik ayarları etkilenmez. Alternatif olarak betiği şu şekilde de çalıştırabilirsiniz:
>
> ```powershell
> powershell -ExecutionPolicy Bypass -File .\setup.ps1
> ```
>
> Yukarıdaki yöntemlerden yalnızca biri yeterlidir; ikisini birden çalıştırmanıza gerek yoktur.

```powershell
# Depoyu klonlayın
git clone https://github.com/<kullanici-adiniz>/TestReportAnalyzer.git
cd TestReportAnalyzer

# Kurulum komut dosyasını çalıştırın
.\setup.ps1
```

> **Not:** PowerShell'de aynı klasördeki komut dosyalarını çalıştırmak için `.\` ön ekini kullanmanız önerilir. Bu sözdizimi 
> özellikle Windows PowerShell 5.1 gibi eski sürümlerde `./` kullanımının komutun bulunamamasına yol açmasını engeller.

`setup.ps1` betiği aşağıdaki işlemleri yapar:
1. Python ve Node.js kurulumlarını doğrular.
2. Backend için sanal ortam (`backend/venv`) oluşturur ve `requirements.txt` bağımlılıklarını yükler.
3. SQLite veritabanını başlatmak için `init_db()` fonksiyonunu çalıştırır.
4. Frontend bağımlılıklarını (`frontend` klasöründe) yükler.
5. PDF yüklemeleri için `backend/uploads/` klasörünü oluşturur.

## Çalıştırma
Uygulamayı başlatmak için kök dizinde aşağıdaki PowerShell komutunu çalıştırın:

```powershell
.\start-app.ps1
```

Betik, backend'i (Flask sunucusu) 127.0.0.1:5000 üzerinde, frontend'i ise 127.0.0.1:3000 üzerinde başlatır. Her iki hizmet yeni PowerShell pencerelerinde açılır ve durumu terminale yazdırılır.

Uygulamayı durdurmak için:

```powershell
.\stop-app.ps1
```

Alternatif olarak bileşenleri ayrı ayrı yönetmek isterseniz:

```powershell
.\start-backend.ps1   # Flask API'yi başlatır
.\start-frontend.ps1  # React uygulamasını başlatır
```

## Kullanım
1. Frontend arayüzünde "PDF Yükle" formunu kullanarak test raporunu yükleyin.
2. Yükleme tamamlandığında rapor listesine yeni bir kayıt eklenir.
3. Listeden bir rapora tıklayarak özet, PASS/FAIL sayıları ve başarısız test detaylarını görüntüleyin.
4. Başarısız testler için önerilen düzeltmeleri inceleyin veya raporu sistemden kaldırın.

## API Endpoints
| Metot | Endpoint | Açıklama |
|-------|----------|----------|
| `POST` | `/api/upload` | PDF raporunu yükler, analiz eder ve veritabanına kaydeder. |
| `GET` | `/api/reports` | Mevcut tüm raporları sıralama seçenekleriyle döndürür. |
| `GET` | `/api/reports/<id>` | Belirli bir raporun özet bilgilerini getirir. |
| `GET` | `/api/reports/<id>/failures` | Belirli raporun başarısız testlerini listeler. |
| `DELETE` | `/api/reports/<id>` | Raporu veritabanından siler ve ilişkili kayıtları temizler. |

Tüm yanıtlar JSON formatındadır ve CORS varsayılan olarak etkinleştirilmiştir.

## Proje Yapısı
```
TestReportAnalyzer/
├── backend/
│   ├── app.py
│   ├── database.py
│   ├── pdf_analyzer.py
│   ├── requirements.txt
│   └── models/
│       └── schema.sql
├── frontend/
│   ├── package.json
│   └── src/
│       ├── api.js
│       ├── App.js
│       ├── index.js
│       ├── styles/
│       │   └── App.css
│       └── components/
│           ├── Dashboard.js
│           ├── ReportDetail.js
│           ├── TestList.js
│           └── UploadForm.js
├── setup.ps1
├── start-app.ps1
├── start-backend.ps1
├── start-frontend.ps1
├── stop-app.ps1
└── test-samples/
    └── test_report_sample.pdf
```

## Lisans
Bu proje [MIT Lisansı](LICENSE) ile lisanslanmıştır.
