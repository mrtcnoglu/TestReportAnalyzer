import axios from "axios";

const API_BASE = "http://localhost:5000/api";

const client = axios.create({
  baseURL: API_BASE,
  headers: {
    "Content-Type": "application/json",
  },
});

export const uploadReport = async (file) => {
  const formData = new FormData();
  formData.append("file", file);
  const response = await client.post("/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
};

export const getAllReports = async (sortBy = "date", order = "desc") => {
  const response = await client.get("/reports", {
    params: { sortBy, order },
  });
  return response.data.reports;
};

export const getReportById = async (id) => {
  const response = await client.get(`/reports/${id}`);
  return response.data;
};

export const getFailedTests = async (id) => {
  const response = await client.get(`/reports/${id}/failures`);
  return response.data.failures;
};

export const deleteReport = async (id) => {
  const response = await client.delete(`/reports/${id}`);
  return response.data;
};

export const getAIStatus = async () => {
  const response = await axios.get(`${API_BASE}/ai-status`);
  return response.data;
};
