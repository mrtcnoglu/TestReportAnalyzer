import React from "react";
import { Link } from "react-router-dom";

const AllReports = ({ reports }) => {
  return (
    <div className="card">
      <div className="card-header">
        <h2>Tüm Raporlar</h2>
        <span className="badge">{reports.length}</span>
      </div>
      {reports.length === 0 ? (
        <p className="muted-text">Henüz rapor yüklenmedi.</p>
      ) : (
        <ul className="all-reports-list">
          {reports.map((report) => (
            <li key={report.id}>
              <span className="report-name">{report.filename}</span>
              <span className="report-date">{new Date(report.upload_date).toLocaleString()}</span>
              <Link className="report-link" to={`/report/${report.id}`}>
                Görüntüle
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default AllReports;
