export const LANGUAGE_LABELS = {
  tr: "Türkçe",
  en: "English",
  de: "Deutsch",
};

export const SUMMARY_SECTION_LABELS = {
  tr: {
    summary: "Genel Özet",
    conditions: "Test Koşulları",
    improvements: "İyileştirme Önerileri",
    highlights: "Öne Çıkan Bulgular",
    technical: "Teknik Analiz Detayları",
    failures: "Kritik Testler",
  },
  en: {
    summary: "Summary",
    conditions: "Test Conditions",
    improvements: "Improvement Suggestions",
    highlights: "Key Highlights",
    technical: "Technical Analysis Details",
    failures: "Critical Tests",
  },
  de: {
    summary: "Zusammenfassung",
    conditions: "Testbedingungen",
    improvements: "Verbesserungsvorschläge",
    highlights: "Wesentliche Erkenntnisse",
    technical: "Technische Analyse",
    failures: "Kritische Tests",
  },
};

export const STRUCTURED_SECTION_LABELS = {
  tr: {
    graphs: "Grafikler",
    conditions: "Test Koşulları",
    results: "Sonuçlar",
    comments: "Uzman Notları",
  },
  en: {
    graphs: "Graphs",
    conditions: "Test Conditions",
    results: "Results",
    comments: "Expert Notes",
  },
  de: {
    graphs: "Diagramme",
    conditions: "Testbedingungen",
    results: "Ergebnisse",
    comments: "Expertenhinweise",
  },
};

export const COMPARISON_SECTION_LABELS = {
  tr: { overview: "Karşılaştırma Özeti", details: "Teknik Farklar" },
  en: { overview: "Comparison Overview", details: "Technical Differences" },
  de: { overview: "Vergleichsübersicht", details: "Technische Unterschiede" },
};

export const COMPARISON_EMPTY_MESSAGES = {
  tr: "Farklılık bulunamadı.",
  en: "No differing points were identified.",
  de: "Es wurden keine Unterschiede festgestellt.",
};

export const resolveEngineLabel = (engineKey) => {
  if (!engineKey) {
    return "ChatGPT";
  }

  const normalized = engineKey.toString().toLowerCase();

  if (normalized.includes("claude")) {
    return "Claude";
  }

  if (normalized.includes("gpt")) {
    return "ChatGPT";
  }

  return engineKey;
};

export const createAnalysisEntry = (result, { engineKey, source } = {}) => {
  if (!result) {
    return null;
  }

  const timestamp = new Date();
  const entry = {
    id: `${timestamp.getTime()}-${Math.random().toString(16).slice(2, 8)}`,
    timestamp: timestamp.toISOString(),
    engine: result.engine ?? resolveEngineLabel(engineKey),
    message: result.message ?? "",
    summaries: Array.isArray(result.summaries) ? result.summaries : [],
  };

  if (source) {
    entry.source = source;
  }

  return entry;
};

export const formatAnalysisTimestamp = (timestamp) => {
  if (!timestamp) {
    return "";
  }

  const date = typeof timestamp === "string" ? new Date(timestamp) : timestamp;

  if (Number.isNaN(date.getTime())) {
    return "";
  }

  return date.toLocaleString("tr-TR", {
    dateStyle: "short",
    timeStyle: "short",
  });
};
