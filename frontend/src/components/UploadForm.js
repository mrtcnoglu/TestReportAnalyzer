import React, { useState } from "react";
import { uploadReport } from "../api";

const UploadForm = ({ onUploadSuccess }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [status, setStatus] = useState({ type: null, message: "" });
  const [isUploading, setIsUploading] = useState(false);

  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0] ?? null);
    setStatus({ type: null, message: "" });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!selectedFile) {
      setStatus({ type: "error", message: "Lütfen bir PDF dosyası seçin." });
      return;
    }

    setIsUploading(true);
    setStatus({ type: null, message: "" });

    try {
      const response = await uploadReport(selectedFile);
      setStatus({ type: "success", message: "Rapor başarıyla yüklendi." });
      setSelectedFile(null);
      if (typeof onUploadSuccess === "function") {
        onUploadSuccess(response.report);
      }
    } catch (error) {
      const message = error.response?.data?.error ?? "Yükleme sırasında bir hata oluştu.";
      setStatus({ type: "error", message });
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <form className="upload-form" onSubmit={handleSubmit}>
      <input
        type="file"
        accept="application/pdf"
        onChange={handleFileChange}
      />
      <button className="button button-primary" type="submit" disabled={isUploading}>
        {isUploading ? "Yükleniyor..." : "PDF Yükle"}
      </button>
      {status.type && (
        <div className={`alert ${status.type === "success" ? "alert-success" : "alert-error"}`}>
          {status.message}
        </div>
      )}
    </form>
  );
};

export default UploadForm;
