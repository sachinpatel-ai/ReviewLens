import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
  timeout: 60000,
});

export const uploadCsv = (file, onProgress) => {
  const form = new FormData();
  form.append("file", file);
  return api
    .post("/api/upload", form, {
      onUploadProgress: (e) => onProgress?.(e.total ? Math.round((e.loaded * 100) / e.total) : 0),
    })
    .then((r) => r.data);
};
export const startAnalysis = (batchId) => api.post(`/api/batches/${batchId}/analyze`).then((r) => r.data);
export const getBatches = () => api.get("/api/batches").then((r) => r.data);
export const getBatch = (id) => api.get(`/api/batches/${id}`).then((r) => r.data);
export const getAnalytics = (batchId) =>
  api.get("/api/analytics", { params: { batch_id: batchId } }).then((r) => r.data);
export const getReviews = (params) => api.get("/api/reviews", { params }).then((r) => r.data);

/** Turn any axios error into a message a person can act on. */
export function errorMessage(err) {
  if (err.code === "ERR_NETWORK") return "Cannot reach the server. Check that the backend is running and the API URL is correct.";
  if (err.code === "ECONNABORTED") return "The request timed out. Please try again.";
  const detail = err.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((d) => d.msg).join("; ");
  return err.message || "Something went wrong.";
}
