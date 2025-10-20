import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { deleteReport, getAIStatus, getAllReports } from "../api";
import UploadForm from "./UploadForm";

const SORT_OPTIONS = [
  { key: "date", label: "Tarih" },
  { key: "name", label: "İsim" },
  { key: "total", label: "Toplam" },
  { key: "passed", label: "Başarılı" },
  { key: "failed", label: "Başarısız" },
];

const Dashboard = () => {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [aiStatus, setAIStatus] = useState({
    provider: "none",
    status: "inactive",
    claude_available: false,
    chatgpt_available: false,
  });
  const [sortBy, setSortBy] = useState("date");
  const [order, setOrder] = useState("desc");

  const loadReports = async (options = {}) => {
    setLoading(true);
    try {
      const data = await getAllReports(options.sortBy ?? sortBy, options.order ?? order);
      setReports(data);
      setError(null);
    } catch (err) {
      setError("Raporlar alınırken bir hata oluştu.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReports();
  }, []);

  useEffect(() => {
    const fetchAIStatus = async () => {
      try {
        const status = await getAIStatus();
        setAIStatus(status);
      } catch (err) {
        setAIStatus((prev) => ({ ...prev, status: "inactive", provider: "none" }));
      }
    };

    fetchAIStatus();
  }, []);

  const handleSortChange = (key) => {
    const newOrder = sortBy === key && order === "asc" ? "desc" : "asc";
    setSortBy(key);
    setOrder(newOrder);
    loadReports({ sortBy: key, order: newOrder });
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Bu raporu silmek istediğinize emin misiniz?")) {
      return;
    }
    try {
      await deleteReport(id);
      await loadReports();
    } catch (err) {
      setError("Rapor silinirken bir hata oluştu.");
    }
  };

  const sortedLabel = useMemo(() => {
    const option = SORT_OPTIONS.find((item) => item.key === sortBy);
    return option ? option.label : "Tarih";
  }, [sortBy]);

  return (
    <div>
      <div className="ai-status-container">
        <span>AI Provider: </span>
        {aiStatus.status === "active" ? (
          <span className="ai-status active">
            {aiStatus.provider === "claude"
              ? "🤖 Claude"
              : aiStatus.provider === "chatgpt"
              ? "🤖 ChatGPT"
              : "🤖 AI Aktif"}
          </span>
        ) : (
          <span className="ai-status inactive">📋 Kural Tabanlı</span>
        )}
      </div>

      <div className="card">
        <h2>Rapor Yükle</h2>
        <UploadForm onUploadSuccess={() => loadReports()} />
      </div>

      <div className="card">
        <h2>Raporlar</h2>
        <p>
          Sıralama: <strong>{sortedLabel}</strong> ({order === "asc" ? "Artan" : "Azalan"})
        </p>
        {error && <div className="alert alert-error">{error}</div>}
        {loading ? (
          <p>Yükleniyor...</p>
        ) : reports.length === 0 ? (
          <p>Henüz rapor bulunmuyor.</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th onClick={() => handleSortChange("name")}>Dosya Adı</th>
                <th onClick={() => handleSortChange("date")}>Yüklenme Tarihi</th>
                <th onClick={() => handleSortChange("total")}>Toplam Test</th>
                <th onClick={() => handleSortChange("passed")}>PASS</th>
                <th onClick={() => handleSortChange("failed")}>FAIL</th>
                <th>İşlemler</th>
              </tr>
            </thead>
            <tbody>
              {reports.map((report) => (
                <tr key={report.id}>
                  <td>
                    <Link to={`/report/${report.id}`}>{report.filename}</Link>
                  </td>
                  <td>{new Date(report.upload_date).toLocaleString()}</td>
                  <td>{report.total_tests}</td>
                  <td>{report.passed_tests}</td>
                  <td>{report.failed_tests}</td>
                  <td>
                    <button
                      className="button button-danger"
                      type="button"
                      onClick={() => handleDelete(report.id)}
                    >
                      Sil
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
