import { useEffect, useRef, useState } from "react";

const WS_LIVE_URL = "ws://localhost:8000/ws/live";
const SEND_INTERVAL_MS = 300;

export default function LiveMonitor() {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const wsRef = useRef(null);
  const [active, setActive] = useState(false);
  const [detectionCount, setDetectionCount] = useState(0);

  useEffect(() => {
    if (!active) return;

    let stream;
    let intervalId;

    async function start() {
      stream = await navigator.mediaDevices.getUserMedia({ video: true });
      videoRef.current.srcObject = stream;
      await videoRef.current.play();

      wsRef.current = new WebSocket(WS_LIVE_URL);

      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        drawDetections(data.detections);
        setDetectionCount(data.detections.length);
      };

      intervalId = setInterval(sendFrame, SEND_INTERVAL_MS);
    }

    function sendFrame() {
      if (wsRef.current?.readyState !== WebSocket.OPEN) return;
      const canvas = document.createElement("canvas");
      canvas.width = videoRef.current.videoWidth;
      canvas.height = videoRef.current.videoHeight;
      canvas.getContext("2d").drawImage(videoRef.current, 0, 0);
      canvas.toBlob((blob) => {
        if (blob) wsRef.current.send(blob);
      }, "image/jpeg", 0.7);
    }

    function drawDetections(detections) {
      const canvas = canvasRef.current;
      const ctx = canvas.getContext("2d");
      canvas.width = videoRef.current.videoWidth;
      canvas.height = videoRef.current.videoHeight;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.strokeStyle = "#1D9E75";
      ctx.lineWidth = 2;
      ctx.font = "14px sans-serif";
      ctx.fillStyle = "#1D9E75";

      detections.forEach((d) => {
        const [x1, y1, x2, y2] = d.box;
        ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
        ctx.fillText(`${d.class_name} #${d.track_id}`, x1, y1 - 6);
      });
    }

    start();

    return () => {
      clearInterval(intervalId);
      wsRef.current?.close();
      stream?.getTracks().forEach((t) => t.stop());
    };
  }, [active]);

  return (
    <div className="live-monitor">
      <button onClick={() => setActive((a) => !a)}>
        {active ? "Stop monitoring" : "Start live monitoring"}
      </button>
      {active && (
        <>
          <p className="muted">{detectionCount} object(s) currently tracked</p>
          <div className="live-frame" style={{ position: "relative" }}>
            <video ref={videoRef} muted style={{ width: "100%", display: "block" }} />
            <canvas
              ref={canvasRef}
              style={{ position: "absolute", top: 0, left: 0, width: "100%", height: "100%" }}
            />
          </div>
        </>
      )}
    </div>
  );
}