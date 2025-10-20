# -*- coding: utf-8 -*-
"""AI destekli test hatası analizi yardımcı sınıfı."""

import json
import os
from typing import Dict

from anthropic import Anthropic
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


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
            client = self.claude_client
            if hasattr(client, "with_options"):
                client = client.with_options(timeout=self.timeout)

            response = client.messages.create(
                model=self.claude_model,
                max_output_tokens=self.max_tokens,
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

            data = json.loads(content)
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
                max_tokens=self.max_tokens,
                temperature=0,
            )

            content = response.choices[0].message.content if response.choices else ""
            if not content:
                raise ValueError("ChatGPT yanıtı boş döndü")
            data = json.loads(content)
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
