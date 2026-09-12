import axios from "axios";

const API_BASE = "https://theftguard-backend.onrender.com";

export async function uploadVideo(file, onProgress) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await axios.post(`${API_BASE}/api/upload`, formData, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (evt) => {
      if (onProgress) onProgress(Math.round((evt.loaded * 100) / evt.total));
    },
  });
  return res.data;
}

export async function getJob(jobId) {
  const res = await axios.get(`${API_BASE}/api/jobs/${jobId}`);
  return res.data;
}

export async function getJobEvents(jobId) {
  const res = await axios.get(`${API_BASE}/api/jobs/${jobId}/events`);
  return res.data;
}

export async function listJobs() {
  const res = await axios.get(`${API_BASE}/api/jobs`);
  return res.data;
}

export const FILES_BASE = API_BASE;