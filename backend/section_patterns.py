# -*- coding: utf-8 -*-
"""Regex patterns for detecting structured sections inside PDF reports."""
from __future__ import annotations

SECTION_PATTERNS = {
    "test_conditions": {
        "tr": [
            r"Test Koşulları",
            r"Test Şartları",
            r"Deney Koşulları",
        ],
        "en": [
            r"Test Conditions",
            r"Testing Conditions",
            r"Test Parameters",
        ],
        "de": [
            r"Testbedingungen",
            r"Prüfbedingungen",
            r"Versuchsbedingungen",
        ],
    },
    "graphs": {
        "tr": [
            r"Grafikler",
            r"Şekiller",
            r"Diyagramlar",
        ],
        "en": [
            r"Graphs",
            r"Charts",
            r"Figures",
            r"Diagrams",
        ],
        "de": [
            r"Diagramme",
            r"Grafiken",
            r"Abbildungen",
        ],
    },
    "results": {
        "tr": [
            r"Sonuçlar",
            r"Test Sonuçları",
            r"Bulgular",
        ],
        "en": [
            r"Results",
            r"Test Results",
            r"Findings",
        ],
        "de": [
            r"Ergebnisse",
            r"Testergebnisse",
            r"Resultate",
        ],
    },
    "summary": {
        "tr": [
            r"Özet",
            r"Genel Özet",
            r"Sonuç",
        ],
        "en": [
            r"Summary",
            r"Conclusion",
            r"Overview",
        ],
        "de": [
            r"Zusammenfassung",
            r"Übersicht",
            r"Fazit",
        ],
    },
}
