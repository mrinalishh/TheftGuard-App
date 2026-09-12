import sys
import os
import re
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "ai"))

import cv2
import numpy as np
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from ultralytics import YOLO

from .database import Base, engine, get_db
from . import models
from ai.detector import run_detection
from ai.theft_logic import analyze

Base.metadata.create_all(bind=engine)

STORAGE_INPUT = Path("storage/input")
STORAGE_OUTPUT = Path("storage/output")
STORAGE_INPUT.mkdir(parents=True, exist_ok=True)
STORAGE_OUTPUT.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="TheftGuard API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    "/files",
    StaticFiles(directory=str(STORAGE_OUTPUT)),
    name="files"
)

def process_video_job(job_id, video_path, db):
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    try:
        result = run_detection(video_path, str(STORAGE_OUTPUT), job_id)

        cap = cv2.VideoCapture(video_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()

        events = analyze(result["csv_path"], width, height)

        job.tracked_video_path = result["tracked_video_path"]
        job.csv_path = result["csv_path"]
        job.frame_width = width
        job.frame_height = height
        job.status = "done"

        for e in events:
            db.add(models.Event(job_id=job_id, **e))

        db.commit()
    except Exception as exc:
        job.status = "failed"
        db.commit()
        raise exc


@app.post("/api/upload")
async def upload_video(file: UploadFile = File(...), db: Session = Depends(get_db)):
    job = models.Job(original_filename=file.filename)
    db.add(job)
    db.commit()
    db.refresh(job)

    ext = Path(file.filename).suffix or ".mp4"
    safe_filename = f"{job.id}{ext}"

    save_path = STORAGE_INPUT / safe_filename
    with open(save_path, "wb") as f:
        f.write(await file.read())

    process_video_job(job.id, str(save_path), db)

    return {"job_id": job.id, "status": job.status}


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "id": job.id,
        "status": job.status,
        "original_filename": job.original_filename,
        "tracked_video_url": f"/files/{Path(job.tracked_video_path).name}" if job.tracked_video_path else None,
        "created_at": job.created_at,
    }


@app.get("/api/jobs/{job_id}/events")
def get_job_events(job_id: str, db: Session = Depends(get_db)):
    events = db.query(models.Event).filter(models.Event.job_id == job_id).all()
    return [
        {
            "id": e.id,
            "type": e.type,
            "severity": e.severity,
            "timestamp_sec": e.timestamp_sec,
            "object_class": e.object_class,
            "person_track_id": e.person_track_id,
            "description": e.description,
        }
        for e in events
    ]


@app.get("/api/jobs")
def list_jobs(db: Session = Depends(get_db)):
    jobs = db.query(models.Job).order_by(models.Job.created_at.desc()).limit(50).all()
    return [{"id": j.id, "status": j.status, "original_filename": j.original_filename} for j in jobs]


live_model = YOLO("../yolo11n.pt")


@app.websocket("/ws/live")
async def live_feed(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_bytes()
            frame = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
            results = live_model.track(frame, persist=True, conf=0.4, verbose=False)

            detections = []
            r = results[0]
            if r.boxes is not None and r.boxes.id is not None:
                for box, tid, cls, conf in zip(
                    r.boxes.xyxy.cpu().numpy(),
                    r.boxes.id.cpu().numpy().astype(int),
                    r.boxes.cls.cpu().numpy().astype(int),
                    r.boxes.conf.cpu().numpy(),
                ):
                    detections.append({
                        "track_id": int(tid),
                        "class_name": r.names[int(cls)],
                        "box": [float(v) for v in box],
                        "confidence": float(conf),
                    })

            await websocket.send_json({"detections": detections})
    except WebSocketDisconnect:
        pass
    