import React, { useMemo, useState } from "react";
import { detectReportType, getReportSummary } from "../utils/reportUtils";

const NaturalLanguageQuery = ({ reports, analysisEngine }) => {
  const [query, setQuery] = useState("");
  const [queryResult, setQueryResult] = useState("");
  const [aiResult, setAiResult] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);

  const latestReport = useMemo(() => {
    if (reports.length === 0) {
      return null;
    }
    return [...reports].sort((a, b) => new Date(b.upload_date) - new Date(a.upload_date))[0];
  }, [reports]);

  const schemaSummaries = useMemo(
    () =>
      reports.map((report) => {
        const pdfType = detectReportType(report.filename);
        const total = Number(report.total_tests ?? 0);
        const passed = Number(report.passed_tests ?? 0);
        const failed = Number(report.failed_tests ?? 0);
        const successRate = total > 0 ? Math.round((passed / total) * 100) : 0;
        return {
          id: report.id,
          fileName: report.filename,
          pdfType,
          summary: getReportSummary(report),
          insights:
            total === 0
              ? "Analiz verisi bulunmuyor"
              : `Başarı oranı %${successRate}. ${failed > 0 ? `${failed} başarısız test incelenmeli.` : "Tüm testler geçti."}`,
          rawMetrics: `${passed} PASS / ${failed} FAIL / ${total} TOPLAM`,
          modelUsed: analysisEngine === "claude" ? "Claude" : "ChatGPT",
          createdAt: new Date(report.upload_date).toLocaleString(),
        };
      }),
    [reports, analysisEngine]
  );

  const handleSubmit = (event) => {
    event.preventDefault();
    if (!query.trim()) {
      return;
    }

    setIsProcessing(true);
    const baseReport = latestReport ?? reports[0];

    setTimeout(() => {
      if (!baseReport) {
        setQueryResult("Analiz edilecek rapor bulunamadı.");
        setAiResult("Lütfen önce rapor yükleyin.");
        setIsProcessing(false);
        return;
      }

      const summary = getReportSummary(baseReport);
      setQueryResult(
        `"${query}" sorgusu için ${baseReport.filename} raporundan öne çıkan bilgiler:\n${summary}`
      );
      setAiResult(
        `${analysisEngine === "claude" ? "Claude" : "ChatGPT"} yorumuna göre: ${
          summary.includes("başarılı")
            ? "Testler genel olarak başarılı görünüyor, kritik alanlarda iyileştirme önerisi bulunmuyor."
            : "Test sonuçlarında riskli alanlar mevcut, detaylı inceleme önerilir."
        }`
      );
      setIsProcessing(false);
    }, 600);
  };

  return (
    <div className="natural-language-section">
      <div className="query-left">
        <div className="card">
          <h2>Sorgu Editörü</h2>
          <form className="query-form" onSubmit={handleSubmit}>
            <textarea
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="PDF içeriğinde ne aramak istersiniz?"
              rows={6}
            />
            <button className="button button-primary" type="submit" disabled={isProcessing}>
              {isProcessing ? "Sorgulanıyor..." : "Sorgula"}
            </button>
          </form>
        </div>

        <div className="card">
          <h3>Sorgu Sonuçları</h3>
          <p className="muted-text">
            Rapor içerisinden doğrudan çekilen bulgular burada gösterilir.
          </p>
          <pre className="query-output">{queryResult || "Henüz bir sorgu çalıştırılmadı."}</pre>
        </div>

        <div className="card">
          <h3>AI Raporu</h3>
          <p className="muted-text">
            Yapay zekanın değerlendirmesi ve ek yorumları bu alanda yer alır.
          </p>
          <pre className="query-output">{aiResult || "AI değerlendirmesi hazır değil."}</pre>
        </div>
      </div>

      <div className="schema-explorer card">
        <h2>Şema Gezgini</h2>
        <p className="muted-text">
          Raporlardan çıkarılan temel alanlara hızlı bir bakış.
        </p>
        {schemaSummaries.length === 0 ? (
          <p className="muted-text">Gösterilecek rapor bulunamadı.</p>
        ) : (
          <div className="schema-card-grid">
            {schemaSummaries.map((item) => (
              <div className="schema-card" key={item.id}>
                <span className="schema-type">{item.pdfType}</span>
                <div className="schema-field">
                  <strong>ID:</strong> {item.id}
                </div>
                <div className="schema-field">
                  <strong>File Name:</strong> {item.fileName}
                </div>
                <div className="schema-field">
                  <strong>PDF Type:</strong> {item.pdfType}
                </div>
                <div className="schema-field">
                  <strong>Summary:</strong> {item.summary}
                </div>
                <div className="schema-field">
                  <strong>Insights:</strong> {item.insights}
                </div>
                <div className="schema-field">
                  <strong>Raw Metrics:</strong> {item.rawMetrics}
                </div>
                <div className="schema-field">
                  <strong>Model Used:</strong> {item.modelUsed}
                </div>
                <div className="schema-field">
                  <strong>Created at:</strong> {item.createdAt}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default NaturalLanguageQuery;
