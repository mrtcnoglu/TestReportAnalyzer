const REPORT_TYPE_LABELS = {
  r80: "R80 Darbe Testi",
  r10: "R10 EMC Testi",
  unknown: "Bilinmeyen",
};

const REPORT_TYPE_NORMALIZATION = {
  r80: REPORT_TYPE_LABELS.r80,
  "ece r80": REPORT_TYPE_LABELS.r80,
  "r80 darbe testi": REPORT_TYPE_LABELS.r80,
  "r80 impact": REPORT_TYPE_LABELS.r80,
  "r10": REPORT_TYPE_LABELS.r10,
  "ece r10": REPORT_TYPE_LABELS.r10,
  "r10 emc testi": REPORT_TYPE_LABELS.r10,
  "r10 emc": REPORT_TYPE_LABELS.r10,
  unknown: REPORT_TYPE_LABELS.unknown,
};

const normalizeReportTypeLabel = (value = "") => {
  if (!value) {
    return null;
  }
  const key = value.toString().trim().toLowerCase();
  if (!key) {
    return null;
  }
  if (REPORT_TYPE_NORMALIZATION[key]) {
    return REPORT_TYPE_NORMALIZATION[key];
  }
  if (key.includes("r80") || key.includes("darbe")) {
    return REPORT_TYPE_LABELS.r80;
  }
  if (key.includes("r10") || key.includes("emc")) {
    return REPORT_TYPE_LABELS.r10;
  }
  return null;
};

const detectFromFilename = (filename = "") => {
  const name = (filename || "").toString().toLowerCase();
  if (name.includes("r80") || name.includes("darbe")) {
    return REPORT_TYPE_LABELS.r80;
  }
  if (name.includes("r10") || name.includes("emc")) {
    return REPORT_TYPE_LABELS.r10;
  }
  return REPORT_TYPE_LABELS.unknown;
};

export const detectReportType = (source = "") => {
  if (typeof source === "object" && source !== null) {
    const inferredFromLabel = normalizeReportTypeLabel(
      source.test_type_label || source.test_type || source.detectedType
    );
    if (inferredFromLabel) {
      return inferredFromLabel;
    }
    return detectFromFilename(source.filename ?? "");
  }

  return detectFromFilename(source);
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
