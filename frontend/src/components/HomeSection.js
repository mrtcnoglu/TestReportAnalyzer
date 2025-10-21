import React, { useMemo } from "react";
import UploadForm from "./UploadForm";
import { detectReportType } from "../utils/reportUtils";

const HomeSection = ({ reports, onRefresh, loading, error }) => {
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
        <div className="card-header">
          <h2>PDF Raporlarını Sürükleyin &amp; Bırakın veya Tıklayarak Dosya Seçin</h2>
          {loading && <span className="badge badge-info">Raporlar yükleniyor...</span>}
        </div>
        {error && <div className="alert alert-error">{error}</div>}
        <UploadForm onUploadSuccess={onRefresh} />
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
    </div>
  );
};

export default HomeSection;
