# Backend - Test Report Analyzer API

## Environment Variables

### Zorunlu
Hiçbiri (varsayılan değerlerle çalışır)

### Opsiyonel (AI Özelliği için)
```env
ANTHROPIC_API_KEY=sk-ant-...      # Claude API key
OPENAI_API_KEY=sk-proj-...        # OpenAI API key
AI_PROVIDER=none                  # claude|chatgpt|both|none
AI_MODEL_CLAUDE=claude-sonnet-4-5-20250929
AI_MODEL_OPENAI=gpt-4o-mini
AI_MAX_TOKENS=500
AI_TIMEOUT=30
```

## API Endpoints

### POST /api/upload
PDF yükle ve analiz et

### GET /api/reports
Tüm raporları listele

### GET /api/reports/:id
Rapor detayı

### GET /api/ai-status
AI provider durumu

Response:
```json
{
  "provider": "claude",
  "claude_available": true,
  "chatgpt_available": false,
  "status": "active"
}
```

## Çalıştırma
```powershell
# Virtual environment aktif et
.\venv\Scripts\Activate.ps1

# Uygulamayı başlat
python app.py
```
