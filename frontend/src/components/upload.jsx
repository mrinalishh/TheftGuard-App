import { useState } from "react";
import { uploadVideo } from "../api";

export default function Upload({ onJobReady }) {
  const [progress, setProgress] = useState(0);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState(null);

  async function handleFile(e) {
    const file = e.target.files[0];
    if (!file) return;

    setError(null);
    setProcessing(true);
    setProgress(0);

    try {
      const result = await uploadVideo(file, setProgress);
      onJobReady(result.job_id);
    } catch (err) {
      setError("Upload or processing failed. Check the backend logs.");
    } finally {
      setProcessing(false);
    }
  }

  return (
    <div className="upload-box">
      <label className="upload-label">
        {processing ? `Processing... ${progress}%` : "Choose a video to analyze"}
        <input type="file" accept="video/*" onChange={handleFile} disabled={processing} hidden />
      </label>
      {error && <p className="error-text">{error}</p>}
    </div>
  );
}