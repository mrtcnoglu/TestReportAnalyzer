import React from "react";
import { Link, Route, Routes } from "react-router-dom";
import Dashboard from "./components/Dashboard";
import ReportDetail from "./components/ReportDetail";

const App = () => {
  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Test Report Analyzer</h1>
        <nav>
          <Link to="/">Ana Sayfa</Link>
        </nav>
      </header>
      <main className="app-main">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/report/:id" element={<ReportDetail />} />
        </Routes>
      </main>
      <footer className="app-footer">© {new Date().getFullYear()} Test Report Analyzer</footer>
    </div>
  );
};

export default App;
