import uuid
from datetime import datetime

from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


def gen_id():
    return str(uuid.uuid4())


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, default=gen_id)
    original_filename = Column(String)
    status = Column(String, default="processing")
    tracked_video_path = Column(String, nullable=True)
    csv_path = Column(String, nullable=True)
    frame_width = Column(Integer, nullable=True)
    frame_height = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    events = relationship("Event", back_populates="job")


class Event(Base):
    __tablename__ = "events"

    id = Column(String, primary_key=True, default=gen_id)
    job_id = Column(String, ForeignKey("jobs.id"))
    type = Column(String)
    severity = Column(String)
    timestamp_sec = Column(Float)
    object_track_id = Column(Integer, nullable=True)
    object_class = Column(String, nullable=True)
    person_track_id = Column(Integer, nullable=True)
    description = Column(String)

    job = relationship("Job", back_populates="events")