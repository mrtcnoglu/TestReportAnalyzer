import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getDetailedReport, getFailedTests, getReportById } from "../api";
import TestList from "./TestList";

const ReportDetail = () => {
  const { id } = useParams();
  const [report, setReport] = useState(null);
  const [tests, setTests] = useState([]);
  const [failures, setFailures] = useState([]);
  const [detailedAnalysis, setDetailedAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadReport = async () => {
      try {
        const [reportData, failureData, detailedData] = await Promise.all([
          getReportById(id),
          getFailedTests(id),
          getDetailedReport(id),
        ]);
        setReport(reportData.report);
        setTests(reportData.results);
        setFailures(failureData);
        setDetailedAnalysis(detailedData?.detailed_analysis || null);
      } catch (err) {
        setError("Rapor detayları alınırken bir hata oluştu.");
      } finally {
        setLoading(false);
      }
    };

    loadReport();
  }, [id]);

  if (loading) {
    return <p>Yükleniyor...</p>;
  }

  if (error) {
    return (
      <div className="card">
        <p>{error}</p>
        <Link to="/">Rapora geri dön</Link>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="card">
        <p>Rapor bulunamadı.</p>
        <Link to="/">Rapora geri dön</Link>
      </div>
    );
  }

  return (
    <div>
      <div className="card">
        <h2>{report.filename}</h2>
        <p>Yüklenme Tarihi: {new Date(report.upload_date).toLocaleString()}</p>
        <div className="report-stats">
          <span className="status-pill status-pass">PASS: {report.passed_tests}</span>
          <span className="status-pill status-fail">FAIL: {report.failed_tests}</span>
          <span className="status-pill">TOPLAM: {report.total_tests}</span>
        </div>
        <Link to="/">← Listeye dön</Link>
      </div>

      {detailedAnalysis && (
        <div className="analysis-grid">
          {detailedAnalysis.test_conditions && (
            <div className="analysis-card">
              <h3>Test Koşulları</h3>
              <p>{detailedAnalysis.test_conditions}</p>
            </div>
          )}

          {detailedAnalysis.graphs && (
            <div className="analysis-card">
              <h3>Grafikler</h3>
              <p>{detailedAnalysis.graphs}</p>
            </div>
          )}

          {detailedAnalysis.results && (
            <div className="analysis-card">
              <h3>Detaylı Test Sonuçları</h3>
              <pre>{detailedAnalysis.results}</pre>
            </div>
          )}

          {detailedAnalysis.improvements && (
            <div className="analysis-card">
              <h3>İyileştirme Önerileri</h3>
              {(() => {
                const items = detailedAnalysis.improvements
                  .split(/\r?\n/)
                  .map((item) => item.trim())
                  .filter(Boolean);
                if (items.length <= 1) {
                  return <p>{items[0] || detailedAnalysis.improvements}</p>;
                }
                return (
                  <ul>
                    {items.map((item, index) => (
                      <li key={`${item}-${index}`}>{item}</li>
                    ))}
                  </ul>
                );
              })()}
            </div>
          )}
        </div>
      )}

      <h3>Tüm Testler</h3>
      <TestList tests={tests} showAiProvider />

      <h3>Başarısız Testler</h3>
      <TestList tests={failures} showAiProvider />
    </div>
  );
};

export default ReportDetail;
