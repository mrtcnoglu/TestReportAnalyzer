import React from "react";
import { formatAnalysisTimestamp, LANGUAGE_LABELS } from "../utils/analysisUtils";

const SECTION_LABELS = {
  graphs: "Grafikler",
  conditions: "Test Koşulları",
  results: "Sonuçlar",
  comments: "Uzman Notları",
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
                  {analysis.summaries.map((item) => (
                    <li key={`${analysis.id}-${item.filename}`}>
                      <div className="analysis-summary-header">
                        <span className="analysis-summary-file">{item.filename}</span>
                        <span className="analysis-summary-metrics">
                          {item.passed_tests}/{item.total_tests} PASS · {item.failed_tests} FAIL
                        </span>
                      </div>
                      {item.report_type_label && (
                        <p className="muted-text">Analiz edilen test türü: {item.report_type_label}</p>
                      )}
                      <p>{item.summary}</p>
                      {item.condition_evaluation && (
                        <p className="muted-text">{item.condition_evaluation}</p>
                      )}
                      {item.improvement_overview && (
                        <p className="muted-text">{item.improvement_overview}</p>
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
                                <h4>{SECTION_LABELS[sectionKey] || sectionKey}</h4>
                                <p>{Array.isArray(value) ? value.join(" ") : value}</p>
                              </div>
                            ))}
                        </div>
                      )}
                      {item.localized_summaries && (
                        <div className="analysis-localized-grid">
                          {Object.entries(item.localized_summaries).map(([languageKey, content]) => (
                            <div className="analysis-localized-card" key={`${analysis.id}-${item.filename}-${languageKey}`}>
                              <h4>{LANGUAGE_LABELS[languageKey] || languageKey.toUpperCase()}</h4>
                              <p>{content.summary}</p>
                              <p className="muted-text">{content.conditions}</p>
                              <p className="muted-text">{content.improvements}</p>
                            </div>
                          ))}
                        </div>
                      )}
                      {item.highlights?.length > 0 && (
                        <ul className="analysis-highlights">
                          {item.highlights.map((highlight, highlightIndex) => (
                            <li
                              key={`${analysis.id}-${item.filename}-highlight-${highlightIndex}`}
                            >
                              {highlight}
                            </li>
                          ))}
                        </ul>
                      )}
                      {item.failures?.length > 0 && (
                        <ul className="analysis-failure-list">
                          {item.failures.map((failure) => (
                            <li key={`${analysis.id}-${item.filename}-${failure.test_name}`}>
                              <strong>{failure.test_name}:</strong> {failure.failure_reason || "Açıklama yok."}
                              {failure.suggested_fix && (
                                <span> — Öneri: {failure.suggested_fix}</span>
                              )}
                            </li>
                          ))}
                        </ul>
                      )}
                    </li>
                  ))}
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
