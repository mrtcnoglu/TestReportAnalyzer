import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getFailedTests, getReportById } from "../api";
import TestList from "./TestList";

const ReportDetail = () => {
  const { id } = useParams();
  const [report, setReport] = useState(null);
  const [tests, setTests] = useState([]);
  const [failures, setFailures] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadReport = async () => {
      try {
        const data = await getReportById(id);
        setReport(data.report);
        setTests(data.results);
        const failureData = await getFailedTests(id);
        setFailures(failureData);
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

      <h3>Tüm Testler</h3>
      <TestList tests={tests} showAiProvider />

      <h3>Başarısız Testler</h3>
      <TestList tests={failures} showAiProvider />
    </div>
  );
};

export default ReportDetail;
