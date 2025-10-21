import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { deleteReport } from "../api";

const AllReports = ({ reports, onReportDeleted }) => {
  const [items, setItems] = useState(reports);
  const [actionStatus, setActionStatus] = useState(null);

  useEffect(() => {
    setItems(reports);
  }, [reports]);

  const handleDelete = async (reportId) => {
    if (!reportId) {
      return;
    }

    const confirmDelete = window.confirm("Bu raporu silmek istediğinize emin misiniz?");
    if (!confirmDelete) {
      return;
    }

    try {
      await deleteReport(reportId);
      setItems((prev) => prev.filter((report) => report.id !== reportId));
      setActionStatus({ type: "success", message: "Rapor başarıyla silindi." });
      if (typeof onReportDeleted === "function") {
        onReportDeleted();
      }
    } catch (error) {
      const message =
        error?.response?.data?.error || "Rapor silinirken bir sorun oluştu. Lütfen tekrar deneyin.";
      setActionStatus({ type: "error", message });
    }
  };

  return (
    <div className="card">
      <div className="card-header">
        <h2>Tüm Raporlar</h2>
        <span className="badge">{items.length}</span>
      </div>
      {actionStatus && (
        <div
          className={`alert ${
            actionStatus.type === "success"
              ? "alert-success"
              : actionStatus.type === "error"
              ? "alert-error"
              : "alert-info"
          }`}
        >
          {actionStatus.message}
        </div>
      )}
      {items.length === 0 ? (
        <p className="muted-text">Henüz rapor yüklenmedi.</p>
      ) : (
        <ul className="all-reports-list">
          {items.map((report) => (
            <li key={report.id}>
              <span className="report-name">{report.filename}</span>
              <span className="report-date">{new Date(report.upload_date).toLocaleString()}</span>
              <Link className="report-link" to={`/report/${report.id}`}>
                Görüntüle
              </Link>
              <button
                type="button"
                className="button button-danger button-ghost"
                onClick={() => handleDelete(report.id)}
              >
                Sil
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default AllReports;
