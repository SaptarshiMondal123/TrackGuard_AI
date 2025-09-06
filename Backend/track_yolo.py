from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
import uvicorn
import cv2, os, time, shutil
import numpy as np
import pandas as pd
from ultralytics import YOLO
from pathlib import Path
import folium

# ====== FastAPI app ======
app = FastAPI()

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ===== Distance & Risk Logic =====
def braking_distance_m(speed_kmph, reaction_time_s, decel_mps2):
    v = max(0.0, speed_kmph) / 3.6
    return v * reaction_time_s + (v * v) / (2.0 * max(0.1, decel_mps2))

def risk_score(distance_to_fault_m, speed_kmph, reaction_time_s, decel_mps2):
    bd = braking_distance_m(speed_kmph, reaction_time_s, decel_mps2)
    score = max(0.0, 100.0 * (1 - (distance_to_fault_m / (2 * bd))))
    score = float(np.clip(score, 0, 100))
    if distance_to_fault_m > 2 * bd:
        level = "SAFE"
    elif distance_to_fault_m > bd:
        level = "CAUTION"
    else:
        level = "DANGER"
    return level, score

# Fake GPS
train_route = [
    (22.5726, 88.3639), (22.5742, 88.3658), (22.5760, 88.3676),
    (22.5782, 88.3690), (22.5800, 88.3705), (22.5820, 88.3720),
    (22.5838, 88.3735), (22.5855, 88.3750),
]
def get_gps_from_route(frame_count):
    idx = frame_count % len(train_route)
    return train_route[idx]

# YOLO wrapper
def run_yolo(model, frame, conf=0.35):
    results = model.predict(frame, conf=conf, verbose=False)
    detections = []
    if results:
        r = results[0]
        names = r.names
        for xyxy, cls_id, conf_score in zip(r.boxes.xyxy, r.boxes.cls, r.boxes.conf):
            detections.append({
                "bbox": xyxy.cpu().numpy().tolist(),
                "cls": names.get(int(cls_id), str(int(cls_id))),
                "conf": float(conf_score)
            })
    return detections

def draw_boxes(frame, dets):
    for d in dets:
        x1, y1, x2, y2 = map(int, d["bbox"])
        risk = d.get("decision", "UNK")
        color = (0,255,0) if risk=="SAFE" else (0,255,255) if risk=="CAUTION" else (0,0,255)
        txt = f'{d["cls"]} {d["conf"]:.2f} {risk} {d.get("risk_pct",0):.0f}%'
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, txt, (x1, max(20, y1 - 5)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

# ===== Load Model (once) =====
MODEL_PATH = r"C:\Users\SAPTARSHI MONDAL\SnakeGame\Model\track_fault_detection.pt"
model = YOLO(MODEL_PATH)

# ===== Analyze Endpoint =====
@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    conf_th = 0.35
    speed_kmph, reaction_time, decel = 80.0, 1.0, 1.0

    alerts = []
    frame_count = 0
    start_t = time.time()

    # Check type
    is_video = file.filename.lower().endswith((".mp4", ".avi", ".mov"))

    out_video_path, out_image_path = None, None

    if is_video:
        cap = cv2.VideoCapture(file_path)
        out_video_path = os.path.join(OUTPUT_DIR, "output_track_fault.mp4")
        out_video = cv2.VideoWriter(out_video_path,
                                    cv2.VideoWriter_fourcc(*"avc1"), 20,
                                    (int(cap.get(3)), int(cap.get(4))))
    else:
        image = cv2.imread(file_path)
        out_image_path = os.path.join(OUTPUT_DIR, "output_track_fault.jpg")
        frames = [image]

    while True:
        if is_video:
            ok, frame = cap.read()
            if not ok: break
        else:
            if frame_count >= len(frames): break
            frame = frames[frame_count]

        frame_count += 1
        draw_frame = frame.copy()
        detections = run_yolo(model, frame, conf=conf_th)

        for d in detections:
            dist = 50.0
            d["distance_m"] = dist
            d["decision"], d["risk_pct"] = risk_score(dist, speed_kmph, reaction_time, decel)

        draw_boxes(draw_frame, detections)

        gps_lat, gps_lon = get_gps_from_route(frame_count)
        for d in detections:
            alerts.append({
                "t": round(time.time() - start_t, 2),
                "label": d["cls"],
                "distance_m": round(d["distance_m"], 1),
                "decision": d["decision"],
                "risk_pct": d["risk_pct"],
                "lat": gps_lat,
                "lon": gps_lon
            })

        if is_video:
            out_video.write(draw_frame)
        else:
            cv2.imwrite(out_image_path, draw_frame)

    if is_video:
        cap.release()
        out_video.release()

    # Save CSV
    csv_path = os.path.join(OUTPUT_DIR, "alerts_track_fault.csv")
    pd.DataFrame(alerts).to_csv(csv_path, index=False)

    # Save Map
    map_path = os.path.join(OUTPUT_DIR, "track_fault_map.html")
    m = folium.Map(location=[22.5726, 88.3639], zoom_start=14)
    for alert in alerts:
        color = "green" if alert["decision"]=="SAFE" else "orange" if alert["decision"]=="CAUTION" else "red"
        folium.Marker(
            location=[alert["lat"], alert["lon"]],
            popup=f"{alert['label']} - {alert['decision']} ({alert['risk_pct']:.0f}%) - {alert['distance_m']}m",
            icon=folium.Icon(color=color)
        ).add_to(m)
    m.save(map_path)

    return JSONResponse({
        "message": "Analysis complete",
        "csv": "/download/csv",
        "map": "/download/map",
        "video": "/download/video" if is_video else None,
        "image": "/download/image" if not is_video else None
    })

# ===== Download Endpoints =====
@app.get("/download/csv")
async def download_csv():
    return FileResponse(os.path.join(OUTPUT_DIR, "alerts_track_fault.csv"))

@app.get("/download/map")
async def download_map():
    return FileResponse(os.path.join(OUTPUT_DIR, "track_fault_map.html"))

@app.get("/download/video")
async def download_video():
    path = os.path.join(OUTPUT_DIR, "output_track_fault.mp4")
    if os.path.exists(path):
        return FileResponse(path)
    return JSONResponse({"error": "No video available"}, status_code=404)

@app.get("/download/image")
async def download_image():
    path = os.path.join(OUTPUT_DIR, "output_track_fault.jpg")
    if os.path.exists(path):
        return FileResponse(path)
    return JSONResponse({"error": "No image available"}, status_code=404)

# ===== Run =====
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
