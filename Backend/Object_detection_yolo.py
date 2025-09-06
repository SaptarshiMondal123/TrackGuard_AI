import cv2
import time
import os
import math
import uuid
import numpy as np
import pandas as pd
from pathlib import Path
from ultralytics import YOLO
import folium

# Config
MODEL_PATH = r"C:\Users\SAPTARSHI MONDAL\SnakeGame\Model\yolov8m-worldv2.pt"
INPUT_PATH = r"C:\Users\SAPTARSHI MONDAL\SnakeGame\Video\Screen Recording 2025-09-04 121451.mp4"

OUT_DIR = "outputs"
os.makedirs(OUT_DIR, exist_ok=True)

# performance
FRAME_SKIP = 2
BATCH_SIZE = 6
IMG_SIZE = 640

# braking / risk
K_CALIB = 4200.0
REACTION_TIME = 1.0
DECEL = 1.2  # safer braking
WARNING_DIST = 150.0
BRAKE_DIST = 60.0
PERSISTENCE_FRAMES = 3
FORGET_FRAMES = 12  # reset stale tracks

CLASS_WEIGHT = {
    "person": 1.0, "car": 0.9, "truck": 1.1, "motorcycle": 0.95, "bicycle": 0.95,
    "cow": 1.2, "buffalo": 1.2, "dog": 1.1, "sheep": 1.15, "goat": 1.15,
    "elephant": 1.3, "train": 2.0, "animal": 1.3
}

# Filtering settings
WHITELIST_CLASSES = set(CLASS_WEIGHT.keys())
IGNORED_CLASSES = {"traffic light", "toothbrush", "surfboard", "snowboard", "boat", "banana", "bottle", "chair"}
MIN_CONF_DEFAULT = 0.40
MIN_BBOX_HEIGHT_PX = 30
MIN_BBOX_AREA_PX = 1500
ROI_CENTER_X_RATIO = (0.20, 0.80)  # wider central corridor
ROI_MIN_BOTTOM_RATIO = 0.40       # lower 60% of frame

# GPS route (simulated)
TRAIN_ROUTE = [
    (22.5726, 88.3639), (22.5742, 88.3658), (22.5760, 88.3676),
    (22.5782, 88.3690), (22.5800, 88.3705), (22.5820, 88.3720),
    (22.5838, 88.3735), (22.5855, 88.3750),
]
def get_gps_from_route(frame_count): return TRAIN_ROUTE[frame_count % len(TRAIN_ROUTE)]

# helpers
def estimate_distance_from_bbox(bbox, k_calib=K_CALIB, min_cap=2.0, max_cap=300.0):
    x1, y1, x2, y2 = bbox
    h = max(1.0, (y2 - y1))
    d = k_calib / h
    return float(np.clip(d, min_cap, max_cap))

def stopping_distance(speed_kmph):
    v = speed_kmph / 3.6
    return v * REACTION_TIME + (v ** 2) / (2 * DECEL)

def risk_score(distance, conf, cls, speed_kmph):
    d_norm = np.clip(1.0 - (distance / 500.0), 0.0, 1.0)
    c_norm = np.clip(conf, 0.0, 1.0)
    s_norm = np.clip(speed_kmph / 200.0, 0.0, 1.0)
    cw = CLASS_WEIGHT.get(cls, 1.0)
    score = (0.6 * d_norm + 0.25 * c_norm + 0.15 * s_norm) * 100.0 * cw
    return float(np.clip(score, 0, 100))

def ai_decision(distance, ttc, speed_kmph, cls):
    safe_stop = stopping_distance(speed_kmph)
    if distance <= safe_stop * 0.8 or ttc <= 5:
        return "BRAKE_EMERGENCY"
    elif distance <= safe_stop * 1.5:
        return "SLOW_DOWN"
    elif distance <= WARNING_DIST:
        return "CAUTION"
    return "CLEAR"

def center_of_bbox(bbox):
    x1, y1, x2, y2 = bbox
    return ((x1+x2)/2.0, (y1+y2)/2.0)

def bbox_area(bbox):
    x1, y1, x2, y2 = bbox
    return max(0, x2-x1) * max(0, y2-y1)

def is_in_rail_roi(bbox, frame_shape):
    h, w = frame_shape[:2]
    cx, cy = center_of_bbox(bbox)
    if not (ROI_CENTER_X_RATIO[0]*w <= cx <= ROI_CENTER_X_RATIO[1]*w):
        return False
    _, _, _, y2 = bbox
    if (y2 / h) < ROI_MIN_BOTTOM_RATIO:
        return False
    return True

# persistence tracker
persistence = {}  # key -> {count, last}

# recent thumbnails buffer for HUD (keep last N crops)
RECENT_THUMBNAILS = []
MAX_THUMBNAILS = 5

# HUD drawing
def draw_hud(frame, speed_kmph, overall_decision, overall_risk, thumbnails):
    """Draws a simple in-cab HUD: speed, risk bar, decision strip, thumbnails."""
    h, w = frame.shape[:2]
    # translucent panel
    overlay = frame.copy()
    cv2.rectangle(overlay, (0,0), (w, 110), (10,10,10), -1)
    alpha = 0.45
    cv2.addWeighted(overlay, alpha, frame, 1-alpha, 0, frame)

    # Title
    cv2.putText(frame, "TrackGuard HUD", (12, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)

    # Speed display (left)
    sp_x = 12
    sp_y = 48
    cv2.putText(frame, f"Speed: {int(speed_kmph)} km/h", (sp_x, sp_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200,200,255), 2)
    # small gauge arc
    center = (sp_x+80, sp_y+55)
    radius = 40
    # background arc
    cv2.ellipse(frame, center, (radius, radius), 180, 0, 180, (50,50,50), 8)
    # needle angle map: speed 0..200 -> angle 0..180
    angle = int(np.clip(speed_kmph, 0, 200) / 200.0 * 180.0)
    # compute needle endpoint
    theta = math.radians(180 - angle)
    nx = int(center[0] + radius * math.cos(theta))
    ny = int(center[1] - radius * math.sin(theta))
    cv2.line(frame, center, (nx,ny), (0,255,255), 3)
    cv2.circle(frame, center, 4, (255,255,255), -1)

    # Decision strip (center)
    ds_x = int(w*0.3)
    ds_y = 18
    ds_w = int(w*0.4)
    ds_h = 34
    # background
    cv2.rectangle(frame, (ds_x, ds_y), (ds_x+ds_w, ds_y+ds_h), (30,30,30), -1)
    # colored indicator
    color_map = {
        "CLEAR": (0,200,0),
        "CAUTION": (0,165,255),
        "SLOW_DOWN": (0,165,255),
        "BRAKE_EMERGENCY": (0,0,255)
    }
    col = color_map.get(overall_decision, (200,200,200))
    cv2.putText(frame, f"Decision: {overall_decision}", (ds_x+8, ds_y+24), cv2.FONT_HERSHEY_SIMPLEX, 0.8, col, 2)

    # Risk bar (right)
    rb_x = w - 220
    rb_y = 18
    rb_w = 200
    rb_h = 34
    cv2.rectangle(frame, (rb_x, rb_y), (rb_x+rb_w, rb_y+rb_h), (40,40,40), -1)
    cv2.putText(frame, f"Risk: {int(overall_risk)}%", (rb_x+8, rb_y+24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
    # filled bar
    fill_w = int((overall_risk/100.0) * (rb_w-8))
    cv2.rectangle(frame, (rb_x+4, rb_y+6), (rb_x+4+fill_w, rb_y+rb_h-6), (0,0,255) if overall_risk>70 else (0,165,255) if overall_risk>30 else (0,200,0), -1)

    # Thumbnails (right-side vertical)
    thumb_x = w - 160
    thumb_y = 120
    thumb_w = 140
    thumb_h = 80
    spacing = 8
    for i, img in enumerate(thumbnails[-MAX_THUMBNAILS:]):
        # resize thumbnail
        th = cv2.resize(img, (thumb_w, thumb_h))
        ty = thumb_y + i*(thumb_h + spacing)
        if ty + thumb_h > h - 10: break
        frame[ty:ty+thumb_h, thumb_x:thumb_x+thumb_w] = th
        cv2.rectangle(frame, (thumb_x, ty), (thumb_x+thumb_w, ty+thumb_h), (200,200,200), 2)
        cv2.putText(frame, f"#{len(thumbnails)-len(thumbnails[-MAX_THUMBNAILS:])+i+1}", (thumb_x+6, ty+18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)

    return frame

# pipeline
def main():
    model = YOLO(MODEL_PATH)  # CPU only

    is_video = os.path.isfile(INPUT_PATH)
    if is_video:
        cap = cv2.VideoCapture(INPUT_PATH)
        if not cap.isOpened():
            raise SystemExit("Cannot open input video")
        out_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        out_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        out_fps = max(10, int(cap.get(cv2.CAP_PROP_FPS) or 20))
        out_path = f"{OUT_DIR}/output_obstacle_fast_hud.mp4"
        out_writer = cv2.VideoWriter(out_path, cv2.VideoWriter_fourcc(*"mp4v"), out_fps, (out_w, out_h))
    else:
        image_files = sorted(Path(INPUT_PATH).glob("*.*"))

    alerts = []
    frame_count = 0
    start_t = time.time()
    batch_frames, batch_orig = [], []

    # local speed used for calculations (simulate or read from metadata)
    SIM_SPEED_KMPH = 80.0

    while True:
        if is_video:
            ok, frame = cap.read()
            if not ok: break
        else:
            if frame_count >= len(image_files): break
            frame = cv2.imread(str(image_files[frame_count]))

        frame_count += 1
        if frame_count % FRAME_SKIP != 0:
            continue

        h, w = frame.shape[:2]
        resized = cv2.resize(frame, (IMG_SIZE, IMG_SIZE))
        batch_frames.append(resized)
        batch_orig.append(frame)

        if len(batch_frames) >= BATCH_SIZE:
            results = model.predict(batch_frames, imgsz=IMG_SIZE, conf=0.30, verbose=False, device='cpu')
            for idx, r in enumerate(results):
                orig = batch_orig[idx]
                scale_x = orig.shape[1] / IMG_SIZE
                scale_y = orig.shape[0] / IMG_SIZE

                filtered_dets = []
                if r.boxes is not None and len(r.boxes) > 0:
                    xyxy = r.boxes.xyxy.cpu().numpy()
                    cls_ids = r.boxes.cls.cpu().numpy().astype(int)
                    confs = r.boxes.conf.cpu().numpy()
                    names = r.names

                    for box, cid, conf in zip(xyxy, cls_ids, confs):
                        cls_name = names.get(int(cid), str(cid)).lower()
                        if cls_name in IGNORED_CLASSES: continue
                        if cls_name not in WHITELIST_CLASSES: continue
                        if conf < MIN_CONF_DEFAULT: continue

                        x1, y1, x2, y2 = box
                        x1 *= scale_x; x2 *= scale_x; y1 *= scale_y; y2 *= scale_y
                        bbox = [x1, y1, x2, y2]

                        if (y2-y1) < MIN_BBOX_HEIGHT_PX or bbox_area(bbox) < MIN_BBOX_AREA_PX:
                            continue
                        if not is_in_rail_roi(bbox, orig.shape):
                            continue

                        key = (cls_name, int(center_of_bbox(bbox)[0]//20), int(center_of_bbox(bbox)[1]//20))
                        st = persistence.get(key, {"count":0, "last":0})
                        st["count"] += 1
                        st["last"] = frame_count
                        persistence[key] = st

                        # forget old tracks
                        if frame_count - st["last"] > FORGET_FRAMES:
                            persistence.pop(key, None)

                        if st["count"] >= PERSISTENCE_FRAMES:
                            filtered_dets.append({"bbox":bbox, "cls":cls_name, "conf":float(conf)})

                # compute per-frame overall metrics
                per_frame_risks = []
                per_frame_decisions = []
                current_thumbs = []

                draw_frame = orig.copy()
                for d in filtered_dets:
                    dist = estimate_distance_from_bbox(d["bbox"])
                    ttc = dist / max(0.1, SIM_SPEED_KMPH/3.6)
                    score = risk_score(dist, d["conf"], d["cls"], SIM_SPEED_KMPH)
                    decision = ai_decision(dist, ttc, SIM_SPEED_KMPH, d["cls"])

                    x1,y1,x2,y2 = map(int, d["bbox"])
                    color = (0,255,0) if decision=="CLEAR" else \
                            (0,165,255) if decision in ["SLOW_DOWN","CAUTION"] else \
                            (0,0,255)
                    cv2.rectangle(draw_frame, (x1,y1), (x2,y2), color, 2)
                    cv2.putText(draw_frame, f"{d['cls']} {d['conf']:.2f} {decision}", (x1, max(20,y1-5)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

                    if decision != "CLEAR":
                        crop = orig[max(0,y1):min(orig.shape[0],y2), max(0,x1):min(orig.shape[1],x2)]
                        crop_name = f"{OUT_DIR}/{frame_count}_{d['cls']}_{uuid.uuid4().hex[:6]}.jpg"
                        if crop.size > 0:
                            cv2.imwrite(crop_name, crop)
                            # save thumbnail in memory for HUD
                            thumb = cv2.resize(crop, (140,80))
                            RECENT_THUMBNAILS.append(thumb)
                            # also keep current_thumbs
                            current_thumbs.append(thumb)
                        alerts.append({
                            "time_s": round(time.time()-start_t,2),
                            "frame": frame_count,
                            "label": d["cls"],
                            "conf": round(d["conf"],2),
                            "distance_m": round(dist,1),
                            "ttc_s": round(ttc,1),
                            "decision": decision,
                            "risk_score": round(score,1),
                            "lat": get_gps_from_route(frame_count)[0],
                            "lon": get_gps_from_route(frame_count)[1],
                            "crop": crop_name
                        })

                    per_frame_risks.append(score)
                    per_frame_decisions.append(decision)

                # overall decision logic for HUD (worst-case)
                if len(per_frame_risks) == 0:
                    overall_risk = 0.0
                    overall_decision = "CLEAR"
                else:
                    overall_risk = float(np.clip(max(per_frame_risks), 0, 100))
                    # priority: BRAKE_EMERGENCY > SLOW_DOWN > CAUTION > CLEAR
                    if any(d=="BRAKE_EMERGENCY" for d in per_frame_decisions):
                        overall_decision = "BRAKE_EMERGENCY"
                    elif any(d=="SLOW_DOWN" for d in per_frame_decisions):
                        overall_decision = "SLOW_DOWN"
                    elif any(d=="CAUTION" for d in per_frame_decisions):
                        overall_decision = "CAUTION"
                    else:
                        overall_decision = "CLEAR"

                # draw HUD on top of draw_frame
                hud_frame = draw_hud(draw_frame, SIM_SPEED_KMPH, overall_decision, overall_risk, RECENT_THUMBNAILS)

                out_writer.write(hud_frame)

            batch_frames.clear()
            batch_orig.clear()

    if is_video:
        cap.release()
        out_writer.release()

    if alerts:
        pd.DataFrame(alerts).to_csv(f"{OUT_DIR}/alerts_obstacle.csv", index=False)

    m = folium.Map(location=TRAIN_ROUTE[0], zoom_start=14)
    for a in alerts:
        color = "red" if "BRAKE" in a["decision"] else \
                "orange" if a["decision"] in ["SLOW_DOWN","CAUTION"] else \
                "green"
        folium.Marker([a["lat"], a["lon"]],
                      popup=f"{a['label']} {a['distance_m']}m Risk:{a['risk_score']}",
                      icon=folium.Icon(color=color)).add_to(m)
    m.save(f"{OUT_DIR}/map.html")
    print("✅ Done — outputs in", OUT_DIR)


if __name__ == "__main__":
    main()
