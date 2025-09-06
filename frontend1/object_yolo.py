import cv2
import time
import os
import numpy as np
import pandas as pd
from ultralytics import YOLO
from pathlib import Path
import folium

# Distance & Braking Logic
def estimate_distance_from_bbox(bbox, k_calib=4200.0, min_cap=2.0, max_cap=300.0):
    x1, y1, x2, y2 = bbox
    h = max(1.0, (y2 - y1))
    d = k_calib / h
    return float(np.clip(d, min_cap, max_cap))

def braking_distance_m(speed_kmph, reaction_time_s, decel_mps2):
    v = max(0.0, speed_kmph) / 3.6
    return v * reaction_time_s + (v * v) / (2.0 * max(0.1, decel_mps2))

def should_brake(distance_to_fault_m, speed_kmph, reaction_time_s, decel_mps2):
    return distance_to_fault_m <= braking_distance_m(speed_kmph, reaction_time_s, decel_mps2)

train_route = [
    (22.5726, 88.3639),  # Sealdah
    (22.5742, 88.3658),
    (22.5760, 88.3676),
    (22.5782, 88.3690),
    (22.5800, 88.3705),
    (22.5820, 88.3720),
    (22.5838, 88.3735),
    (22.5855, 88.3750),  # Near Dum Dum
]

# Get current GPS based on frame count
def get_gps_from_route(frame_count):
    idx = frame_count % len(train_route)
    return train_route[idx]

# YOLO Detection
def run_yolo(model, frame, conf=0.35, target_classes=None):
    results = model.predict(frame, conf=conf, verbose=False)
    detections = []
    if results:
        r = results[0]
        names = r.names
        for xyxy, cls_id, conf_score in zip(r.boxes.xyxy, r.boxes.cls, r.boxes.conf):
            label = names.get(int(cls_id), str(int(cls_id)))
            if target_classes and label.lower() not in [c.lower() for c in target_classes]:
                continue
            detections.append({
                "bbox": xyxy.cpu().numpy().tolist(),
                "cls": label,
                "conf": float(conf_score)
            })
    return detections

def draw_boxes(frame, dets, color, label_prefix=""):
    for d in dets:
        x1, y1, x2, y2 = map(int, d["bbox"])
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        txt = f'{label_prefix}{d["cls"]} {d["conf"]:.2f}'
        cv2.putText(frame, txt, (x1, max(20, y1 - 5)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

# Main
if __name__ == "__main__":
    model_path = r"C:\Users\SAPTARSHI MONDAL\PycharmProjects\CarbonModel\Model\yolov8m-worldv2.pt"  # pre-trained or fine-tuned
    input_path = r"C:\Users\SAPTARSHI MONDAL\PycharmProjects\CarbonModel\Video\Screen Recording 2025-09-04 094340.mp4"      # video or folder

    target_classes = [
        "person", "car", "truck", "motorcycle", "bicycle",
        "cow", "buffalo", "dog", "sheep", "goat", "elephant",
        "train", "animal"
    ]

    conf_th = 0.35
    k_calib = 4200.0
    speed_kmph = 80.0
    reaction_time = 1.0
    decel = 1.0
    gps_lat, gps_lon = 22.5726, 88.3639
    gps_step_m = 1.0

    # ===== Load Model =====
    print("Loading obstacle detection model...")
    model = YOLO(model_path)
    print("✅ Model loaded.")

    alerts = []
    frame_count = 0
    start_t = time.time()

    # Video or Image Processing
    if os.path.isfile(input_path):
        cap = cv2.VideoCapture(input_path)
        out_video = cv2.VideoWriter("output_obstacle.mp4",
                                    cv2.VideoWriter_fourcc(*"mp4v"), 20,
                                    (int(cap.get(3)), int(cap.get(4))))
        is_video = True
    else:
        image_files = sorted(Path(input_path).glob("*.*"))
        is_video = False

    print("▶ Processing started...")
    while True:
        if is_video:
            ok, frame = cap.read()
            if not ok:
                break
        else:
            if frame_count >= len(image_files):
                break
            frame = cv2.imread(str(image_files[frame_count]))

        frame_count += 1
        draw_frame = frame.copy()

        # Run detection
        detections = run_yolo(model, frame, conf=conf_th, target_classes=target_classes)
        draw_boxes(draw_frame, detections, color=(0, 255, 0), label_prefix="OBS: ")

        # Calculate braking logic
        distances = []
        for d in detections:
            dist = estimate_distance_from_bbox(d["bbox"], k_calib=k_calib)
            d["distance_m"] = dist
            distances.append((d["cls"], dist, d["conf"]))

        if distances:
            nearest = sorted(distances, key=lambda x: x[1])[0]
            label, dist_m, conf_score = nearest
            brake = should_brake(dist_m, speed_kmph, reaction_time, decel)
            decision = "BRAKE" if brake else "SAFE"
            print(f"[{frame_count}] {label} at {dist_m:.1f}m — {decision}")
            alerts.append({
                "t": round(time.time() - start_t, 2),
                "label": label,
                "distance_m": round(dist_m, 1),
                "decision": decision,
                "lat": gps_lat,
                "lon": gps_lon
            })

        # Save frame
        if is_video:
            out_video.write(draw_frame)
        else:
            cv2.imwrite(f"frame_{frame_count:04d}.jpg", draw_frame)

        gps_lat, gps_lon = get_gps_from_route(frame_count)


    if is_video:
        cap.release()
        out_video.release()

    pd.DataFrame(alerts).to_csv("alerts_obstacle.csv", index=False)
    print("\n✅ Obstacle detection finished — Output: output_obstacle.mp4, Log: alerts_obstacle.csv")

    # === Generate Fake GPS Map ===
    print("Generating fake GPS map...")
    m = folium.Map(location=[22.5726, 88.3639], zoom_start=14)
    for alert in alerts:
        color = "red" if alert["decision"] == "BRAKE" else "green"
        folium.Marker(
            location=[alert["lat"], alert["lon"]],
            popup=f"{alert['label']} - {alert['decision']} - {alert['distance_m']}m",
            icon=folium.Icon(color=color)
        ).add_to(m)
    m.save("track_fault_map.html")
    print("✅ Map saved as track_fault_map.html")
