const REPORT_TYPE_LABELS = {
  r80: "R80 Darbe Testi",
  r10: "R10 EMC Testi",
  unknown: "Bilinmeyen"
};

export const detectReportType = (filename = "") => {
  const name = filename.toLowerCase();
  if (name.includes("r80") || name.includes("darbe")) {
    return REPORT_TYPE_LABELS.r80;
  }
  if (name.includes("r10") || name.includes("emc")) {
    return REPORT_TYPE_LABELS.r10;
  }
  return REPORT_TYPE_LABELS.unknown;
};

export const getReportStatusLabel = (report) => {
  const passed = Number(report?.passed_tests ?? 0);
  const failed = Number(report?.failed_tests ?? 0);

  if (failed === 0 && (passed > 0 || Number(report?.total_tests ?? 0) > 0)) {
    return "Başarılı";
  }
  if (failed > 0 && passed === 0) {
    return "Başarısız";
  }
  if (passed > 0 && failed > 0) {
    return "Kısmi Başarı";
  }
  return "Analiz Bekleniyor";
};

export const getReportSummary = (report) => {
  const total = Number(report?.total_tests ?? 0);
  const passed = Number(report?.passed_tests ?? 0);
  const failed = Number(report?.failed_tests ?? 0);
  if (total === 0) {
    return "Test verisi bulunmuyor.";
  }
  return `Toplam ${total} testin ${passed}'i başarılı, ${failed}'i başarısız.`;
};
