# -*- coding: utf-8 -*-
"""AI destekli test hatası analizi yardımcı sınıfı."""

import json
import os
import re
import textwrap
from typing import Dict, List, Optional, Sequence, Tuple

from anthropic import Anthropic
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


DEFAULT_SUMMARY_LABELS: Dict[str, Dict[str, str]] = {
    "tr": {
        "summary": "Genel Özet",
        "conditions": "Test Koşulları",
        "improvements": "İyileştirme Önerileri",
        "technical": "Teknik Analiz Detayları",
        "highlights": "Öne Çıkan Bulgular",
        "failures": "Kritik Testler",
    },
    "en": {
        "summary": "Summary",
        "conditions": "Test Conditions",
        "improvements": "Improvement Suggestions",
        "technical": "Technical Analysis Details",
        "highlights": "Key Highlights",
        "failures": "Critical Tests",
    },
    "de": {
        "summary": "Zusammenfassung",
        "conditions": "Testbedingungen",
        "improvements": "Verbesserungsvorschläge",
        "technical": "Technische Analyse",
        "highlights": "Wesentliche Erkenntnisse",
        "failures": "Kritische Tests",
    },
}


class AIAnalyzer:
    """Test başarısızlıklarını AI veya kural tabanlı yöntemlerle analiz eder."""

    def __init__(self) -> None:
        self.provider = "none"
        self.anthropic_key = ""
        self.openai_key = ""
        self.claude_model = "claude-sonnet-4-5-20250929"
        self.openai_model = "gpt-4o-mini"
        self.max_tokens = 500
        self.timeout = 30
        self.claude_client = None
        self.openai_client = None
        self._claude_client_key = None
        self._openai_client_key = None
        self._translation_cache: Dict[
            Tuple[str, str, Tuple[str, ...]], Dict[str, str]
        ] = {}
        self._refresh_configuration()

    def _refresh_configuration(self) -> None:
        """Ortam değişkenlerini okuyup gerekli istemcileri güncelle."""
        provider_value = (os.getenv("AI_PROVIDER", self.provider) or "none").strip().lower()
        if provider_value not in {"claude", "chatgpt", "both", "none"}:
            provider_value = "none"
        self.provider = provider_value
        self.anthropic_key = (os.getenv("ANTHROPIC_API_KEY", "") or "").strip()
        self.openai_key = (os.getenv("OPENAI_API_KEY", "") or "").strip()
        self.claude_model = os.getenv("AI_MODEL_CLAUDE", self.claude_model)
        self.openai_model = os.getenv("AI_MODEL_OPENAI", self.openai_model)

        try:
            self.max_tokens = int(os.getenv("AI_MAX_TOKENS", str(self.max_tokens)) or self.max_tokens)
        except ValueError:
            self.max_tokens = 500

        try:
            self.timeout = int(os.getenv("AI_TIMEOUT", str(self.timeout)) or self.timeout)
        except ValueError:
            self.timeout = 30

        if self.anthropic_key:
            if self.anthropic_key != self._claude_client_key:
                try:
                    self.claude_client = Anthropic(api_key=self.anthropic_key)
                    self._claude_client_key = self.anthropic_key
                except Exception as exc:  # pragma: no cover - yalnızca hata kaydı
                    print(f"[AIAnalyzer] Claude istemcisi oluşturulamadı: {exc}")
                    self.claude_client = None
                    self._claude_client_key = None
        else:
            self.claude_client = None
            self._claude_client_key = None

        if self.openai_key:
            if self.openai_key != self._openai_client_key:
                try:
                    self.openai_client = OpenAI(api_key=self.openai_key)
                    self._openai_client_key = self.openai_key
                except Exception as exc:  # pragma: no cover - yalnızca hata kaydı
                    print(f"[AIAnalyzer] OpenAI istemcisi oluşturulamadı: {exc}")
                    self.openai_client = None
                    self._openai_client_key = None
        else:
            self.openai_client = None
            self._openai_client_key = None

    def analyze_failure_with_ai(self, test_name: str, error_message: str, test_context: str = "") -> Dict[str, str]:
        """Sağlanan AI sağlayıcısına göre analiz yap."""
        self._refresh_configuration()
        prompt = self._create_analysis_prompt(test_name, error_message, test_context)

        provider = self.provider or "none"
        provider = provider.lower()

        if provider == "none":
            return self._rule_based_analysis(error_message)

        if provider == "claude":
            return self._analyze_with_claude(prompt, error_message)

        if provider == "chatgpt":
            return self._analyze_with_chatgpt(prompt, error_message)

        if provider == "both":
            claude_result = self._analyze_with_claude(prompt, error_message)
            if claude_result.get("ai_provider") == "claude":
                return claude_result
            return self._analyze_with_chatgpt(prompt, error_message)

        # Bilinmeyen provider durumunda kural tabanlı analize dön
        return self._rule_based_analysis(error_message)

    def _create_analysis_prompt(self, test_name: str, error_message: str, test_context: str) -> str:
        """AI modelinden yapılandırılmış bir JSON çıktısı isteyen Türkçe prompt hazırla."""
        context_section = ""
        if test_context.strip():
            context_section = f"\nTest bağlamı:\n{test_context.strip()}"

        prompt = (
            "Aşağıdaki test başarısızlığını analiz et ve nedenini açıkla. "
            "Yanıtta yalnızca JSON formatı döndür."
            f"\n\nTest adı: {test_name}\nHata mesajı: {error_message}{context_section}\n"
            "\nLütfen şu JSON formatında ve Türkçe yanıt ver:\n"
            "{\n"
            "  \"failure_reason\": \"<kısa açıklama>\",\n"
            "  \"suggested_fix\": \"<önerilen çözüm>\"\n"
            "}"
        )
        return prompt

    def _analyze_with_claude(self, prompt: str, error_message: str) -> Dict[str, str]:
        """Claude API çağrısı yap ve sonucu JSON olarak işle."""
        if not self.claude_client:
            return self._rule_based_analysis(error_message)

        try:
            data = self._request_json_from_claude(prompt, max_tokens=self.max_tokens)
            failure_reason = data.get("failure_reason", "").strip()
            suggested_fix = data.get("suggested_fix", "").strip()
            if not failure_reason or not suggested_fix:
                raise ValueError("Claude yanıtı eksik alan içeriyor")
            return {
                "failure_reason": failure_reason,
                "suggested_fix": suggested_fix,
                "ai_provider": "claude",
            }
        except Exception as exc:  # pragma: no cover - API hataları kullanıcıya gösterilmez
            print(f"[AIAnalyzer] Claude analizi başarısız: {exc}")
            return self._rule_based_analysis(error_message)

    def _analyze_with_chatgpt(self, prompt: str, error_message: str) -> Dict[str, str]:
        """OpenAI Chat Completions API çağrısı yap."""
        if not self.openai_client:
            return self._rule_based_analysis(error_message)

        try:
            data = self._request_json_from_chatgpt(prompt, max_tokens=self.max_tokens)
            failure_reason = data.get("failure_reason", "").strip()
            suggested_fix = data.get("suggested_fix", "").strip()
            if not failure_reason or not suggested_fix:
                raise ValueError("ChatGPT yanıtı eksik alan içeriyor")
            return {
                "failure_reason": failure_reason,
                "suggested_fix": suggested_fix,
                "ai_provider": "chatgpt",
            }
        except Exception as exc:  # pragma: no cover - API hataları kullanıcıya gösterilmez
            print(f"[AIAnalyzer] ChatGPT analizi başarısız: {exc}")
            return self._rule_based_analysis(error_message)

    def _request_json_from_claude(self, prompt: str, max_tokens: Optional[int] = None) -> Dict:
        """Claude API'sinden JSON içerik döndür."""
        if not self.claude_client:
            raise ValueError("Claude client not configured")

        client = self.claude_client
        if hasattr(client, "with_options"):
            client = client.with_options(timeout=self.timeout)

        response = client.messages.create(
            model=self.claude_model,
            max_output_tokens=max_tokens or self.max_tokens,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )

        content = ""
        if getattr(response, "content", None):
            content = "".join(
                getattr(block, "text", "") for block in response.content if getattr(block, "text", "")
            )

        if not content:
            raise ValueError("Claude yanıtı boş döndü")

        return json.loads(content)

    def _request_json_from_chatgpt(self, prompt: str, max_tokens: Optional[int] = None) -> Dict:
        """OpenAI Chat Completions API çağrısından JSON yanıtı döndür."""
        if not self.openai_client:
            raise ValueError("ChatGPT client not configured")

        client = self.openai_client
        if hasattr(client, "with_options"):
            client = client.with_options(timeout=self.timeout)

        response = client.chat.completions.create(
            model=self.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": "Sen uzman bir test analisti olarak Türkçe konuşuyorsun. Yanıtı JSON formatında üret.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens or self.max_tokens,
            temperature=0,
        )

        content = response.choices[0].message.content if response.choices else ""
        if not content:
            raise ValueError("ChatGPT yanıtı boş döndü")

        return json.loads(content)

    def _prepare_report_excerpt(self, text: str, limit: int = 12000) -> str:
        """PDF metninden özet çıkar ve uzunluğu sınırla."""
        cleaned = re.sub(r"\s+", " ", text.strip())
        if len(cleaned) <= limit:
            return cleaned

        # Metnin başından, ortasından ve sonundan örnekler alarak bağlamı koru
        segment_length = max(limit // 3, 1000)
        head = cleaned[:segment_length]
        tail = cleaned[-segment_length:]
        midpoint = len(cleaned) // 2
        middle_start = max(midpoint - segment_length // 2, 0)
        middle_end = middle_start + segment_length
        middle = cleaned[middle_start:middle_end]

        return "\n…\n".join([head.strip(), middle.strip(), tail.strip()])

    def _create_report_summary_prompt(
        self,
        *,
        filename: str,
        report_type: str,
        total_tests: int,
        passed_tests: int,
        failed_tests: int,
        excerpt: str,
        failure_details: Sequence[Dict[str, str]],
    ) -> str:
        """Raporun tamamını özetleyecek çok dilli JSON yanıtı iste."""

        failure_lines: List[str] = []
        for failure in failure_details:
            test_name = failure.get("test_name", "Bilinmeyen Test")
            reason = failure.get("failure_reason") or failure.get("error_message") or ""
            suggestion = failure.get("suggested_fix") or ""
            joined = f"{test_name}: {reason}".strip()
            if suggestion:
                joined += f" | Öneri: {suggestion}"
            failure_lines.append(joined)

        failure_block = "\n".join(failure_lines) if failure_lines else "(başarısız test bulunmuyor)"

        prompt = f"""
PDF test raporunu analiz eden uzman bir mühendis olarak hareket et. Rapor dosya adı: {filename}. Test türü: {report_type}.
Toplam test sayısı: {total_tests}. Başarılı test sayısı: {passed_tests}. Başarısız test sayısı: {failed_tests}.
Başarısız testlerin özet listesi:
{failure_block}

Rapor metninden çıkarılmış içerik (görsel ve tablo açıklamaları dahil olabilir):
"""

        prompt += excerpt
        prompt += """

GÖREV:
- Metni dikkatlice incele; grafikler, ölçüm koşulları, kullanılan standartlar, sonuçlar ve uzman yorumları gibi öğeleri ayrıntılı biçimde değerlendir.
- Yanıtı mutlaka geçerli JSON formatında ver.
- Her dil için summary/conditions/improvements alanlarına ek olarak "labels" nesnesi üret ve bu nesnede ilgili başlıkları (ör. "Test Koşulları", "Test Conditions", "Testbedingungen") o dilde ver.
- "sections" alanında grafikler, test kurulumları, ölçüm sonuçları ve yorumlara dair teknik özeti ayrıntılı doldur.
- Aşağıdaki yapıyı kullan:
{
  "localized_summaries": {
    "tr": {"summary": "...", "conditions": "...", "improvements": "...", "labels": {"summary": "Genel Özet", "conditions": "Test Koşulları", "improvements": "İyileştirme Önerileri"}},
    "en": {"summary": "...", "conditions": "...", "improvements": "...", "labels": {"summary": "Summary", "conditions": "Test Conditions", "improvements": "Improvement Suggestions"}},
    "de": {"summary": "...", "conditions": "...", "improvements": "...", "labels": {"summary": "Zusammenfassung", "conditions": "Testbedingungen", "improvements": "Verbesserungsvorschläge"}}
  },
  "sections": {
    "graphs": "Grafik ve görsel anlatımların özeti",
    "conditions": "Test kurulumları ve çevresel koşullar",
    "results": "Önemli ölçüm sonuçları",
    "comments": "Uzman görüşü veya değerlendirilen yorumlar"
  },
  "highlights": ["En fazla 5 kısa maddelik önemli bulgular listesi"]
}

Tüm metinleri ilgili dilde üret. JSON dışında açıklama yapma.
"""

        return textwrap.dedent(prompt).strip()

    def _create_translation_prompt(
        self,
        *,
        text: str,
        source_language: str,
        target_languages: Sequence[str],
    ) -> str:
        language_names = {"tr": "Turkish", "en": "English", "de": "German"}
        source_label = language_names.get(source_language, source_language or "original language")
        targets_description = ", ".join(
            f"{language_names.get(lang, lang)} ({lang})" for lang in target_languages
        )
        key_list = ", ".join(f'"{lang}"' for lang in target_languages)
        example_lines: List[str] = []
        for index, lang in enumerate(target_languages):
            suffix = "," if index < len(target_languages) - 1 else ""
            example_lines.append(f'                "{lang}": "..."{suffix}')
        example_block = "\n".join(example_lines) if example_lines else '                "tr": "..."'
        template = """
            Sen teknik test raporları için uzman bir çevirmen olarak görev yapıyorsun.
            Verilen metin {source_label} dilindedir. Bu metni {targets_description} dillerine çevir.
            Yanıtını mutlaka geçerli JSON formatında ver ve ek açıklama ekleme.
            JSON çıktısında yalnızca translations anahtarını ve şu alt anahtarları kullan: {key_list}.
            Örnek yapı:
            {{
              "translations": {{
{example_block}
              }}
            }}

            Çevrilecek metin aşağıda verilmiştir:
            ---
            {text}
            ---
        """
        prompt = textwrap.dedent(template).strip().format(
            source_label=source_label,
            targets_description=targets_description,
            key_list=key_list,
            example_block=example_block,
            text=text,
        )
        return prompt

    def _parse_translation_response(
        self, payload: Dict, target_languages: Sequence[str]
    ) -> Dict[str, str]:
        translations = payload.get("translations") if isinstance(payload, dict) else {}
        normalised: Dict[str, str] = {}
        if isinstance(translations, dict):
            for language in target_languages:
                value = translations.get(language, "") if language in translations else ""
                value_str = str(value).strip()
                if value_str:
                    normalised[language] = value_str
        else:
            for language in target_languages:
                value = payload.get(language, "") if isinstance(payload, dict) else ""
                value_str = str(value).strip()
                if value_str:
                    normalised[language] = value_str
        return normalised

    def translate_texts(
        self,
        text: str,
        *,
        source_language: Optional[str] = None,
        target_languages: Sequence[str] = (),
    ) -> Dict[str, str]:
        cleaned_text = (text or "").strip()
        if not cleaned_text:
            return {}

        targets = tuple(sorted({str(lang).strip().lower() for lang in target_languages if str(lang).strip()}))
        if not targets:
            return {}

        source_key = (source_language or "").strip().lower()
        cache_key = (source_key, cleaned_text, targets)
        if cache_key in self._translation_cache:
            return dict(self._translation_cache[cache_key])

        self._refresh_configuration()
        provider = (self.provider or "none").lower()
        if provider == "none":
            return {}

        prompt = self._create_translation_prompt(
            text=cleaned_text, source_language=source_key or "", target_languages=targets
        )
        candidates: List[str]
        if provider == "both":
            candidates = ["claude", "chatgpt"]
        else:
            candidates = [provider]

        max_tokens = min(self.max_tokens * 2, 1200)
        for candidate in candidates:
            try:
                if candidate == "claude":
                    data = self._request_json_from_claude(prompt, max_tokens=max_tokens)
                else:
                    data = self._request_json_from_chatgpt(prompt, max_tokens=max_tokens)
                if not isinstance(data, dict):
                    continue
                translations = self._parse_translation_response(data, targets)
                if translations:
                    self._translation_cache[cache_key] = dict(translations)
                    return translations
            except Exception as exc:  # pragma: no cover - API hataları kullanıcıya gösterilmez
                print(f"[AIAnalyzer] {candidate} çeviri isteği başarısız: {exc}")
                continue

        return {}

    def _normalise_summary_response(self, payload: Dict) -> Dict[str, object]:
        """AI yanıtını öngörülen anahtarlara göre düzenle."""

        localized = payload.get("localized_summaries") or payload.get("localized") or payload.get("languages") or {}
        sections = payload.get("sections") or payload.get("structured_sections") or {}
        highlights = payload.get("highlights") or payload.get("key_findings") or []

        normalised_localized = {}
        for language in ("tr", "en", "de"):
            entry = localized.get(language, {}) if isinstance(localized, dict) else {}
            raw_labels = entry.get("labels") if isinstance(entry, dict) else {}
            defaults = DEFAULT_SUMMARY_LABELS.get(language, {})
            labels = {}
            for key in ("summary", "conditions", "improvements", "technical", "highlights", "failures"):
                value = ""
                if isinstance(raw_labels, dict):
                    value = str(raw_labels.get(key, "")).strip()
                default_value = str(defaults.get(key, "")).strip()
                labels[key] = value or default_value

            normalised_localized[language] = {
                "summary": (entry.get("summary") or "").strip(),
                "conditions": (entry.get("conditions") or "").strip(),
                "improvements": (entry.get("improvements") or "").strip(),
                "labels": labels,
            }

        normalised_sections = {}
        if isinstance(sections, dict):
            for key in ("graphs", "conditions", "results", "comments"):
                value = sections.get(key, "")
                if isinstance(value, list):
                    value = " ".join(str(item).strip() for item in value if str(item).strip())
                normalised_sections[key] = str(value).strip()

        normalised_highlights: List[str] = []
        if isinstance(highlights, (list, tuple)):
            for item in highlights:
                text = str(item).strip()
                if text:
                    normalised_highlights.append(text)

        return {
            "localized_summaries": normalised_localized,
            "sections": normalised_sections,
            "highlights": normalised_highlights,
        }

    def generate_report_summary(
        self,
        *,
        filename: str,
        report_type: str,
        total_tests: int,
        passed_tests: int,
        failed_tests: int,
        raw_text: str,
        failure_details: Sequence[Dict[str, str]],
    ) -> Optional[Dict[str, object]]:
        """PDF metnini detaylı şekilde inceleyen bir özet üret."""

        self._refresh_configuration()
        provider = (self.provider or "none").lower()
        if provider == "none":
            return None

        excerpt = self._prepare_report_excerpt(raw_text)
        prompt = self._create_report_summary_prompt(
            filename=filename,
            report_type=report_type,
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            excerpt=excerpt,
            failure_details=failure_details,
        )

        providers: List[str]
        if provider == "both":
            providers = ["claude", "chatgpt"]
        else:
            providers = [provider]

        for candidate in providers:
            try:
                if candidate == "claude":
                    data = self._request_json_from_claude(prompt, max_tokens=min(self.max_tokens * 2, 1500))
                else:
                    data = self._request_json_from_chatgpt(prompt, max_tokens=min(self.max_tokens * 2, 1500))
                if not isinstance(data, dict):
                    continue
                return self._normalise_summary_response(data)
            except Exception as exc:  # pragma: no cover - ağ hataları raporlanmaz
                print(f"[AIAnalyzer] Rapor özeti üretilemedi ({candidate}): {exc}")

        return None

    def _rule_based_analysis(self, error_message: str) -> Dict[str, str]:
        """Basit kural tabanlı analizle fallback sonucu döndür."""
        message = (error_message or "").lower()

        if "timeout" in message:
            return {
                "failure_reason": "Test zaman aşımına uğradı",
                "suggested_fix": "Zaman aşımı limitini artırın veya performans darboğazlarını araştırın.",
                "ai_provider": "rule-based",
            }
        if "connection" in message or "network" in message:
            return {
                "failure_reason": "Bağlantı veya ağ hatası",
                "suggested_fix": "Servislerin ve ağ bağlantısının çalıştığını doğrulayın.",
                "ai_provider": "rule-based",
            }
        if "null" in message or "none" in message:
            return {
                "failure_reason": "Boş/None değer kullanımı",
                "suggested_fix": "Null kontrolleri ekleyin ve gerekli verilerin sağlandığından emin olun.",
                "ai_provider": "rule-based",
            }
        if "permission" in message:
            return {
                "failure_reason": "Yetki hatası",
                "suggested_fix": "Kullanıcı veya servis hesabına gerekli izinleri tanımlayın.",
                "ai_provider": "rule-based",
            }
        if "authentication" in message or "auth" in message:
            return {
                "failure_reason": "Kimlik doğrulama başarısız",
                "suggested_fix": "Kimlik doğrulama bilgilerini ve token geçerliliğini kontrol edin.",
                "ai_provider": "rule-based",
            }
        if "assertion" in message:
            return {
                "failure_reason": "Beklenen koşul sağlanamadı",
                "suggested_fix": "Testteki beklenen değerleri veya uygulama mantığını gözden geçirin.",
                "ai_provider": "rule-based",
            }

        return {
            "failure_reason": "Hata mesajını inceleyerek detaylı kök neden analizi yapın.",
            "suggested_fix": "İlgili log kayıtlarını ve stack trace'i kontrol edin.",
            "ai_provider": "rule-based",
        }


# Dosyanın sonunda singleton instance oluştur
ai_analyzer = AIAnalyzer()
