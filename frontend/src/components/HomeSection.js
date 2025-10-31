import React, { useCallback, useMemo, useState } from "react";
import UploadForm from "./UploadForm";
import AnalysisSummaryCard from "./AnalysisSummaryCard";
import { resetAllData } from "../api";
import { getReportStatusLabel } from "../utils/reportUtils";

const HomeSection = ({
  reports,
  onRefresh,
  loading,
  error,
  analysisEngine,
  recentAnalyses = [],
  onAnalysisComplete,
  onClearAnalyses,
}) => {
  const [resetStatus, setResetStatus] = useState(null);
  const [isResetting, setIsResetting] = useState(false);

  const metrics = useMemo(() => {
    const totals = reports.reduce(
      (acc, report) => {
        const status = getReportStatusLabel(report);

        if (status !== "Analiz Bekleniyor") {
          acc.analysedFiles += 1;
          acc.totalAnalyses += 1;

          if (status === "Başarılı") {
            acc.successfulAnalyses += 1;
          }
        }

        return acc;
      },
      {
        analysedFiles: 0,
        successfulAnalyses: 0,
        totalAnalyses: 0,
      }
    );

    return {
      analysedFiles: totals.analysedFiles,
      successfulAnalyses: totals.successfulAnalyses,
      totalAnalyses: totals.totalAnalyses,
    };
  }, [reports]);

  const handleAnalysisComplete = useCallback(
    (result) => onAnalysisComplete?.(result, { source: "home", engineKey: analysisEngine }),
    [analysisEngine, onAnalysisComplete]
  );

  const handleResetAll = useCallback(async () => {
    setIsResetting(true);
    setResetStatus(null);
    try {
      const response = await resetAllData();
      setResetStatus({ type: "success", message: response.message });
      onClearAnalyses?.();
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
  }, [onRefresh, onClearAnalyses]);

  return (
    <div className="home-section">
      <div className="metrics-grid">
        <div className="metric-card">
          <span className="metric-label">
            <span className="metric-icon">📁</span>Analiz Edilen Dosya
          </span>
          <span className="metric-value">{metrics.analysedFiles}</span>
        </div>
        <div className="metric-card">
          <span className="metric-label">
            <span className="metric-icon metric-icon-success">✔</span>Başarılı Analizler
          </span>
          <span className="metric-value">{metrics.successfulAnalyses}</span>
        </div>
        <div className="metric-card">
          <span className="metric-label">
            <span className="metric-icon">📊</span>Toplam Analiz
          </span>
          <span className="metric-value">{metrics.totalAnalyses}</span>
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
      <AnalysisSummaryCard
        analyses={recentAnalyses}
        title="Analiz Özeti"
        introText={
          recentAnalyses.length > 0
            ? "Son gerçekleştirilen en fazla iki AI analizi aşağıda listelenmiştir."
            : "AI analizi gerçekleştirmek için PDF seçip 'PDF Yükle ve AI ile Analiz Et' butonuna tıklayın."
        }
      />
    </div>
  );
};

export default HomeSection;
