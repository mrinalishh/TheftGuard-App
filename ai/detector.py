import csv
import time
from pathlib import Path

import cv2
from ultralytics import YOLO

MODEL_PATH = "yolo11n.pt"


def run_detection(video_path, output_dir, job_id):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    tracked_video_path = output_dir / f"{job_id}_tracked.mp4"
    csv_path = output_dir / f"{job_id}_tracking.csv"

    model = YOLO(MODEL_PATH)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(tracked_video_path), fourcc, fps, (width, height))

    csv_file = open(csv_path, "w", newline="")
    writer = csv.writer(csv_file)
    writer.writerow(["frame", "timestamp_sec", "track_id", "class_name",
                      "confidence", "x1", "y1", "x2", "y2", "cx", "cy"])

    frame_idx = 0
    start_time = time.time()

    results = model.track(source=video_path, stream=True, persist=True, conf=0.4, verbose=False)

    for result in results:
        frame = result.orig_img
        timestamp_sec = frame_idx / fps

        if result.boxes is not None and result.boxes.id is not None:
            boxes = result.boxes.xyxy.cpu().numpy()
            track_ids = result.boxes.id.cpu().numpy().astype(int)
            confs = result.boxes.conf.cpu().numpy()
            classes = result.boxes.cls.cpu().numpy().astype(int)
            names = result.names

            for box, tid, conf, cls in zip(boxes, track_ids, confs, classes):
                x1, y1, x2, y2 = box
                cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
                class_name = names[int(cls)]

                writer.writerow([frame_idx, round(timestamp_sec, 2), int(tid), class_name,
                                  round(float(conf), 3), int(x1), int(y1), int(x2), int(y2),
                                  int(cx), int(cy)])

                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                cv2.putText(frame, f"{class_name} #{tid}", (int(x1), int(y1) - 8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        out.write(frame)
        frame_idx += 1

    cap.release()
    out.release()
    csv_file.close()

    return {
        "tracked_video_path": str(tracked_video_path),
        "csv_path": str(csv_path),
        "frame_count": frame_idx,
        "fps": fps,
        "processing_seconds": round(time.time() - start_time, 1),
    }