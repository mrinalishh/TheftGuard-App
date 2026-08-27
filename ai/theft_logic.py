from collections import defaultdict
import csv
import math

VALUABLE_CLASSES = {"backpack", "handbag", "suitcase", "laptop", "cell phone", "bicycle"}
EDGE_MARGIN_PX = 40
PROXIMITY_PX = 120
DISAPPEAR_WINDOW_SEC = 3.0
LOITER_SECONDS = 15.0
LOITER_RADIUS_PX = 80


def load_tracks(csv_path):
    tracks = defaultdict(list)
    with open(csv_path, newline="") as f:
        for row in csv.DictReader(f):
            tracks[int(row["track_id"])].append(row)
    for tid in tracks:
        tracks[tid].sort(key=lambda r: int(r["frame"]))
    return tracks


def dist(a, b):
    return math.hypot(float(a["cx"]) - float(b["cx"]), float(a["cy"]) - float(b["cy"]))


def analyze(csv_path, frame_width, frame_height):
    tracks = load_tracks(csv_path)
    events = []

    person_tracks = {tid: rows for tid, rows in tracks.items() if rows[0]["class_name"] == "person"}
    object_tracks = {tid: rows for tid, rows in tracks.items() if rows[0]["class_name"] in VALUABLE_CLASSES}

    for obj_id, rows in object_tracks.items():
        last = rows[-1]
        x, y = float(last["cx"]), float(last["cy"])
        near_edge = (x < EDGE_MARGIN_PX or x > frame_width - EDGE_MARGIN_PX or
                     y < EDGE_MARGIN_PX or y > frame_height - EDGE_MARGIN_PX)
        if near_edge:
            continue

        disappear_time = float(last["timestamp_sec"])
        class_name = last["class_name"]
        linked_person = None

        for p_id, p_rows in person_tracks.items():
            p_end_time = float(p_rows[-1]["timestamp_sec"])
            if abs(p_end_time - disappear_time) > DISAPPEAR_WINDOW_SEC:
                continue
            for obj_row in rows[-10:]:
                for p_row in p_rows:
                    if p_row["frame"] == obj_row["frame"] and dist(obj_row, p_row) < PROXIMITY_PX:
                        linked_person = p_id
                        break
                if linked_person:
                    break
            if linked_person:
                break

        if linked_person:
            events.append({
                "type": "possible_removal", "severity": "high", "timestamp_sec": disappear_time,
                "object_track_id": obj_id, "object_class": class_name, "person_track_id": linked_person,
                "description": f"{class_name} (id {obj_id}) vanished near person (id {linked_person}) who left around the same time.",
            })
        else:
            events.append({
                "type": "object_disappeared", "severity": "medium", "timestamp_sec": disappear_time,
                "object_track_id": obj_id, "object_class": class_name, "person_track_id": None,
                "description": f"{class_name} (id {obj_id}) disappeared mid-frame with no clear cause.",
            })

    for p_id, rows in person_tracks.items():
        start, end = rows[0], rows[-1]
        duration = float(end["timestamp_sec"]) - float(start["timestamp_sec"])
        if duration < LOITER_SECONDS:
            continue
        cx0, cy0 = float(start["cx"]), float(start["cy"])
        max_drift = max(math.hypot(float(r["cx"]) - cx0, float(r["cy"]) - cy0) for r in rows)
        if max_drift < LOITER_RADIUS_PX:
            events.append({
                "type": "loitering", "severity": "low", "timestamp_sec": float(start["timestamp_sec"]),
                "object_track_id": None, "object_class": None, "person_track_id": p_id,
                "description": f"Person (id {p_id}) stayed in roughly the same spot for {duration:.1f}s.",
            })

    events.sort(key=lambda e: e["timestamp_sec"])
    return events