import React, { useMemo, useState } from "react";
import { getReportDownloadUrl } from "../api";
import { detectReportType, getReportStatusLabel } from "../utils/reportUtils";

const TestReportsBoard = ({ title, reports, analysisEngine }) => {
  const [selectedIds, setSelectedIds] = useState([]);
  const [actionMessage, setActionMessage] = useState(null);

  const tableData = useMemo(
    () =>
      reports.map((report) => ({
        ...report,
        detectedType: detectReportType(report),
        statusLabel: getReportStatusLabel(report),
      })),
    [reports]
  );

  const toggleSelection = (id) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const engineLabel = analysisEngine === "claude" ? "Claude" : "ChatGPT";

  const handleCompare = () => {
    if (selectedIds.length < 2) {
      setActionMessage("Karşılaştırma için en az iki rapor seçmelisiniz.");
      return;
    }

    if (selectedIds.length > 2) {
      setActionMessage("En Fazla 2 Adet Test Raporunu Karşılaştırma Yapabilirsiniz!");
      return;
    }

    setActionMessage(
      `${selectedIds.length} rapor ${engineLabel} ile karşılaştırılıyor...`
    );
  };

  const handleAnalyze = () => {
    if (selectedIds.length === 0) {
      setActionMessage("Analize göndermek için rapor seçin.");
      return;
    }

    if (selectedIds.length > 2) {
      setActionMessage("En Fazla 2 Adet Test Raporunu Analiz Edebilirsiniz!");
      return;
    }

    setActionMessage(
      `${selectedIds.length} rapor ${engineLabel} ile yeniden analiz ediliyor...`
    );
  };

  const handleView = () => {
    if (selectedIds.length !== 1) {
      setActionMessage("Bir raporu görüntülemek için tek rapor seçin.");
      return;
    }
    const [reportId] = selectedIds;
    const report = reports.find((item) => item.id === reportId);

    if (!report) {
      setActionMessage("Seçilen rapor bulunamadı.");
      return;
    }

    const pdfUrl = getReportDownloadUrl(reportId);
    window.open(pdfUrl, "_blank", "noopener,noreferrer");
    setActionMessage("PDF raporu yeni sekmede açılıyor...");
  };

  return (
    <div className="card">
      <div className="card-header">
        <h2>{title}</h2>
        <span className="badge">{reports.length} kayıt</span>
      </div>
      {reports.length === 0 ? (
        <p className="muted-text">Bu kategoriye ait rapor bulunamadı.</p>
      ) : (
        <table className="table">
          <thead>
            <tr>
              <th></th>
              <th>Tarih</th>
              <th>Koltuk Modeli</th>
              <th>Araç Platformu</th>
              <th>Lab</th>
              <th>Durum</th>
            </tr>
          </thead>
          <tbody>
            {tableData.map((report) => (
              <tr key={report.id}>
                <td>
                  <input
                    type="checkbox"
                    checked={selectedIds.includes(report.id)}
                    onChange={() => toggleSelection(report.id)}
                  />
                </td>
                <td>{new Date(report.upload_date).toLocaleDateString()}</td>
                <td>{report.detectedType === "R80 Darbe Testi" ? "ECE R80 Koltuk" : "Belirtilmedi"}</td>
                <td>{report.detectedType === "R10 EMC Testi" ? "ECE R10 Platformu" : "Genel Platform"}</td>
                <td>{report.detectedType === "R10 EMC Testi" ? "EMC Lab" : "Darbe Lab"}</td>
                <td>
                  <span className={`status-pill ${report.statusLabel.includes("Başarısız") ? "status-fail" : "status-pass"}`}>
                    {report.statusLabel}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <div className="report-actions">
        <button className="button" type="button" onClick={handleCompare}>
          Karşılaştır
        </button>
        <button className="button button-primary" type="button" onClick={handleAnalyze}>
          Analize Gönder
        </button>
        <button className="button" type="button" onClick={handleView}>
          Görüntüle
        </button>
      </div>
      {actionMessage && <div className="alert alert-info">{actionMessage}</div>}
    </div>
  );
};

export default TestReportsBoard;
