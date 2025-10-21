import React, { useRef, useState } from "react";
import { uploadReport } from "../api";

const UploadForm = ({ onUploadSuccess }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [status, setStatus] = useState({ type: null, message: "" });
  const [isUploading, setIsUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileSelection = (file) => {
    if (!file) {
      return;
    }

    if (file.type !== "application/pdf") {
      setStatus({ type: "error", message: "Lütfen PDF formatında bir dosya yükleyin." });
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
      return;
    }

    setSelectedFile(file);
    setStatus({ type: null, message: "" });
  };

  const handleFileChange = (event) => {
    const file = event.target.files?.[0];
    handleFileSelection(file);
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
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
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

  const handleDragOver = (event) => {
    event.preventDefault();
    event.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (event) => {
    event.preventDefault();
    event.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (event) => {
    event.preventDefault();
    event.stopPropagation();
    setIsDragging(false);
    const file = event.dataTransfer?.files?.[0];
    handleFileSelection(file);
  };

  const openFileDialog = () => {
    fileInputRef.current?.click();
  };

  return (
    <form className="upload-form" onSubmit={handleSubmit}>
      <div
        className={`drag-area ${isDragging ? "drag-active" : ""}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={openFileDialog}
        role="button"
        tabIndex={0}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            openFileDialog();
          }
        }}
        aria-label="PDF dosyalarınızı sürükleyip bırakın veya dosya seçin"
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="application/pdf"
          onChange={handleFileChange}
          hidden
        />
        <p className="drag-area-title">PDF raporlarınızı buraya sürükleyip bırakın</p>
        <p className="drag-area-subtitle">ya da aşağıdaki butona tıklayarak bilgisayarınızdan bir dosya seçin.</p>
        <button
          type="button"
          className="button button-secondary"
          onClick={(event) => {
            event.stopPropagation();
            openFileDialog();
          }}
        >
          Dosya Seç
        </button>
        {selectedFile && (
          <span className="selected-file-name">Seçilen dosya: {selectedFile.name}</span>
        )}
      </div>
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
