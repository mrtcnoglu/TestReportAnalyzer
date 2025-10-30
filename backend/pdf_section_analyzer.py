# -*- coding: utf-8 -*-
"""Utilities for detecting structured sections inside PDF report text."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

try:  # pragma: no cover - allow running as a script without a package context
    from .section_patterns import SECTION_PATTERNS
except ImportError:  # pragma: no cover
    from section_patterns import SECTION_PATTERNS  # type: ignore


SUBSECTION_PATTERNS: Dict[str, Dict[str, str]] = {
    "sled_deceleration": {
        "de": r"Schlittenverzögerung:",
        "en": r"Sled\s+deceleration:",
        "tr": r"Kızak\s+(?:gecikmesi|yavaşlaması):",
    },
    "load_values": {
        "de": r"Belastungswerte:",
        "en": r"Load\s+values:",
        "tr": r"Yük\s+değerleri:",
    },
    "photo_documentation": {
        "de": r"Fotodokumentation:",
        "en": r"Photo\s+documentation:",
        "tr": r"Fotoğraf\s+dokümantasyonu:",
    },
    "test_setup": {
        "de": r"Abb\.\s*\d+:\s*(?:Aufbau|Setup)",
        "en": r"Fig\.\s*\d+:\s*(?:Setup|Configuration)",
        "tr": r"Şekil\s*\d+:\s*(?:Kurulum|Yapılandırma)",
    },
}


@dataclass(frozen=True)
class SectionMarker:
    """Represents a detected section heading inside the PDF text."""

    start: int
    end: int
    section: str
    language: str
    heading: str


def _ensure_text_string(text_or_dict: object) -> str:
    """Return a plain string from either raw text or extraction dict results."""

    if isinstance(text_or_dict, dict):
        structured = text_or_dict.get("structured_text")
        if structured:
            return str(structured)
        fallback = text_or_dict.get("text")
        if fallback:
            return str(fallback)
        return ""
    return str(text_or_dict or "")


def _compile_heading_patterns(patterns: Iterable[str]) -> str:
    escaped = [f"(?:{pattern})" for pattern in patterns]
    return r"|".join(escaped)


def _iter_section_markers(text: str | dict) -> List[SectionMarker]:
    markers: List[SectionMarker] = []
    text = _ensure_text_string(text)
    if not text:
        return markers

    for section_key, language_map in SECTION_PATTERNS.items():
        for language, pattern_list in language_map.items():
            if not pattern_list:
                continue
            combined = _compile_heading_patterns(pattern_list)
            regex = re.compile(rf"^(?P<heading>\s*(?:{combined})\s*)$", re.IGNORECASE | re.MULTILINE)
            for match in regex.finditer(text):
                heading = (match.group("heading") or "").strip()
                markers.append(
                    SectionMarker(
                        start=match.start(),
                        end=match.end(),
                        section=section_key,
                        language=language,
                        heading=heading,
                    )
                )
    markers.sort(key=lambda item: item.start)
    return markers


def extract_section(text: str | dict, start_pattern: str, end_pattern: Optional[str] = None) -> str:
    """Extract a section using explicit start and optional end regex patterns."""

    text = _ensure_text_string(text)
    if not text:
        return ""

    start_regex = re.compile(start_pattern, re.IGNORECASE | re.MULTILINE)
    start_match = start_regex.search(text)
    if not start_match:
        return ""

    start_index = start_match.end()
    newline_index = text.find("\n", start_index)
    if newline_index != -1:
        start_index = newline_index + 1

    end_index = len(text)
    if end_pattern:
        end_regex = re.compile(end_pattern, re.IGNORECASE | re.MULTILINE)
        end_match = end_regex.search(text, start_index)
        if end_match:
            end_index = end_match.start()

    return text[start_index:end_index].strip()


def identify_section_language(text: str | dict) -> str:
    """Best-effort language detection based on known section headings."""

    text = _ensure_text_string(text)
    if not text:
        return "tr"

    scores = {"tr": 0, "en": 0, "de": 0}
    lower_text = text.lower()
    for section_map in SECTION_PATTERNS.values():
        for language, pattern_list in section_map.items():
            for pattern in pattern_list:
                if not pattern:
                    continue
                try:
                    occurrences = len(re.findall(pattern, lower_text, re.IGNORECASE))
                except re.error:
                    occurrences = 0
                scores[language] = scores.get(language, 0) + occurrences

    best_language = max(scores, key=scores.get)
    if scores[best_language] == 0:
        return "tr"
    return best_language


def detect_sections(text: str | dict) -> Dict[str, str]:
    """Detect major sections of a PDF report and return their contents."""

    text = _ensure_text_string(text)
    sections = {
        "header": "",
        "summary": "",
        "test_conditions": "",
        "graphs": "",
        "results": "",
        "detailed_data": "",
    }

    if not text:
        return sections

    markers = _iter_section_markers(text)
    if not markers:
        sections["header"] = text.strip()
        sections["detailed_data"] = text.strip()
        return sections

    header_start = text[: markers[0].start].strip()
    sections["header"] = header_start

    for index, marker in enumerate(markers):
        start_index = marker.end
        newline_index = text.find("\n", start_index)
        if newline_index != -1:
            start_index = newline_index + 1
        end_index = len(text)
        for next_marker in markers[index + 1 :]:
            if next_marker.start > marker.start:
                end_index = next_marker.start
                break
        content = text[start_index:end_index].strip()
        if marker.section in sections and not sections[marker.section]:
            sections[marker.section] = content

    last_marker = markers[-1]
    tail_content = text[last_marker.end :].strip()
    if tail_content:
        if not sections.get(last_marker.section):
            sections[last_marker.section] = tail_content
        else:
            sections["detailed_data"] = tail_content

    # Fill detailed data with remainder if still empty
    if not sections["detailed_data"]:
        consumed_segments: List[str] = []
        for key in ["summary", "test_conditions", "graphs", "results"]:
            if sections.get(key):
                consumed_segments.append(sections[key])
        remainder = text
        for segment in consumed_segments:
            remainder = remainder.replace(segment, "")
        if remainder.strip():
            sections["detailed_data"] = remainder.strip()

    if not sections["summary"] and sections["header"]:
        sections["summary"] = sections["header"]

    return sections


def detect_subsections(text: str | dict) -> Dict[str, str]:
    """Detect known subsections within a larger section text."""

    text = _ensure_text_string(text)
    if not text:
        return {}

    language = identify_section_language(text)
    markers: List[SectionMarker] = []

    for key, language_map in SUBSECTION_PATTERNS.items():
        pattern = language_map.get(language) or language_map.get("en")
        if not pattern:
            continue
        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error:
            continue
        for match in regex.finditer(text):
            markers.append(
                SectionMarker(
                    start=match.start(),
                    end=match.end(),
                    section=key,
                    language=language,
                    heading=match.group(0),
                )
            )

    if not markers:
        return {}

    markers.sort(key=lambda item: item.start)
    subsections: Dict[str, str] = {}

    for index, marker in enumerate(markers):
        start_index = marker.start
        end_index = len(text)
        for next_marker in markers[index + 1 :]:
            if next_marker.start > marker.start:
                end_index = next_marker.start
                break
        content = text[start_index:end_index].strip()
        if content:
            subsections[marker.section] = content

    return subsections
