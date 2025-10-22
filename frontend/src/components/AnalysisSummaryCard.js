import React from "react";
import {
  formatAnalysisTimestamp,
  LANGUAGE_LABELS,
  SUMMARY_SECTION_LABELS,
  STRUCTURED_SECTION_LABELS,
} from "../utils/analysisUtils";

const PLACEHOLDER_TEXT = {
  tr: "İçerik bulunamadı.",
  en: "No data available.",
  de: "Keine Daten vorhanden.",
};

const LANGUAGE_ORDER = ["tr", "en", "de"];

const resolveLocalizedLabels = (languageKey, content) => {
  const fallback = SUMMARY_SECTION_LABELS[languageKey] || SUMMARY_SECTION_LABELS.tr;
  const provided = (content && content.labels) || {};

  return {
    summary: (provided.summary || fallback.summary || "").trim(),
    conditions: (provided.conditions || fallback.conditions || "").trim(),
    improvements: (provided.improvements || fallback.improvements || "").trim(),
    highlights: (provided.highlights || fallback.highlights || "").trim(),
    technical: (provided.technical || fallback.technical || "").trim(),
    failures: (provided.failures || fallback.failures || "").trim(),
  };
};

const getStructuredLabel = (sectionKey, languageKey) => {
  const languageLabels = STRUCTURED_SECTION_LABELS[languageKey];
  if (languageLabels && languageLabels[sectionKey]) {
    return languageLabels[sectionKey];
  }

  const fallback =
    STRUCTURED_SECTION_LABELS.tr?.[sectionKey] ||
    STRUCTURED_SECTION_LABELS.en?.[sectionKey] ||
    STRUCTURED_SECTION_LABELS.de?.[sectionKey] ||
    sectionKey;

  return fallback;
};

const normaliseStructuredValue = (rawValue, languageKey) => {
  if (!rawValue) {
    return "";
  }

  if (typeof rawValue === "string") {
    return rawValue.trim();
  }

  if (Array.isArray(rawValue)) {
    return rawValue
      .map((item) => String(item || "").trim())
      .filter((entry) => entry.length > 0)
      .join(" ");
  }

  if (typeof rawValue === "object") {
    const direct = rawValue[languageKey];
    if (typeof direct === "string") {
      return direct.trim();
    }
    if (Array.isArray(direct)) {
      return direct
        .map((item) => String(item || "").trim())
        .filter((entry) => entry.length > 0)
        .join(" ");
    }

    const fallbackValue = Object.values(rawValue).find((value) => {
      if (typeof value === "string") {
        return value.trim().length > 0;
      }
      if (Array.isArray(value)) {
        return value.some((item) => String(item || "").trim().length > 0);
      }
      return false;
    });

    if (typeof fallbackValue === "string") {
      return fallbackValue.trim();
    }

    if (Array.isArray(fallbackValue)) {
      return fallbackValue
        .map((item) => String(item || "").trim())
        .filter((entry) => entry.length > 0)
        .join(" ");
    }
  }

  return String(rawValue).trim();
};

const hasStructuredContent = (rawValue) => {
  if (!rawValue) {
    return false;
  }

  if (typeof rawValue === "string") {
    return rawValue.trim().length > 0;
  }

  if (Array.isArray(rawValue)) {
    return rawValue.some((item) => String(item || "").trim().length > 0);
  }

  if (typeof rawValue === "object") {
    return Object.values(rawValue).some((value) => {
      if (typeof value === "string") {
        return value.trim().length > 0;
      }
      if (Array.isArray(value)) {
        return value.some((item) => String(item || "").trim().length > 0);
      }
      return false;
    });
  }

  return false;
};

const parseConditionEntries = (text) => {
  if (typeof text !== "string") {
    return [];
  }

  const segments = text
    .replace(/\r/g, "")
    .split(/[\n;]+/)
    .map((segment) => segment.replace(/^[-•*]+\s*/, "").trim())
    .filter(Boolean);

  if (!segments.length) {
    const cleaned = text.trim();
    return cleaned ? [{ type: "text", value: cleaned }] : [];
  }

  return segments.map((segment) => {
    const colonIndex = segment.indexOf(":");
    if (colonIndex > 0 && colonIndex < segment.length - 1) {
      return {
        type: "kv",
        label: segment.slice(0, colonIndex).trim(),
        value: segment.slice(colonIndex + 1).trim(),
      };
    }

    return { type: "text", value: segment };
  });
};

const renderConditionsContent = (value, languageKey) => {
  const entries = parseConditionEntries(value);

  if (!entries.length) {
    return (
      <p className="muted-text">
        {PLACEHOLDER_TEXT[languageKey] || PLACEHOLDER_TEXT.tr}
      </p>
    );
  }

  const keyValueEntries = entries.filter((entry) => entry.type === "kv");
  const textEntries = entries.filter((entry) => entry.type !== "kv");

  return (
    <div className="analysis-conditions-content">
      {keyValueEntries.length > 0 ? (
        <dl className="analysis-conditions-grid">
          {keyValueEntries.map((entry, index) => (
            <div className="analysis-condition-pair" key={`condition-kv-${index}`}>
              <dt>{entry.label}</dt>
              <dd>{entry.value}</dd>
            </div>
          ))}
        </dl>
      ) : null}
      {textEntries.length > 0 ? (
        <ul className="analysis-conditions-list">
          {textEntries.map((entry, index) => (
            <li key={`condition-text-${index}`}>{entry.value}</li>
          ))}
        </ul>
      ) : null}
    </div>
  );
};

const renderLocalizedParagraph = (value, languageKey, className = "") => {
  const text = typeof value === "string" ? value.trim() : "";
  const classes = className ? [className] : [];

  if (text) {
    return <p className={classes.join(" ")}>{text}</p>;
  }

  classes.push("muted-text");
  return (
    <p className={classes.join(" ").trim()}>
      {PLACEHOLDER_TEXT[languageKey] || PLACEHOLDER_TEXT.tr}
    </p>
  );
};

const AnalysisSummaryCard = ({
  title = "Analiz Özeti",
  analyses = [],
  introText = "",
  emptyMessage = "Gösterilecek bir analiz özeti bulunmuyor.",
  headerActions = null,
  collapsed = false,
}) => {
  const hasAnalyses = analyses.length > 0;

  return (
    <div className={`card analysis-summary-card ${collapsed ? "analysis-summary-card-collapsed" : ""}`}>
      <div className="analysis-summary-card-header">
        <h3>{title}</h3>
        {headerActions && <div className="analysis-summary-card-actions">{headerActions}</div>}
      </div>
      {!collapsed && introText && <p className="muted-text">{introText}</p>}
      {collapsed ? null : !hasAnalyses ? (
        <p className="muted-text">{emptyMessage}</p>
      ) : (
        <ul className="analysis-run-list">
          {analyses.map((analysis) => (
            <li key={analysis.id} className="analysis-run-item">
              <div className="analysis-run-meta">
                <span className="analysis-summary-engine">{analysis.engine}</span>
                {analysis.timestamp && (
                  <span className="analysis-summary-time">
                    {formatAnalysisTimestamp(analysis.timestamp)}
                  </span>
                )}
              </div>
              {analysis.message && (
                <div className="alert alert-info analysis-run-message">{analysis.message}</div>
              )}
              {analysis.summaries?.length ? (
                <ul className="analysis-summary-list">
                  {analysis.summaries.map((item) => {
                    const localizedEntries = LANGUAGE_ORDER.map((languageKey) => [
                      languageKey,
                      (item.localized_summaries && item.localized_summaries[languageKey]) || {},
                    ]);
                    const baseLabels = resolveLocalizedLabels(
                      "tr",
                      item.localized_summaries?.tr || {}
                    );

                    return (
                      <li key={`${analysis.id}-${item.filename}`}>
                        <div className="analysis-summary-header">
                          <span className="analysis-summary-file">{item.filename}</span>
                          <span className="analysis-summary-metrics">
                            {item.passed_tests}/{item.total_tests} PASS · {item.failed_tests} FAIL
                          </span>
                        </div>
                        {item.report_type_label && (
                          <p className="muted-text">
                            Analiz edilen test türü: {item.report_type_label}
                          </p>
                        )}
                        <div className="analysis-language-accordion">
                          {localizedEntries.map(([languageKey, content]) => {
                            const languageLabels = resolveLocalizedLabels(languageKey, content);
                            return (
                              <details
                                className="analysis-language-panel"
                                key={`${analysis.id}-${item.filename}-${languageKey}`}
                              >
                                <summary className="analysis-language-summary">
                                  <span className="analysis-language-chip">
                                    {LANGUAGE_LABELS[languageKey] || languageKey.toUpperCase()}
                                  </span>
                                  <span className="analysis-language-heading">
                                    {languageLabels.summary}
                                  </span>
                                </summary>
                                <div className="analysis-language-content">
                                  <h4>{languageLabels.summary}</h4>
                                  {renderLocalizedParagraph(content.summary, languageKey)}
                                  <h5>{languageLabels.conditions}</h5>
                                  {renderConditionsContent(
                                    content.conditions,
                                    languageKey
                                  )}
                                  <h5>{languageLabels.improvements}</h5>
                                  {renderLocalizedParagraph(
                                    content.improvements,
                                    languageKey,
                                    "muted-text"
                                  )}
                                </div>
                              </details>
                            );
                          })}
                        </div>
                        <details className="analysis-technical-block">
                          <summary>{baseLabels.technical}</summary>
                          <div className="analysis-technical-content">
                            {item.condition_evaluation && (
                              <p className="analysis-technical-note">{item.condition_evaluation}</p>
                            )}
                            {item.improvement_overview && (
                              <p className="analysis-technical-note">{item.improvement_overview}</p>
                            )}
                            {item.structured_sections && (
                              <div className="analysis-structured-sections">
                                {Object.entries(item.structured_sections)
                                  .filter(([, value]) => hasStructuredContent(value))
                                  .map(([sectionKey, value]) => (
                                    <div
                                      className="analysis-structured-section"
                                      key={`${analysis.id}-${item.filename}-${sectionKey}`}
                                    >
                                      <h5 className="analysis-structured-section-title">
                                        {getStructuredLabel(sectionKey, "tr")}
                                      </h5>
                                      <div className="analysis-structured-language-grid">
                                        {LANGUAGE_ORDER.map((languageKey) => {
                                          const sectionLabel = getStructuredLabel(
                                            sectionKey,
                                            languageKey
                                          );
                                          const sectionContent = normaliseStructuredValue(
                                            value,
                                            languageKey
                                          );

                                          return (
                                            <div
                                              className="analysis-structured-language-card"
                                              key={`${analysis.id}-${item.filename}-${sectionKey}-${languageKey}`}
                                            >
                                              <div className="analysis-structured-language-header">
                                                <span className="analysis-language-chip">
                                                  {LANGUAGE_LABELS[languageKey] ||
                                                    languageKey.toUpperCase()}
                                                </span>
                                                <span className="analysis-structured-language-title">
                                                  {sectionLabel}
                                                </span>
                                              </div>
                                              {sectionContent ? (
                                                <p>{sectionContent}</p>
                                              ) : (
                                                <p className="muted-text">
                                                  {
                                                    PLACEHOLDER_TEXT[languageKey] ||
                                                    PLACEHOLDER_TEXT.tr
                                                  }
                                                </p>
                                              )}
                                            </div>
                                          );
                                        })}
                                      </div>
                                    </div>
                                  ))}
                              </div>
                            )}
                            {item.highlights?.length > 0 && (
                              <div className="analysis-technical-section">
                                <h5>{baseLabels.highlights}</h5>
                                <ul className="analysis-highlights">
                                  {item.highlights.map((highlight, highlightIndex) => (
                                    <li
                                      key={`${analysis.id}-${item.filename}-highlight-${highlightIndex}`}
                                    >
                                      {highlight}
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            {item.failures?.length > 0 && (
                              <div className="analysis-technical-section">
                                <h5>{baseLabels.failures}</h5>
                                <ul className="analysis-failure-list">
                                  {item.failures.map((failure) => (
                                    <li key={`${analysis.id}-${item.filename}-${failure.test_name}`}>
                                      <strong>{failure.test_name}:</strong>{" "}
                                      {failure.failure_reason || "Açıklama yok."}
                                      {failure.suggested_fix && (
                                        <span> — Öneri: {failure.suggested_fix}</span>
                                      )}
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        </details>
                      </li>
                    );
                  })}
                </ul>
              ) : (
                <p className="muted-text">Gösterilecek bir analiz özeti bulunmuyor.</p>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default AnalysisSummaryCard;
