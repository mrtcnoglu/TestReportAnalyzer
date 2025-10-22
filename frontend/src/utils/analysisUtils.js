export const LANGUAGE_LABELS = {
  tr: "Türkçe",
  en: "English",
  de: "Deutsch",
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
