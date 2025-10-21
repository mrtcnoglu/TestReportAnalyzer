import React from "react";

const SettingsPanel = ({ theme, onThemeChange, analysisEngine, onEngineChange }) => {
  return (
    <div className="settings-section">
      <div className="two-column-grid settings-grid">
        <div className="card">
          <h2>Tema Tercihi</h2>
          <p className="muted-text">
            Uygulamanın görünümünü açık veya koyu tema arasında değiştirin.
          </p>
          <div className="radio-group">
            <label>
              <input
                type="radio"
                name="theme"
                value="light"
                checked={theme === "light"}
                onChange={(event) => onThemeChange(event.target.value)}
              />
              Açık Tema
            </label>
            <label>
              <input
                type="radio"
                name="theme"
                value="dark"
                checked={theme === "dark"}
                onChange={(event) => onThemeChange(event.target.value)}
              />
              Koyu Tema
            </label>
          </div>
        </div>

        <div className="card">
          <h2>Analiz Motoru</h2>
          <p className="muted-text">Rapor analizleri için kullanılacak yapay zeka motorunu seçin.</p>
          <div className="radio-group">
            <label>
              <input
                type="radio"
                name="engine"
                value="chatgpt"
                checked={analysisEngine === "chatgpt"}
                onChange={(event) => onEngineChange(event.target.value)}
              />
              ChatGPT
            </label>
            <label>
              <input
                type="radio"
                name="engine"
                value="claude"
                checked={analysisEngine === "claude"}
                onChange={(event) => onEngineChange(event.target.value)}
              />
              Claude
            </label>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPanel;
