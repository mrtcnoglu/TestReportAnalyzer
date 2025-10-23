"""Çevrimdışı çeviri yardımcıları.

Bu modül, AI tabanlı çeviri servisleri erişilemediğinde temel düzeyde
çeviri sağlayabilmek için sınırlı ama kullanışlı bir sözlük tabanlı
yaklaşım sunar. Tüm terminoloji kapsanmasa da test raporları bağlamında
tekrar eden ifadeler için anlamlı sonuçlar üretir.
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Dict, Tuple

SUPPORTED_LANGUAGES: Tuple[str, ...] = ("tr", "en", "de")


_BASE_PHRASES: Dict[Tuple[str, str], Dict[str, str]] = {
    ("en", "tr"): {
        "high-speed camera": "yüksek hızlı kamera",
        "high-speed cameras": "yüksek hızlı kameralar",
        "test setup": "test kurulumu",
        "test environment": "test ortamı",
        "ambient temperature": "ortam sıcaklığı",
        "measurement file": "ölçüm dosyası",
        "expert notes": "uzman notları",
        "test conditions": "test koşulları",
        "camera recordings": "kamera kayıtları",
        "no deviations": "sapma yok",
        "data logger": "veri kaydedici",
        "was performed with": "ile gerçekleştirildi",
        "was carried out": "gerçekleştirildi",
    },
    ("en", "de"): {
        "high-speed camera": "Hochgeschwindigkeitskamera",
        "high-speed cameras": "Hochgeschwindigkeitskameras",
        "test setup": "Testaufbau",
        "test environment": "Testumgebung",
        "ambient temperature": "Umgebungstemperatur",
        "measurement file": "Messdatei",
        "expert notes": "Expertenhinweise",
        "test conditions": "Testbedingungen",
        "camera recordings": "Kameraaufzeichnungen",
        "no deviations": "Keine Abweichungen",
        "data logger": "Datenlogger",
        "was carried out": "wurde durchgeführt",
    },
}


_BASE_WORDS: Dict[Tuple[str, str], Dict[str, str]] = {
    ("en", "tr"): {
        "test": "test",
        "tests": "testler",
        "note": "not",
        "notes": "notlar",
        "camera": "kamera",
        "cameras": "kameralar",
        "recorded": "kaydedildi",
        "recording": "kayıt",
        "environment": "ortam",
        "condition": "koşul",
        "conditions": "koşulları",
        "system": "sistem",
        "operator": "operatör",
        "measurement": "ölçüm",
        "measurements": "ölçümler",
        "performed": "gerçekleştirildi",
        "analysis": "analiz",
        "summary": "özet",
        "failure": "başarısızlık",
        "pass": "başarılı",
        "fail": "başarısız",
        "reference": "referans",
        "temperature": "sıcaklık",
        "humidity": "nem",
        "voltage": "voltaj",
        "frequency": "frekans",
        "power": "güç",
        "setup": "kurulum",
        "load": "yük",
        "result": "sonuç",
        "results": "sonuçlar",
        "expert": "uzman",
        "warning": "uyarı",
        "attention": "dikkat",
        "with": "ile",
        "under": "altında",
        "the": "",
        "was": "oldu",
        "carried": "gerçekleştirildi",
        "out": "",
    },
    ("en", "de"): {
        "test": "Test",
        "tests": "Tests",
        "note": "Hinweis",
        "notes": "Hinweise",
        "camera": "Kamera",
        "cameras": "Kameras",
        "recorded": "aufgezeichnet",
        "recording": "Aufzeichnung",
        "environment": "Umgebung",
        "condition": "Bedingung",
        "conditions": "Bedingungen",
        "system": "System",
        "operator": "Operator",
        "measurement": "Messung",
        "measurements": "Messungen",
        "performed": "durchgeführt",
        "analysis": "Analyse",
        "summary": "Zusammenfassung",
        "failure": "Fehler",
        "pass": "bestanden",
        "fail": "fehlgeschlagen",
        "reference": "Referenz",
        "temperature": "Temperatur",
        "humidity": "Feuchtigkeit",
        "voltage": "Spannung",
        "frequency": "Frequenz",
        "power": "Leistung",
        "setup": "Aufbau",
        "load": "Belastung",
        "result": "Ergebnis",
        "results": "Ergebnisse",
        "expert": "Experte",
        "warning": "Warnung",
        "attention": "Achtung",
        "with": "mit",
        "under": "unter",
        "was": "war",
        "carried": "durchgeführt",
        "out": "",
    },
}


_EXTRA_PHRASES: Dict[Tuple[str, str], Dict[str, str]] = {
    ("de", "en"): {
        "wurde mit": "was performed with",
        "wurde unter": "was conducted under",
        "für hochgeschwindigkeitskameras": "for high-speed cameras",
    },
    ("de", "tr"): {
        "wurde mit": "ile gerçekleştirildi",
        "wurde unter": "altında yürütüldü",
    },
    ("tr", "en"): {
        "yüksek hızlı": "high-speed",
        "test raporu": "test report",
    },
    ("tr", "de"): {
        "yüksek hızlı": "hohe geschwindigkeit",
        "test koşulları": "Testbedingungen",
    },
}


_EXTRA_WORDS: Dict[Tuple[str, str], Dict[str, str]] = {
    ("de", "en"): {
        "der": "the",
        "die": "the",
        "das": "the",
        "ein": "a",
        "eine": "a",
        "wurde": "was",
        "wurden": "were",
        "mit": "with",
        "unter": "under",
        "bei": "at",
        "messung": "measurement",
        "messungen": "measurements",
        "geräte": "equipment",
        "ausrüstung": "equipment",
        "hinweis": "note",
        "hinweise": "notes",
        "kamera": "camera",
        "kameras": "cameras",
        "bedingungen": "conditions",
        "umgebung": "environment",
        "temperatur": "temperature",
        "feuchtigkeit": "humidity",
        "aufgenommen": "recorded",
        "aufzeichnung": "recording",
        "protokoll": "log",
        "daten": "data",
        "getestet": "tested",
        "test": "test",
        "prüfung": "test",
        "gerät": "device",
        "ergebnis": "result",
        "ergebnisse": "results",
        "abweichung": "deviation",
        "abweichungen": "deviations",
    },
    ("tr", "en"): {
        "ile": "with",
        "altında": "under",
        "yapıldı": "was carried out",
        "kaydedildi": "was recorded",
        "çalıştı": "operated",
        "koşul": "condition",
        "koşulları": "conditions",
        "cihaz": "device",
        "cihazı": "device",
        "test": "test",
        "not": "note",
        "notları": "notes",
        "notu": "note",
        "ölçüm": "measurement",
        "ölçümler": "measurements",
        "gerçekleştirildi": "was performed",
        "ortam": "environment",
        "sıcaklığı": "temperature",
        "kamera": "camera",
        "kameralar": "cameras",
    },
}


def _normalise_language(language: str | None) -> str:
    if not language:
        return ""
    value = language.strip().lower()
    return value if value in SUPPORTED_LANGUAGES else ""


def _invert_dictionary(entries: Dict[str, str]) -> Dict[str, str]:
    inverted: Dict[str, str] = {}
    for key, value in entries.items():
        key_clean = key.strip()
        value_clean = value.strip()
        if not key_clean or not value_clean:
            continue
        inverted[value_clean.lower()] = key_clean
    return inverted


def _generate_translation_tables() -> Dict[Tuple[str, str], Dict[str, Dict[str, str]]]:
    tables: Dict[Tuple[str, str], Dict[str, Dict[str, str]]] = {}

    for (source, target), phrases in _BASE_PHRASES.items():
        tables.setdefault((source, target), {})["phrases"] = phrases

    for (source, target), words in _BASE_WORDS.items():
        tables.setdefault((source, target), {})["words"] = words

    for (source, target), phrases in _EXTRA_PHRASES.items():
        merged = tables.setdefault((source, target), {}).setdefault("phrases", {})
        merged.update(phrases)

    for (source, target), words in _EXTRA_WORDS.items():
        merged = tables.setdefault((source, target), {}).setdefault("words", {})
        merged.update(words)

    # Ters yöndeki sözlükleri üret.
    for (source, target), data in list(tables.items()):
        reverse_key = (target, source)
        reversed_phrases = {
            value.lower(): key
            for key, value in data.get("phrases", {}).items()
            if key and value
        }
        reversed_words = _invert_dictionary(data.get("words", {}))
        if reversed_phrases:
            phrase_bucket = tables.setdefault(reverse_key, {}).setdefault("phrases", {})
            for key, value in reversed_phrases.items():
                phrase_bucket.setdefault(key, value)
        if reversed_words:
            word_bucket = tables.setdefault(reverse_key, {}).setdefault("words", {})
            for key, value in reversed_words.items():
                word_bucket.setdefault(key, value)

    return tables


@lru_cache(maxsize=None)
def _translation_tables() -> Dict[Tuple[str, str], Dict[str, Dict[str, str]]]:
    return _generate_translation_tables()


def _apply_case(template: str, replacement: str) -> str:
    if not template:
        return replacement
    if template.isupper():
        return replacement.upper()
    if template[0].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement


def _apply_phrase_translations(text: str, phrases: Dict[str, str]) -> str:
    if not phrases:
        return text

    def replacement(match: re.Match) -> str:
        matched = match.group(0)
        key = matched.lower()
        translated = phrases.get(key, "")
        return _apply_case(matched, translated) if translated else matched

    # Daha uzun ifadeleri önce ele almak için uzunluğa göre sırala.
    pattern = "|".join(
        re.escape(phrase)
        for phrase in sorted(phrases.keys(), key=len, reverse=True)
        if phrase
    )
    if not pattern:
        return text

    regex = re.compile(pattern, flags=re.IGNORECASE)
    return regex.sub(replacement, text)


def _apply_word_translations(text: str, words: Dict[str, str]) -> str:
    if not words:
        return text

    def replacement(match: re.Match) -> str:
        token = match.group(0)
        lookup = token.lower()
        translated = words.get(lookup)
        if translated is None:
            return token
        if translated == "":
            return ""
        return _apply_case(token, translated)

    pattern = re.compile(r"\b[\wÄÖÜäöüßÇĞİÖŞÜçğıöşü]+\b", flags=re.UNICODE)
    return pattern.sub(replacement, text)


def _translate_direct(text: str, source: str, target: str) -> str:
    tables = _translation_tables()
    data = tables.get((source, target), {})
    phrases = {key.lower(): value for key, value in data.get("phrases", {}).items()}
    words = {key.lower(): value for key, value in data.get("words", {}).items()}

    translated = _apply_phrase_translations(text, phrases)
    translated = _apply_word_translations(translated, words)
    return translated


def _tidy_text(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    cleaned = cleaned.replace(" ,", ",").replace(" .", ".").replace(" :", ":")
    return cleaned


def _contains_language_hints(text: str, language: str) -> bool:
    hints = {
        "de": (" der ", " die ", " das ", " mit ", " auf", " prüf", " kamera"),
        "tr": (" ile ", " için ", " test ", " ölç", " cihaz", " koşul", " yapıldı"),
    }
    candidates = hints.get(language)
    if not candidates:
        return False
    lowered = f" {text.lower()} "
    return any(keyword in lowered for keyword in candidates)


def _needs_translation(text: str, source: str, target: str) -> bool:
    if source == target:
        return False
    sample = text.strip()
    if not sample:
        return False
    # Eğer metin hedef dile ait bazı karakterleri içeriyorsa yeniden çevirmeye gerek yok.
    target_specific = {
        "tr": "çğıöşüİ",
        "de": "äöüß",
        "en": "",
    }
    hints = target_specific.get(target, "")
    source_hints = target_specific.get(source, "")
    if hints and any(char in sample for char in hints):
        return False
    if source_hints and any(char in sample for char in source_hints):
        return True
    return True


def fallback_translate_text(
    text: str,
    *,
    source_language: str | None,
    target_language: str,
) -> str:
    """Sözlük tabanlı basit çeviri.

    Desteklenen diller dışındaki isteklerde ya da çevirinin gerekli
    olmadığı durumlarda orijinal metni döndürür.
    """

    cleaned_text = (text or "").strip()
    if not cleaned_text:
        return ""

    source = _normalise_language(source_language) or ""
    target = _normalise_language(target_language)

    if not target or target == source:
        return cleaned_text

    if source and not _needs_translation(cleaned_text, source, target):
        return cleaned_text

    direct = _translate_direct(cleaned_text, source or "en", target)

    if direct != cleaned_text and source and _contains_language_hints(direct, source):
        direct = cleaned_text

    if direct != cleaned_text or not source or source == "en":
        return _tidy_text(direct)

    # Kaynak dil İngilizce değilse İngilizce üzerinden pivot çeviri dene.
    pivot = _translate_direct(cleaned_text, source, "en")
    if pivot != cleaned_text:
        second_pass = _translate_direct(pivot, "en", target)
        return _tidy_text(second_pass)

    return _tidy_text(direct)

