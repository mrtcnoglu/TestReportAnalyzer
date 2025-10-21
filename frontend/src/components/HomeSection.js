import React, { useCallback, useMemo, useState } from "react";
import UploadForm from "./UploadForm";
import { resetAllData } from "../api";
import { detectReportType } from "../utils/reportUtils";

const HomeSection = ({ reports, onRefresh, loading, error, analysisEngine }) => {
  const [analysisSummaries, setAnalysisSummaries] = useState([]);
  const [analysisInfo, setAnalysisInfo] = useState(null);
  const [resetStatus, setResetStatus] = useState(null);
  const [isResetting, setIsResetting] = useState(false);

  const metrics = useMemo(() => {
    const totals = reports.reduce(
      (acc, report) => {
        const total = Number(report.total_tests ?? 0);
        const passed = Number(report.passed_tests ?? 0);
        const failed = Number(report.failed_tests ?? 0);
        const uploadDate = report.upload_date ? new Date(report.upload_date) : null;
        const isWithin24h = uploadDate
          ? Date.now() - uploadDate.getTime() <= 24 * 60 * 60 * 1000
          : false;

        acc.totalAnalyses += 1;
        acc.totalPassed += passed;
        acc.totalFailed += failed;
        acc.totalTestsLast24h += isWithin24h ? total : 0;
        acc.types.add(detectReportType(report.filename));
        return acc;
      },
      {
        totalAnalyses: 0,
        totalPassed: 0,
        totalFailed: 0,
        totalTestsLast24h: 0,
        types: new Set(),
      }
    );

    return {
      totalAnalyses: totals.totalAnalyses,
      totalPassed: totals.totalPassed,
      totalFailed: totals.totalFailed,
      totalTestsLast24h: totals.totalTestsLast24h,
      supportedTypes: Array.from(totals.types),
    };
  }, [reports]);

  const clearAnalysisSummary = useCallback(() => {
    setAnalysisSummaries([]);
    setAnalysisInfo(null);
  }, []);

  const handleAnalysisComplete = useCallback(
    (result) => {
      if (!result) {
        clearAnalysisSummary();
        return;
      }

      setAnalysisSummaries(result.summaries ?? []);
      setAnalysisInfo({
        message: result.message ?? "",
        engine: result.engine ?? (analysisEngine === "claude" ? "Claude" : "ChatGPT"),
      });
    },
    [analysisEngine, clearAnalysisSummary]
  );

  const handleResetAll = useCallback(async () => {
    setIsResetting(true);
    setResetStatus(null);
    try {
      const response = await resetAllData();
      setResetStatus({ type: "success", message: response.message });
      clearAnalysisSummary();
      if (typeof onRefresh === "function") {
        await onRefresh();
      }
    } catch (resetError) {
      const message =
        resetError?.response?.data?.error || "Veriler sıfırlanırken bir hata oluştu. Lütfen tekrar deneyin.";
      setResetStatus({ type: "error", message });
    } finally {
      setIsResetting(false);
    }
  }, [onRefresh, clearAnalysisSummary]);

  return (
    <div className="home-section">
      <div className="metrics-grid">
        <div className="metric-card">
          <span className="metric-label">
            <span className="metric-icon">📊</span>Toplam Analiz
          </span>
          <span className="metric-value">{metrics.totalAnalyses}</span>
        </div>
        <div className="metric-card">
          <span className="metric-label">
            <span className="metric-icon metric-icon-success">✔</span>Başarılı Testler
          </span>
          <span className="metric-value">{metrics.totalPassed}</span>
        </div>
        <div className="metric-card">
          <span className="metric-label">
            <span className="metric-icon metric-icon-danger">✖</span>Başarısız Testler
          </span>
          <span className="metric-value">{metrics.totalFailed}</span>
        </div>
        <div className="metric-card">
          <span className="metric-label">
            <span className="metric-icon">⏳</span>Son 24 Saatte Analiz Edilen Test
          </span>
          <span className="metric-value">{metrics.totalTestsLast24h}</span>
        </div>
      </div>

      <div className="card upload-card">
        {loading && (
          <div className="card-header">
            <span className="badge badge-info">Raporlar yükleniyor...</span>
          </div>
        )}
        {error && <div className="alert alert-error">{error}</div>}
        <UploadForm
          onUploadSuccess={onRefresh}
          analysisEngine={analysisEngine}
          onAnalysisComplete={handleAnalysisComplete}
          onClearAnalysis={clearAnalysisSummary}
        />
      </div>
      <div className="card supported-types-card">
        <div className="supported-types">
          <h3>Desteklenen PDF Türleri</h3>
          <ul>
            <li>ECE R80 Darbe Testi Raporu</li>
            <li>ECE R10 EMC Test Raporu</li>
          </ul>
        </div>
      </div>
      <div className="card reset-card">
        <button
          type="button"
          className="button button-danger reset-button"
          onClick={handleResetAll}
          disabled={isResetting}
        >
          ❗ Bütün Verileri Sıfırla
        </button>
        <p className="muted-text reset-help">Yüklü raporlar, analizler ve test sonuçları sıfırlanır.</p>
        {resetStatus && (
          <div
            className={`alert ${
              resetStatus.type === "success"
                ? "alert-success"
                : resetStatus.type === "error"
                ? "alert-error"
                : "alert-info"
            }`}
          >
            {resetStatus.message}
          </div>
        )}
      </div>
      <div className="card analysis-summary-card">
        <h3>Analiz Özeti</h3>
        <p className="muted-text">
          {analysisInfo?.message
            ? `${analysisInfo.engine} tarafından oluşturulan en güncel özet aşağıdadır.`
            : "AI analizi gerçekleştirmek için PDF seçip 'AI İle Analiz Et' butonuna tıklayın."}
        </p>
        {analysisInfo?.message && <div className="alert alert-info">{analysisInfo.message}</div>}
        {analysisSummaries.length === 0 ? (
          <p className="muted-text">Gösterilecek bir analiz özeti bulunmuyor.</p>
        ) : (
          <ul className="analysis-summary-list">
            {analysisSummaries.map((item) => (
              <li key={item.filename}>
                <div className="analysis-summary-header">
                  <span className="analysis-summary-file">{item.filename}</span>
                  <span className="analysis-summary-metrics">
                    {item.passed_tests}/{item.total_tests} PASS · {item.failed_tests} FAIL
                  </span>
                </div>
                <p>{item.summary}</p>
                {item.failures?.length > 0 && (
                  <ul className="analysis-failure-list">
                    {item.failures.map((failure) => (
                      <li key={`${item.filename}-${failure.test_name}`}>
                        <strong>{failure.test_name}:</strong> {failure.failure_reason || "Açıklama yok."}
                        {failure.suggested_fix && <span> — Öneri: {failure.suggested_fix}</span>}
                      </li>
                    ))}
                  </ul>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default HomeSection;
