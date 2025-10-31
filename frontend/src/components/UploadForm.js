import React, { useEffect, useRef, useState } from "react";
import { analyzeReportsWithAI, uploadReport } from "../api";

const MIN_FILES = 1;
const MAX_FILES = 2;
const MAX_FILES_MESSAGE = "En fazla 2 pdf yükleyebilirsiniz!";

const UploadForm = ({
  onUploadSuccess,
  analysisEngine = "chatgpt",
  onAnalysisComplete,
  onClearAnalysis,
  isProcessing = false,
  onProcessingStart,
  onProcessingEnd,
}) => {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [status, setStatus] = useState({ type: null, message: "" });
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);
  const isMountedRef = useRef(true);

  useEffect(() => {
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  const setSelectedFilesSafe = (value) => {
    if (isMountedRef.current) {
      setSelectedFiles(value);
    }
  };

  const setStatusSafe = (value) => {
    if (isMountedRef.current) {
      setStatus(value);
    }
  };

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
        error: MAX_FILES_MESSAGE,
      };
    }

    return { files: incomingFiles, error: null };
  };

  const handleFileSelection = (fileList) => {
    const { files, error } = sanitizeFiles(fileList);

    if (error) {
      setSelectedFilesSafe([]);
      setStatusSafe({ type: "error", message: error });
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
      return;
    }

    setSelectedFilesSafe(files);
    setStatusSafe({ type: null, message: "" });
    if (files.length > 0 && typeof onClearAnalysis === "function") {
      onClearAnalysis();
    }
  };

  const handleFileChange = (event) => {
    if (isProcessing) {
      return;
    }
    handleFileSelection(event.target.files);
    if (event.target) {
      event.target.value = "";
    }
  };

  const handleUploadAndAnalyze = async (event) => {
    event.preventDefault();

    if (isProcessing) {
      return;
    }

    if (selectedFiles.length < MIN_FILES) {
      setStatusSafe({
        type: "error",
        message: `Lütfen en az ${MIN_FILES} adet PDF dosyası seçin.`,
      });
      onAnalysisComplete?.(null);
      return;
    }

    if (selectedFiles.length > MAX_FILES) {
      setStatusSafe({
        type: "error",
        message: MAX_FILES_MESSAGE,
      });
      onAnalysisComplete?.(null);
      return;
    }

    onProcessingStart?.();
    setStatusSafe({ type: null, message: "" });

    let successCount = 0;
    let failCount = 0;

    try {
      for (const file of selectedFiles) {
        try {
          await uploadReport(file);
          successCount += 1;
        } catch (error) {
          console.error("PDF yükleme hatası", error);
          failCount += 1;
        }
      }

      let analysisResult = null;
      let analysisErrorMessage = "";

      if (successCount > 0) {
        try {
          analysisResult = await analyzeReportsWithAI(selectedFiles, analysisEngine);
        } catch (error) {
          analysisErrorMessage =
            error?.response?.data?.error || "AI analizi sırasında bir sorun oluştu. Lütfen tekrar deneyin.";
        }
      }

      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
      setSelectedFilesSafe([]);

      if (successCount > 0 && typeof onUploadSuccess === "function") {
        await onUploadSuccess();
      }

      if (analysisResult) {
        onAnalysisComplete?.(analysisResult);
      } else if (analysisErrorMessage) {
        onAnalysisComplete?.(null);
      } else if (successCount === 0) {
        onAnalysisComplete?.(null);
      }

      const messages = [];
      if (successCount === 0) {
        messages.push("Seçilen raporlar yüklenemedi. Lütfen tekrar deneyin.");
      } else if (failCount === 0) {
        messages.push(`${successCount} rapor başarıyla yüklendi.`);
      } else {
        messages.push(`${successCount} rapor yüklendi, ${failCount} rapor yüklenemedi.`);
      }

      if (analysisResult?.message) {
        messages.push(analysisResult.message);
      }

      if (analysisErrorMessage) {
        messages.push(analysisErrorMessage);
      }

      let statusType = "success";
      if (analysisErrorMessage) {
        statusType = "error";
      } else if (successCount === 0) {
        statusType = "error";
      } else if (failCount > 0) {
        statusType = "warning";
      }

      setStatusSafe({ type: statusType, message: messages.join(" ") });
    } finally {
      onProcessingEnd?.();
    }
  };

  const handleClearSelection = (event) => {
    event.preventDefault();
    if (isProcessing) {
      return;
    }
    setSelectedFilesSafe([]);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
    setStatusSafe({ type: null, message: "" });
    if (typeof onClearAnalysis === "function") {
      onClearAnalysis();
    }
  };

  const handleDragOver = (event) => {
    event.preventDefault();
    event.stopPropagation();
    if (isProcessing) {
      return;
    }
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
    if (isProcessing) {
      return;
    }
    handleFileSelection(event.dataTransfer?.files);
  };

  const openFileDialog = () => {
    fileInputRef.current?.click();
  };

  return (
    <form className="upload-form" onSubmit={handleUploadAndAnalyze}>
      <div
        className={`drag-area ${isDragging ? "drag-active" : ""}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => {
          if (!isProcessing) {
            openFileDialog();
          }
        }}
        role="button"
        tabIndex={0}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            if (!isProcessing) {
              openFileDialog();
            }
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
        <p className="drag-area-title">PDF Test Raporlarını Sürükleyip Bırakabilirsiniz</p>
        <p className="drag-area-subtitle">Aynı anda en fazla 2 pdf yükleyebilirsiniz!</p>
        <button
          type="button"
          className="button button-secondary"
          onClick={(event) => {
            event.stopPropagation();
            if (!isProcessing) {
              openFileDialog();
            }
          }}
          disabled={isProcessing}
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
          className="button button-primary"
          type="submit"
          disabled={isProcessing || selectedFiles.length === 0}
        >
          {isProcessing ? "İşleniyor..." : "PDF Yükle ve AI ile Analiz Et"}
        </button>
        <button
          type="button"
          className="button button-secondary"
          onClick={handleClearSelection}
          disabled={isProcessing || selectedFiles.length === 0}
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
