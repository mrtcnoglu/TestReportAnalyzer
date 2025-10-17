# Codex Instructions: TestReportAnalyzer PowerShell Project

## Genel Yönergeler
- Tüm dosyalar UTF-8 encoding ile oluşturulmalıdır.
- Windows PowerShell ortamında çalışacak komutlar yazılmalıdır.
- Ek bağımlılıklar (Docker vb.) kullanılmamalıdır.
- Repository kök dizini: `TestReportAnalyzer`.
- Versiyon kontrolü: Git (GitHub uyumlu).

## Görev Akışı

### 1. Repository ve Temel Dosyalar
1. `TestReportAnalyzer` adında yeni bir Git repository oluştur.
2. Aşağıdaki dizin yapısını hazırla:
   ```
   TestReportAnalyzer/
   ├── backend/
   ├── frontend/
   ├── setup.ps1
   ├── start-backend.ps1
   ├── start-frontend.ps1
   ├── start-app.ps1
   ├── stop-app.ps1
   ├── .gitignore
   └── README.md
   ```
3. `.gitignore` dosyasını şu içerikle oluştur:
   ```
   backend/venv/
   backend/__pycache__/
   backend/*.pyc
   backend/database.db
   backend/uploads/*.pdf
   frontend/node_modules/
   frontend/build/
   frontend/.env
   .vscode/
   .idea/
   Thumbs.db
   desktop.ini
   *.log
   ```
4. `README.md` dosyasına proje özeti, gereksinimler, kurulum/çalıştırma komutları, API özetleri ve proje yapısını ekle (detaylar için bkz. Görev 28).

### 2. Backend (Python + Flask)
5. `backend/requirements.txt` dosyasına şu bağımlılıkları yaz:
   ```
   Flask==3.0.0
   flask-cors==4.0.0
   pypdf2==3.0.1
   pdfplumber==0.10.3
   python-dateutil==2.8.2
   ```
6. `backend/models/schema.sql` dosyasını oluştur ve aşağıdaki SQL komutlarını ekle:
   ```sql
   CREATE TABLE IF NOT EXISTS reports (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       filename TEXT NOT NULL,
       upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
       total_tests INTEGER DEFAULT 0,
       passed_tests INTEGER DEFAULT 0,
       failed_tests INTEGER DEFAULT 0,
       pdf_path TEXT NOT NULL
   );

   CREATE TABLE IF NOT EXISTS test_results (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       report_id INTEGER NOT NULL,
       test_name TEXT NOT NULL,
       status TEXT CHECK(status IN ('PASS', 'FAIL')) NOT NULL,
       error_message TEXT,
       failure_reason TEXT,
       suggested_fix TEXT,
       FOREIGN KEY (report_id) REFERENCES reports(id) ON DELETE CASCADE
   );

   CREATE INDEX idx_report_id ON test_results(report_id);
   CREATE INDEX idx_status ON test_results(status);
   ```
7. `backend/database.py` dosyasını oluştur ve aşağıdaki fonksiyonları tanımla (UTF-8, `pathlib.Path` kullan):
   - `get_db_connection()`
   - `init_db()`
   - `insert_report(filename, pdf_path)`
   - `update_report_stats(report_id, total, passed, failed)`
   - `insert_test_result(report_id, test_name, status, error_msg, reason, fix)`
   - `get_all_reports(sort_by='date', order='desc')`
   - `get_report_by_id(report_id)`
   - `get_failed_tests(report_id)`

8. `backend/pdf_analyzer.py` dosyasında şu fonksiyonları yaz:
   - `extract_text_from_pdf(pdf_path)` (PyPDF2 veya pdfplumber)
   - `parse_test_results(text)` (case-insensitive regex ile PASS/FAIL tespiti)
   - `analyze_failure(error_message)` (ön tanımlı pattern → reason & suggested fix)

9. `backend/routes.py` dosyasında Flask Blueprint tanımla ve bu endpoint'leri implement et:
   - `POST /api/upload`
   - `GET /api/reports`
   - `GET /api/reports/<int:report_id>`
   - `GET /api/reports/<int:report_id>/failures`
   - `DELETE /api/reports/<int:report_id>`
   Tüm yanıtlar JSON olmalı, CORS etkin olmalı, hata yönetimi yapılmalı.

10. `backend/app.py` dosyasında:
    - Flask uygulamasını oluştur ve CORS ayarla.
    - `init_db()` fonksiyonunu ilk çalıştırmada çağır.
    - `uploads/` klasörünü kontrol edip yoksa oluştur.
    - Blueprint'i kaydet ve uygulamayı `host='127.0.0.1', port=5000, debug=True` ile çalıştır.

### 3. Frontend (React)
11. `frontend/package.json` dosyasını şu içerikle oluştur:
    ```json
    {
      "name": "test-report-analyzer-frontend",
      "version": "1.0.0",
      "private": true,
      "dependencies": {
        "axios": "^1.6.0",
        "react": "^18.2.0",
        "react-dom": "^18.2.0",
        "react-router-dom": "^6.20.0"
      },
      "devDependencies": {
        "react-scripts": "5.0.1"
      },
      "scripts": {
        "start": "react-scripts start",
        "build": "react-scripts build"
      },
      "browserslist": {
        "production": [">0.2%", "not dead"],
        "development": ["last 1 chrome version"]
      }
    }
    ```
12. `frontend/public/index.html` dosyasını UTF-8 meta etiketli basit HTML iskeletiyle oluştur.
13. `frontend/src` klasöründe aşağıdaki dosyaları hazırla:
    - `index.js`
    - `App.js`
    - `api.js`
    - `styles/App.css`
    - `components/Dashboard.js`
    - `components/UploadForm.js`
    - `components/ReportDetail.js`
    - `components/TestList.js`

14. `frontend/src/api.js` dosyasında `axios.create` ile `http://localhost:5000/api` taban URL'li istemci oluştur ve şu fonksiyonları dışa aktar:
    - `uploadReport(file)`
    - `getAllReports(sortBy, order)`
    - `getReportById(id)`
    - `getFailedTests(id)`
    - `deleteReport(id)`

15. React bileşenlerinin temel sorumlulukları:
    - `UploadForm`: PDF seçim/yükleme, durum mesajları, başarılı yükleme sonrası parent callback.
    - `Dashboard`: Rapor listesini tablo halinde göster, sıralama/filtreleme, detay ve silme butonları, `UploadForm` entegrasyonu.
    - `ReportDetail`: Seçili raporun özetini ve PASS/FAIL listelerini göster, başarısız testler için neden/öneri alanları.
    - `TestList`: PASS/FAIL rozetleri, isteğe bağlı detay gösterimi.
    - `App`: React Router ile `/` (Dashboard) ve `/report/:id` (ReportDetail) rotalarını yönet, basit bir üst navigasyon ekle.
    - `index.js`: `ReactDOM.createRoot` kullanarak `App` bileşenini render et.

16. `frontend/src/styles/App.css` içinde genel stil rehberi sağlayın (gövde font ayarı, tablo/card stilleri, responsive kurallar, success/error sınıfları vb.).

### 4. PowerShell Scriptleri
17. `setup.ps1`: UTF-8 çıktıyı etkinleştir, Python ve Node.js kurulumlarını denetle, backend için sanal ortam ve bağımlılıkları kur, `init_db()` çalıştır, frontend bağımlılıklarını yükle, `uploads/` klasörünü oluştur.
18. `start-backend.ps1`: UTF-8 çıktıyı ayarla, backend dizinine geç, sanal ortamı aktifleştir, `python app.py` çalıştır.
19. `start-frontend.ps1`: UTF-8 çıktıyı ayarla, frontend dizinine geç, `npm start` çalıştır.
20. `start-app.ps1`: Backend'i yeni PowerShell penceresinde başlat, kısa bekleme sonrası frontend'i yeni pencerede başlat, bağlantı URL'lerini yazdır.
21. `stop-app.ps1`: Çalışan Python ve Node.js süreçlerini sonlandır.

### 5. Test Verisi ve Dokümantasyon
22. `test-samples/` klasörünü oluştur ve `test_report_sample.pdf` isimli örnek raporu ekle (metin içeriği: 5 test, 3 PASS, 2 FAIL – timeout ve NullPointer örnekleri).
23. `README.md` dosyasını aşağıdaki başlıklarla güncelle:
    - Proje Tanımı
    - Özellikler
    - Teknoloji Stack
    - Gereksinimler
    - Kurulum (PowerShell komutlarıyla)
    - Çalıştırma
    - Kullanım
    - API Endpoints
    - Proje Yapısı
    - Lisans

### 6. Git İşlemleri
24. Tüm dosyaları ekleyip şu mesajla ilk commit'i oluştur: `Initial commit: Test Report Analyzer PowerShell setup`.
25. Ana branch adını `main` olarak ayarla.

### 7. Son Kontrol Checklist'i
- [ ] Dizinin tamamı Git'e ekli ve commitlenmiş olmalı.
- [ ] `setup.ps1` ve `start-app.ps1` PowerShell'de sorunsuz çalışmalı.
- [ ] Backend ve frontend 5000/3000 portlarında erişilebilir olmalı.
- [ ] Örnek PDF yüklemesiyle PASS/FAIL analizi yapılabilmeli.
- [ ] README talimatları güncel ve çalıştırılabilir olmalı.

Bu talimatları tamamladıktan sonra projeyi GitHub'a push et.
