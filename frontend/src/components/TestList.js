import React from "react";

const TestList = ({ tests, showAiProvider = false }) => {
  if (!tests || tests.length === 0) {
    return <p>Gösterilecek test sonucu bulunamadı.</p>;
  }

  return (
    <div className="card">
      <table className="table">
        <thead>
          <tr>
            <th>Test Adı</th>
            <th>Durum</th>
            <th>Hata Mesajı</th>
            <th>Olası Neden</th>
            <th>Önerilen Çözüm</th>
          </tr>
        </thead>
        <tbody>
          {tests.map((test) => (
            <tr key={test.id || test.test_name}>
              <td>
                {test.test_name}
                {test.status === "FAIL" && showAiProvider && (
                  <span className={`ai-badge ${test.ai_provider || "rule-based"}`}>
                    {test.ai_provider === "claude"
                      ? "🤖 Claude"
                      : test.ai_provider === "chatgpt"
                      ? "🤖 ChatGPT"
                      : "📋 Kural Tabanlı"}
                  </span>
                )}
              </td>
              <td>
                <span
                  className={`status-pill ${test.status === "PASS" ? "status-pass" : "status-fail"}`}
                >
                  {test.status}
                </span>
              </td>
              <td>{test.error_message || "-"}</td>
              <td>{test.failure_reason || "-"}</td>
              <td>{test.suggested_fix || "-"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default TestList;
