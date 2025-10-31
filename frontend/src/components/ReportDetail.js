import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getReportById } from "../api";

function ReportDetail() {
  const { id } = useParams();
  const [report, setReport] = useState(null);
  const [detailedAnalysis, setDetailedAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const reportData = await getReportById(id);
        setReport(reportData.report);
        setDetailedAnalysis(reportData.detailed_analysis);
      } catch (err) {
        console.error("Hata:", err);
        setError("Rapor detayları alınamadı.");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id]);

  if (loading) {
    return <div>Yükleniyor...</div>;
  }

  if (error) {
    return <div className="error-text">{error}</div>;
  }

  if (!report) {
    return <div>Rapor bulunamadı.</div>;
  }

  return (
    <div className="report-detail">
      <div className="summary-card">
        <h2>{report.filename}</h2>
        <p>Tarih: {new Date(report.upload_date).toLocaleString("tr-TR")}</p>
        <p>
          Toplam: {report.total_tests}, Başarılı: {report.passed_tests}, Başarısız: {report.failed_tests}
        </p>
      </div>

      {detailedAnalysis?.test_conditions && (
        <div className="analysis-card">
          <h3>📋 Test Koşulları</h3>
          <p className="ai-summary">{detailedAnalysis.test_conditions}</p>
          {detailedAnalysis.test_conditions.length < 50 && (
            <small style={{ color: "#999" }}>
              ⚠️ Analiz eksik - backend log'larını kontrol edin
            </small>
          )}
        </div>
      )}

      {detailedAnalysis?.graphs && (
        <div className="analysis-card">
          <h3>📊 Grafik ve Ölçüm Verileri</h3>
          <p className="ai-summary">{detailedAnalysis.graphs}</p>
          {detailedAnalysis.graphs.includes("bulunamadı") && (
            <small style={{ color: "#f59e0b" }}>
              ⚠️ Grafik verisi parse edilemedi
            </small>
          )}
        </div>
      )}

      <div className="tests-section">
        <h3>Test Sonuçları</h3>
        {report.tests && report.tests.length > 0 ? (
          report.tests.map((test, idx) => (
            <div key={idx} className={`test-item ${test.status.toLowerCase()}`}>
              <strong>{test.name || test.test_name || `Test ${idx + 1}`}</strong>
              <span className={`badge-${test.status.toLowerCase()}`}>
                {test.status === "PASS" ? "✓ Başarılı" : "✗ Başarısız"}
              </span>
              {test.status === "FAIL" && (
                <div className="test-details">
                  <p>
                    <em>Neden:</em> {test.failure_reason || test.error_message || "Belirtilmedi"}
                  </p>
                  <p>
                    <em>Öneri:</em> {test.suggested_fix || "Öneri sağlanmadı"}
                  </p>
                </div>
              )}
            </div>
          ))
        ) : (
          <p>Test kaydı bulunamadı.</p>
        )}
      </div>
    </div>
  );
}

export default ReportDetail;
