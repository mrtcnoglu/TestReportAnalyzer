import React, { useMemo, useState } from "react";
import { detectReportType, getReportStatusLabel } from "../utils/reportUtils";
import AnalysisSummaryCard from "./AnalysisSummaryCard";

const deriveLaboratory = (filename = "", detectedType = "") => {
  const name = filename.toLowerCase();
  if (name.includes("concept")) {
    return "Concept Test Laboratuvarı";
  }
  if (name.includes("tse") || name.includes("türk")) {
    return "Türk Standartları Enstitüsü";
  }
  if (name.includes("gcs")) {
    return "GCS Test Laboratuvarı";
  }
  return detectedType === "R10 EMC Testi" ? "GCS Test Laboratuvarı" : "Concept Test Laboratuvarı";
};

const deriveModel = (filename = "") => {
  const name = filename.toLowerCase();
  if (name.includes("avance-x")) {
    return "Avance-X";
  }
  if (name.includes("interline")) {
    return "Interline";
  }
  if (name.includes("avance")) {
    return "Avance";
  }
  return "Avance";
};

const deriveStatusFilterValue = (statusLabel = "") => {
  if (statusLabel === "Başarılı" || statusLabel === "Başarısız") {
    return statusLabel;
  }
  if (statusLabel === "Belirsiz") {
    return "Belirsiz";
  }
  return "Belirsiz";
};

const ArchiveManagement = ({ reports, analysisEngine = "chatgpt", analysisArchive = [] }) => {
  const [filters, setFilters] = useState({
    startDate: "",
    endDate: "",
    testType: "",
    laboratory: "",
    model: "",
    status: "",
  });
  const [filteredReports, setFilteredReports] = useState([]);
  const [filtersApplied, setFiltersApplied] = useState(false);
  const [isArchiveCollapsed, setIsArchiveCollapsed] = useState(false);

  const enrichedReports = useMemo(
    () =>
      reports.map((report) => {
        const detectedType = detectReportType(report);
        const uploadDate = report.upload_date ? new Date(report.upload_date) : null;
        return {
          ...report,
          detectedType,
          uploadDate,
          laboratory: deriveLaboratory(report.filename ?? "", detectedType),
          model: deriveModel(report.filename ?? ""),
          statusLabel: getReportStatusLabel(report),
        };
      }),
    [reports]
  );

  const reportsWithStatus = useMemo(
    () =>
      enrichedReports.map((report) => ({
        ...report,
        statusFilterValue: deriveStatusFilterValue(report.statusLabel),
      })),
    [enrichedReports]
  );

  const archiveSummary = useMemo(() => {
    const summary = {
      r10: 0,
      r80: 0,
      unknown: 0,
    };

    reportsWithStatus.forEach((report) => {
      if (report.detectedType === "R10 EMC Testi") {
        summary.r10 += 1;
      } else if (report.detectedType === "R80 Darbe Testi") {
        summary.r80 += 1;
      } else {
        summary.unknown += 1;
      }
    });

    return summary;
  }, [reportsWithStatus]);

  const recentReports = useMemo(() => {
    return [...reportsWithStatus]
      .sort((a, b) => (b.uploadDate?.getTime() ?? 0) - (a.uploadDate?.getTime() ?? 0))
      .slice(0, 10);
  }, [reportsWithStatus]);

  const matchesDateRange = (report) => {
    if (!report.uploadDate) {
      return false;
    }

    if (filters.startDate) {
      const start = new Date(filters.startDate);
      if (report.uploadDate < start) {
        return false;
      }
    }

    if (filters.endDate) {
      const end = new Date(filters.endDate);
      end.setHours(23, 59, 59, 999);
      if (report.uploadDate > end) {
        return false;
      }
    }

    return true;
  };

  const applyFilters = () => {
    const results = reportsWithStatus.filter((report) => {
      if (filters.startDate || filters.endDate) {
        if (!matchesDateRange(report)) {
          return false;
        }
      }

      if (filters.testType && report.detectedType !== filters.testType) {
        return false;
      }

      if (filters.laboratory && report.laboratory !== filters.laboratory) {
        return false;
      }

      if (filters.model && report.model !== filters.model) {
        return false;
      }

      if (filters.status && report.statusFilterValue !== filters.status) {
        return false;
      }

      return true;
    });

    results.sort(
      (a, b) => (b.uploadDate?.getTime() ?? 0) - (a.uploadDate?.getTime() ?? 0)
    );

    setFilteredReports(results);
    setFiltersApplied(true);
  };

  const clearFilters = () => {
    setFilters({
      startDate: "",
      endDate: "",
      testType: "",
      laboratory: "",
      model: "",
      status: "",
    });
    setFilteredReports([]);
    setFiltersApplied(false);
  };

  const hasFilters = Object.values(filters).some(Boolean);

  return (
    <div className="archive-section">
      <div className="two-column-grid">
        <div className="card archive-summary-card">
          <h2>Arşiv Özeti</h2>
          <p className="muted-text">
            {analysisEngine === "claude"
              ? "Veriler Claude analizi sonrasında güncellendi."
              : "Veriler ChatGPT analizi sonrasında güncellendi."}
          </p>
          <div className="archive-summary-grid">
            <div className="summary-item">
              <span className="summary-label">ECE R10 EMC Testi Sayısı</span>
              <span className="summary-value">{archiveSummary.r10}</span>
            </div>
            <div className="summary-item">
              <span className="summary-label">ECE R80 Darbe Testi Sayısı</span>
              <span className="summary-value">{archiveSummary.r80}</span>
            </div>
            <div className="summary-item">
              <span className="summary-label">Bilinmeyen Test Sayısı</span>
              <span className="summary-value">{archiveSummary.unknown}</span>
            </div>
          </div>
        </div>

        <div className="card filters-card">
          <h2>
            <span className="card-title-icon" aria-hidden="true">
              📖
            </span>
            Filtreler
          </h2>
          <div className="filters-grid">
            <label className="filter-field">
              <span>Başlangıç Tarihi</span>
              <input
                type="date"
                value={filters.startDate}
                onChange={(event) => setFilters((prev) => ({ ...prev, startDate: event.target.value }))}
              />
            </label>
            <label className="filter-field">
              <span>Bitiş Tarihi</span>
              <input
                type="date"
                value={filters.endDate}
                onChange={(event) => setFilters((prev) => ({ ...prev, endDate: event.target.value }))}
              />
            </label>
            <label className="filter-field">
              <span>Test Tipi</span>
              <select
                value={filters.testType}
                onChange={(event) => setFilters((prev) => ({ ...prev, testType: event.target.value }))}
              >
                <option value="">Seçiniz</option>
                <option value="R10 EMC Testi">ECE R10 EMC Testi</option>
                <option value="R80 Darbe Testi">ECE R80 Darbe Testi</option>
              </select>
            </label>
            <label className="filter-field">
              <span>Labaratuvar</span>
              <select
                value={filters.laboratory}
                onChange={(event) => setFilters((prev) => ({ ...prev, laboratory: event.target.value }))}
              >
                <option value="">Seçiniz</option>
                <option value="GCS Test Laboratuvarı">GCS Test Laboratuvarı</option>
                <option value="Concept Test Laboratuvarı">Concept Test Laboratuvarı</option>
                <option value="Türk Standartları Enstitüsü">Türk Standartları Enstitüsü</option>
              </select>
            </label>
            <label className="filter-field">
              <span>Model</span>
              <select
                value={filters.model}
                onChange={(event) => setFilters((prev) => ({ ...prev, model: event.target.value }))}
              >
                <option value="">Seçiniz</option>
                <option value="Avance">Avance</option>
                <option value="Interline">Interline</option>
                <option value="Avance-X">Avance-X</option>
              </select>
            </label>
            <label className="filter-field">
              <span>Durum</span>
              <select
                value={filters.status}
                onChange={(event) => setFilters((prev) => ({ ...prev, status: event.target.value }))}
              >
                <option value="">Seçiniz</option>
                <option value="Başarılı">Başarılı</option>
                <option value="Başarısız">Başarısız</option>
                <option value="Belirsiz">Belirsiz</option>
                <option value="Kısmi Başarı">Kısmi Başarı</option>
                <option value="Analiz Bekleniyor">Analiz Bekleniyor</option>
              </select>
            </label>
          </div>
          <div className="filter-buttons">
            <button type="button" className="button" onClick={clearFilters} disabled={!hasFilters && !filtersApplied}>
              Temizle
            </button>
            <button type="button" className="button button-primary" onClick={applyFilters}>
              Uygula
            </button>
          </div>
        </div>
      </div>

      {filtersApplied && (
        <div className="card filter-results-card">
          <div className="card-header">
            <h2>Filtrelenen Raporlar</h2>
            <span className="badge">{filteredReports.length} kayıt</span>
          </div>
          {filteredReports.length === 0 ? (
            <p className="muted-text">Seçilen kriterlere uygun rapor bulunamadı.</p>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>Yüklenen Rapor</th>
                  <th>Yükleme Tarihi</th>
                  <th>Yükleme Saati</th>
                  <th>Test Tipi</th>
                  <th>Labaratuvar</th>
                  <th>Durum</th>
                </tr>
              </thead>
              <tbody>
                {filteredReports.map((report) => (
                  <tr key={report.id}>
                    <td>{report.filename}</td>
                    <td>{report.uploadDate ? report.uploadDate.toLocaleDateString() : "-"}</td>
                    <td>{report.uploadDate ? report.uploadDate.toLocaleTimeString() : "-"}</td>
                    <td>{report.detectedType}</td>
                    <td>{report.laboratory}</td>
                    <td>{report.statusLabel}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      <div className="card recent-reports-card">
        <h2>Son Yüklenen Raporlar</h2>
        {recentReports.length === 0 ? (
          <p className="muted-text">Henüz rapor yüklenmedi.</p>
        ) : (
          <table className="table recent-reports-table">
            <thead>
              <tr>
                <th>Yüklenen Rapor</th>
                <th>Yükleme Tarihi</th>
                <th>Yükleme Saati</th>
              </tr>
            </thead>
            <tbody>
              {recentReports.map((report) => (
                <tr key={report.id}>
                  <td>{report.filename}</td>
                  <td>{report.uploadDate ? report.uploadDate.toLocaleDateString() : "-"}</td>
                  <td>{report.uploadDate ? report.uploadDate.toLocaleTimeString() : "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
      <AnalysisSummaryCard
        analyses={analysisArchive}
        title="Analiz Arşivi"
        introText={
          analysisArchive.length > 0
            ? "Önceki AI analiz sonuçları arşivde saklanmaktadır."
            : "Arşivde gösterilecek analiz bulunmuyor."
        }
        emptyMessage="Arşivde gösterilecek analiz bulunmuyor."
        headerActions={
          <button
            type="button"
            className="button button-ghost analysis-summary-toggle"
            onClick={() => setIsArchiveCollapsed((prev) => !prev)}
          >
            {isArchiveCollapsed ? "Göster" : "Gizle"}
          </button>
        }
        collapsed={isArchiveCollapsed}
      />
    </div>
  );
};

export default ArchiveManagement;
