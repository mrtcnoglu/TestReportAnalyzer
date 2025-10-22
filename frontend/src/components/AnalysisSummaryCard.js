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

const buildStructuredHeading = (sectionKey) => {
  const tr = STRUCTURED_SECTION_LABELS.tr?.[sectionKey] || sectionKey;
  const en = STRUCTURED_SECTION_LABELS.en?.[sectionKey] || sectionKey;
  const de = STRUCTURED_SECTION_LABELS.de?.[sectionKey] || sectionKey;
  return `${tr} / ${en} / ${de}`;
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
                                  {renderLocalizedParagraph(
                                    content.conditions,
                                    languageKey,
                                    "muted-text"
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
                              <div className="analysis-structured-grid">
                                {Object.entries(item.structured_sections)
                                  .filter(([, value]) => Boolean(value))
                                  .map(([sectionKey, value]) => (
                                    <div
                                      className="analysis-structured-item"
                                      key={`${analysis.id}-${item.filename}-${sectionKey}`}
                                    >
                                      <h5>{buildStructuredHeading(sectionKey)}</h5>
                                      <p>{Array.isArray(value) ? value.join(" ") : value}</p>
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
