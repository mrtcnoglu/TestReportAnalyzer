import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  getDetailedReport,
  getFailedTests,
  getReportById,
  getReportTables,
} from "../api";
import TestList from "./TestList";

const ReportDetail = () => {
  const { id } = useParams();
  const [report, setReport] = useState(null);
  const [tests, setTests] = useState([]);
  const [failures, setFailures] = useState([]);
  const [detailedAnalysis, setDetailedAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tables, setTables] = useState([]);
  const [tablesLoading, setTablesLoading] = useState(false);
  const [tablesError, setTablesError] = useState(null);

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

  const handleFetchTables = async (reportId) => {
    if (!reportId || tablesLoading) {
      return;
    }
    setTablesError(null);
    setTablesLoading(true);
    try {
      const tableResponse = await getReportTables(reportId);
      setTables(tableResponse.tables || []);
    } catch (fetchError) {
      setTablesError("Tablo verileri alınamadı.");
    } finally {
      setTablesLoading(false);
    }
  };

  let parsedStructuredData = null;
  if (report?.structured_data) {
    try {
      parsedStructuredData = JSON.parse(report.structured_data);
    } catch (parseError) {
      parsedStructuredData = null;
    }
  }

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

      {report.table_count > 0 && (
        <div className="analysis-card">
          <h3>📊 Tablo Verileri</h3>
          <p>{report.table_count} adet tablo bulundu ve analiz edildi.</p>
          <button
            className="button"
            onClick={() => handleFetchTables(report.id)}
            disabled={tablesLoading}
          >
            {tablesLoading ? "Yükleniyor..." : "Tabloları Göster"}
          </button>
          {tablesError && <p className="error-text">{tablesError}</p>}
          {tables.length > 0 && (
            <div className="table-preview-grid">
              {tables.map((table, index) => (
                <div key={`${table.page}-${table.table_num}-${index}`} className="table-preview">
                  <h4>
                    Sayfa {table.page}, Tablo {table.table_num}
                  </h4>
                  <table>
                    <tbody>
                      {(table.data || []).slice(0, 5).map((row, rowIndex) => (
                        <tr key={rowIndex}>
                          {(row || []).map((cell, cellIndex) => (
                            <td key={cellIndex}>{cell || ""}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {parsedStructuredData && (
        <div className="analysis-card">
          <h3>📋 Yapılandırılmış Veriler</h3>
          <div className="key-value-grid">
            {Object.entries(parsedStructuredData).map(([key, value]) => (
              <div key={key} className="key-value-row">
                <span className="key">{key}:</span>
                <span className="value">{String(value)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

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
