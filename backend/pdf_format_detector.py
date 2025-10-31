# -*- coding: utf-8 -*-
import re
import logging

logger = logging.getLogger(__name__)


def detect_pdf_format(text):
    """PDF formatını tespit et"""
    text_lower = (text or "").lower()

    if any(
        keyword in text_lower
        for keyword in [
            "nosab 16140",
            "tüv rheinland",
            "tuv rheinland",
            "kielt",
            "prüfbericht",
            "justierung/kontrolle",
        ]
    ):
        return "kielt_format"

    if "junit" in text_lower:
        return "junit_format"

    return "generic"


def parse_kielt_format(text):
    """
    Kielt/TÜV formatındaki PDF'i parse et - GERÇEK FORMAT

    Bu formatta:
    - "Test Koşulları" başlığı altında tüm bilgiler
    - "Justierung/Kontrolle" altında ölçüm değerleri
    - "Schlittenverzögerung" ayrı bölüm
    - "Belastungswerte" başlığı YOK (veriler doğrudan var)
    """
    sections = {}

    # 1. Test Koşulları - Ana bilgiler
    test_cond_pattern = (
        r"(?:Test\s*(?:Koşulları|Conditions|bedingungen))[:\s]*(.+?)(?=Schlittenverzögerung|Fotodokumentation|Prüfbericht\s+kielt|$)"
    )
    test_cond_match = re.search(test_cond_pattern, text, re.IGNORECASE | re.DOTALL)

    if test_cond_match:
        content = test_cond_match.group(1).strip()
        sections["test_conditions"] = content[:1500]
        logger.info("Test koşulları bulundu: %s karakter", len(content))

    # 2. Justierung/Kontrolle bölümü - Ölçüm değerleri burada
    justierung_pattern = r"Justierung/Kontrolle\s*:(.+?)(?=Software|Ingenieurbüro|Schlittenverzögerung|===|$)"
    justierung_match = re.search(justierung_pattern, text, re.IGNORECASE | re.DOTALL)

    if justierung_match:
        content = justierung_match.group(1).strip()
        sections["load_values"] = content
        sections["measurement_data"] = content
        logger.info("Ölçüm verileri bulundu: %s karakter", len(content))

    # 3. Schlittenverzögerung - Kızak yavaşlaması
    sled_pattern = r"Schlittenverzögerung:(.+?)(?=Fotodokumentation|Prüfbericht\s+kielt|===|$)"
    sled_match = re.search(sled_pattern, text, re.IGNORECASE | re.DOTALL)

    if sled_match:
        content = sled_match.group(1).strip()
        sections["sled_deceleration"] = content[:1000]
        logger.info("Schlittenverzögerung bulundu: %s karakter", len(content))

    # 4. Fotodokumentation
    photo_pattern = r"Fotodokumentation:(.+?)(?=Prüfbericht\s+kielt|Bearbeiter|$)"
    photo_match = re.search(photo_pattern, text, re.IGNORECASE | re.DOTALL)

    if photo_match:
        content = photo_match.group(1).strip()
        sections["photo_docs"] = content[:500]

    # 5. TABLO bölümlerini topla
    table_sections = []
    table_pattern = r"===\s*SAYFA\s*\d+\s*-\s*TABLO\s*\d+\s*===(.{0,100})"
    for match in re.finditer(table_pattern, text, re.IGNORECASE):
        table_sections.append(match.group(0))

    if table_sections:
        sections["tables_text"] = "\n".join(table_sections)

    return sections


def extract_measurement_params(text):
    """
    GERÇEK formatına göre ölçüm parametrelerini çıkar

    Format:
        a Kopf über 3 ms [g] 58.15
        ThAC [g] 18.4
        FAC right F [kN] 4.40
    """
    params = []

    # Pattern 1: "a Kopf über 3 ms [g] 58.15"
    kopf_pattern = r"a\s+Kopf\s+über\s+3\s*ms\s*\[g\]\s*([\d\.]+)"
    kopf_matches = re.findall(kopf_pattern, text, re.IGNORECASE)
    if kopf_matches:
        params.append(
            {
                "name": "Baş ivmesi (a Kopf über 3 ms)",
                "unit": "g",
                "values": kopf_matches,
            }
        )
        logger.info("Kopf değerleri bulundu: %s", kopf_matches)

    # Pattern 2: "ThAC [g] 18.4"
    thac_pattern = r"ThAC\s*\[g\]\s*([\d\.]+)"
    thac_matches = re.findall(thac_pattern, text, re.IGNORECASE)
    if thac_matches:
        params.append(
            {
                "name": "Göğüs ivmesi (ThAC)",
                "unit": "g",
                "values": thac_matches,
            }
        )
        logger.info("ThAC değerleri bulundu: %s", thac_matches)

    # Pattern 3: "FAC right F [kN] 4.40"
    fac_right_pattern = r"FAC\s+right\s+F\s*\[kN\]\s*([\d\.]+)"
    fac_right_matches = re.findall(fac_right_pattern, text, re.IGNORECASE)
    if fac_right_matches:
        params.append(
            {
                "name": "Sağ femur kuvveti (FAC right)",
                "unit": "kN",
                "values": fac_right_matches,
            }
        )
        logger.info("FAC right değerleri bulundu: %s", fac_right_matches)

    # Pattern 4: "FAC left F [kN] 4.82"
    fac_left_pattern = r"FAC\s+left\s+F\s*\[kN\]\s*([\d\.]+)"
    fac_left_matches = re.findall(fac_left_pattern, text, re.IGNORECASE)
    if fac_left_matches:
        params.append(
            {
                "name": "Sol femur kuvveti (FAC left)",
                "unit": "kN",
                "values": fac_left_matches,
            }
        )
        logger.info("FAC left değerleri bulundu: %s", fac_left_matches)

    # Pattern 5: "HAC, [120.1, 146.05 ms] 161.18"
    hac_pattern = r"HAC,\s*\[[\d\.]+,\s*[\d\.]+\s*ms\]\s*([\d\.]+)"
    hac_matches = re.findall(hac_pattern, text, re.IGNORECASE)
    if hac_matches:
        params.append(
            {
                "name": "HAC (Head Acceleration Criterion)",
                "unit": "",
                "values": hac_matches,
            }
        )
        logger.info("HAC değerleri bulundu: %s", hac_matches)

    logger.info("Toplam %s parametre grubu bulundu", len(params))
    return params


def format_measurement_params_for_ai(params):
    """
    Measurement params'ı AI için okunabilir formata çevir
    """
    if not params:
        return ""

    lines = ["=== ÖLÇÜM PARAMETRELERİ ===\n"]

    for param in params:
        name = param["name"]
        unit = param["unit"]
        values = param["values"]

        if len(values) == 1:
            lines.append(f"• {name}: {values[0]} {unit}")
        elif len(values) == 2:
            lines.append(f"• {name}: {values[0]} {unit} ve {values[1]} {unit}")
        else:
            values_str = ", ".join(values[:3])
            lines.append(f"• {name}: {values_str} {unit}")

    return "\n".join(lines)


__all__ = [
    "detect_pdf_format",
    "parse_kielt_format",
    "extract_measurement_params",
    "format_measurement_params_for_ai",
]
