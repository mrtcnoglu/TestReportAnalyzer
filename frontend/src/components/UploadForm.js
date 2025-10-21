import React, { useRef, useState } from "react";
import { analyzeReportsWithAI, uploadReport } from "../api";

const MIN_FILES = 1;
const MAX_FILES = 100;

const UploadForm = ({ onUploadSuccess, analysisEngine = "chatgpt", onAnalysisComplete, onClearAnalysis }) => {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [status, setStatus] = useState({ type: null, message: "" });
  const [isUploading, setIsUploading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);

  const sanitizeFiles = (fileList) => {
    const incomingFiles = Array.from(fileList ?? []);

    if (incomingFiles.length === 0) {
      return { files: [], error: "Lütfen en az bir PDF seçin." };
    }

    const nonPdfFiles = incomingFiles.filter((file) => file.type !== "application/pdf");

    if (nonPdfFiles.length > 0) {
      return { files: [], error: "Yalnızca PDF formatındaki raporları yükleyebilirsiniz." };
    }

    if (incomingFiles.length > MAX_FILES) {
      return {
        files: [],
        error: `En fazla ${MAX_FILES} adet PDF yükleyebilirsiniz. Seçilen dosya sayısı: ${incomingFiles.length}.`,
      };
    }

    return { files: incomingFiles, error: null };
  };

  const handleFileSelection = (fileList) => {
    const { files, error } = sanitizeFiles(fileList);

    if (error) {
      setSelectedFiles([]);
      setStatus({ type: "error", message: error });
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
      return;
    }

    setSelectedFiles(files);
    setStatus({ type: null, message: "" });
    if (files.length > 0 && typeof onClearAnalysis === "function") {
      onClearAnalysis();
    }
  };

  const handleFileChange = (event) => {
    handleFileSelection(event.target.files);
    if (event.target) {
      event.target.value = "";
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (selectedFiles.length < MIN_FILES) {
      setStatus({
        type: "error",
        message: `Lütfen en az ${MIN_FILES} adet PDF dosyası seçin.`,
      });
      return;
    }

    if (selectedFiles.length > MAX_FILES) {
      setStatus({
        type: "error",
        message: `En fazla ${MAX_FILES} adet PDF yükleyebilirsiniz.`,
      });
      return;
    }

    setIsUploading(true);
    setStatus({ type: null, message: "" });

    let successCount = 0;
    let failCount = 0;

    for (const file of selectedFiles) {
      try {
        await uploadReport(file);
        successCount += 1;
      } catch (error) {
        console.error("PDF yükleme hatası", error);
        failCount += 1;
      }
    }

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
    setSelectedFiles([]);

    if (successCount > 0 && typeof onUploadSuccess === "function") {
      onUploadSuccess();
    }

    if (failCount === 0) {
      setStatus({
        type: "success",
        message: `${successCount} rapor başarıyla yüklendi.`,
      });
    } else if (successCount === 0) {
      setStatus({
        type: "error",
        message: "Seçilen raporlar yüklenemedi. Lütfen tekrar deneyin.",
      });
    } else {
      setStatus({
        type: "warning",
        message: `${successCount} rapor yüklendi, ${failCount} rapor yüklenemedi.`,
      });
    }

    setIsUploading(false);
  };

  const handleAnalyzeWithAI = async (event) => {
    event.preventDefault();

    if (selectedFiles.length === 0) {
      setStatus({ type: "error", message: "AI analizi için lütfen en az bir PDF seçin." });
      onAnalysisComplete?.(null);
      return;
    }

    setIsAnalyzing(true);
    setStatus({ type: null, message: "" });

    try {
      const result = await analyzeReportsWithAI(selectedFiles, analysisEngine);
      setStatus({ type: "success", message: result.message });
      onAnalysisComplete?.(result);
    } catch (error) {
      const message =
        error?.response?.data?.error || "AI analizi sırasında bir sorun oluştu. Lütfen tekrar deneyin.";
      setStatus({ type: "error", message });
      onAnalysisComplete?.(null);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleClearSelection = (event) => {
    event.preventDefault();
    setSelectedFiles([]);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
    setStatus({ type: null, message: "" });
    if (typeof onClearAnalysis === "function") {
      onClearAnalysis();
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
    handleFileSelection(event.dataTransfer?.files);
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
          multiple
          onChange={handleFileChange}
          hidden
        />
        <p className="drag-area-title">PDF raporlarınızı buraya sürükleyip bırakın</p>
        <p className="drag-area-subtitle">
          ya da aşağıdaki butona tıklayarak bilgisayarınızdan en az 1, en fazla 100 PDF seçin.
        </p>
        <button
          type="button"
          className="button button-secondary"
          onClick={(event) => {
            event.stopPropagation();
            openFileDialog();
          }}
          disabled={isUploading}
        >
          Dosya Seç
        </button>
        {selectedFiles.length > 0 && (
          <div className="selected-files">
            <span className="selected-file-name">
              Seçilen {selectedFiles.length} PDF hazırlanıyor.
            </span>
            <ul className="selected-files-list">
              {selectedFiles.slice(0, 5).map((file) => (
                <li key={file.name}>{file.name}</li>
              ))}
              {selectedFiles.length > 5 && (
                <li>+{selectedFiles.length - 5} adet daha...</li>
              )}
            </ul>
          </div>
        )}
      </div>
      <div className="upload-actions">
        <button
          type="button"
          className="button button-accent"
          onClick={handleAnalyzeWithAI}
          disabled={isUploading || isAnalyzing || selectedFiles.length === 0}
        >
          {isAnalyzing ? "Analiz Ediliyor..." : "AI İle Analiz Et"}
        </button>
        <button
          className="button button-primary"
          type="submit"
          disabled={isUploading || selectedFiles.length === 0}
        >
          {isUploading ? "Yükleniyor..." : "PDF Yükle"}
        </button>
        <button
          type="button"
          className="button button-secondary"
          onClick={handleClearSelection}
          disabled={isUploading || isAnalyzing || selectedFiles.length === 0}
        >
          Temizle
        </button>
      </div>
      {status.type && (
        <div
          className={`alert ${
            status.type === "success"
              ? "alert-success"
              : status.type === "warning"
              ? "alert-warning"
              : "alert-error"
          }`}
        >
          {status.message}
        </div>
      )}
    </form>
  );
};

export default UploadForm;
