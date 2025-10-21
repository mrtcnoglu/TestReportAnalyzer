import React, { useCallback, useMemo, useRef, useState } from "react";
import { uploadReport } from "../api";
import { detectReportType } from "../utils/reportUtils";

const MAX_FILES = 100;

const ArchiveManagement = ({ reports, onRefresh }) => {
  const inputRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);
  const [status, setStatus] = useState(null);
  const [isUploading, setIsUploading] = useState(false);

  const handleFiles = useCallback(
    async (fileList) => {
      if (!fileList || fileList.length === 0) {
        setStatus({ type: "error", message: "Lütfen en az bir PDF seçin." });
        return;
      }

      const files = Array.from(fileList).filter((file) =>
        file.name.toLowerCase().endsWith(".pdf")
      );

      if (files.length === 0) {
        setStatus({ type: "error", message: "Sadece PDF dosyaları yükleyebilirsiniz." });
        return;
      }

      if (files.length > MAX_FILES) {
        setStatus({
          type: "error",
          message: `En fazla ${MAX_FILES} adet PDF yükleyebilirsiniz. Seçilen dosya sayısı: ${files.length}.`,
        });
        return;
      }

      setIsUploading(true);
      setStatus(null);

      let successCount = 0;
      let failCount = 0;

      for (const file of files) {
        try {
          await uploadReport(file);
          successCount += 1;
        } catch (error) {
          console.error("PDF yükleme hatası", error);
          failCount += 1;
        }
      }

      setIsUploading(false);
      setStatus({
        type: failCount > 0 ? "warning" : "success",
        message:
          failCount > 0
            ? `${successCount} rapor yüklendi, ${failCount} rapor yüklenemedi.`
            : `${successCount} rapor başarıyla yüklendi.`,
      });

      if (successCount > 0 && typeof onRefresh === "function") {
        onRefresh();
      }
    },
    [onRefresh]
  );

  const handleSelectClick = () => {
    inputRef.current?.click();
  };

  const handleFileInputChange = (event) => {
    handleFiles(event.target.files);
    event.target.value = "";
  };

  const handleDragOver = (event) => {
    event.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (event) => {
    event.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (event) => {
    event.preventDefault();
    setIsDragging(false);
    handleFiles(event.dataTransfer.files);
  };

  const archiveStats = useMemo(() => {
    const totalReports = reports.length;
    const grouped = reports.reduce(
      (acc, report) => {
        const type = detectReportType(report.filename);
        acc[type] = (acc[type] ?? 0) + 1;
        return acc;
      },
      {}
    );
    return { totalReports, grouped };
  }, [reports]);

  const recentReports = useMemo(
    () =>
      [...reports]
        .sort((a, b) => new Date(b.upload_date) - new Date(a.upload_date))
        .slice(0, 5),
    [reports]
  );

  return (
    <div className="archive-section">
      <div className="two-column-grid">
        <div className="card">
          <h2>Toplu PDF Yükleme</h2>
          <p className="muted-text">
            En fazla 100 adet PDF dosyasını sürükleyip bırakın veya tıklayarak seçin.
          </p>
          <div
            className={`drag-area ${isDragging ? "drag-active" : ""}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <p>{isUploading ? "PDF'ler yükleniyor..." : "Dosyalarınızı sürükleyip bırakın"}</p>
            <button type="button" className="button button-primary" onClick={handleSelectClick} disabled={isUploading}>
              Dosya Seç
            </button>
            <input
              ref={inputRef}
              type="file"
              accept="application/pdf"
              multiple
              hidden
              onChange={handleFileInputChange}
            />
          </div>
          {status && (
            <div className={`alert ${status.type === "success" ? "alert-success" : status.type === "warning" ? "alert-warning" : "alert-error"}`}>
              {status.message}
            </div>
          )}
        </div>

        <div className="card">
          <h2>Arşiv Özeti</h2>
          <p className="muted-text">Yüklenen raporların genel dağılımı.</p>
          <div className="chip-list">
            <div className="chip">
              Toplam Rapor: <strong>{archiveStats.totalReports}</strong>
            </div>
            {Object.entries(archiveStats.grouped).map(([type, count]) => (
              <div className="chip" key={type}>
                {type}: <strong>{count}</strong>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="card">
        <h2>Son Yüklenen Raporlar</h2>
        {recentReports.length === 0 ? (
          <p className="muted-text">Henüz rapor yüklenmedi.</p>
        ) : (
          <ul className="recent-reports">
            {recentReports.map((report) => (
              <li key={report.id}>
                <span className="recent-report-name">{report.filename}</span>
                <span className="recent-report-date">
                  {new Date(report.upload_date).toLocaleString()}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default ArchiveManagement;
