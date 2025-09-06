# inference.py
import os
import time
import uuid
import math
from pathlib import Path

import cv2 # type: ignore
import numpy as np # type: ignore
import pandas as pd # type: ignore
import folium # type: ignore
from ultralytics import YOLO # type: ignore

import subprocess

def convert_to_avc1(input_path, output_path):
    """Re-encode video with ffmpeg to ensure browser-compatible AVC1 codec."""
    subprocess.run([
        "ffmpeg", "-y", "-i", str(input_path),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-pix_fmt", "yuv420p",
        str(output_path)
    ], check=True)

# ---------------- CONFIG ----------------
MODEL_PATH = r"C:\Users\SAPTARSHI MONDAL\SnakeGame\Model\yolov8m-worldv2.pt"
OUT_DIR = "outputs"
os.makedirs(OUT_DIR, exist_ok=True)

# performance
FRAME_SKIP = 2
BATCH_SIZE = 6
IMG_SIZE = 640
FORGET_FRAMES = 12

# braking / risk (used in scoring/decision)
K_CALIB = 4200.0
REACTION_TIME = 1.0
DECEL = 1.2
WARNING_DIST = 150.0
BRAKE_DIST = 60.0
PERSISTENCE_FRAMES = 3

CLASS_WEIGHT = {
    "person": 1.0, "car": 0.9, "truck": 1.1, "motorcycle": 0.95, "bicycle": 0.95,
    "cow": 1.2, "buffalo": 1.2, "dog": 1.1, "sheep": 1.15, "goat": 1.15,
    "elephant": 1.3, "train": 2.0, "animal": 1.3
}
WHITELIST_CLASSES = set(CLASS_WEIGHT.keys())
IGNORED_CLASSES = {"traffic light", "chair", "bottle", "banana"}
MIN_CONF_DEFAULT = 0.40
MIN_BBOX_HEIGHT_PX = 30
MIN_BBOX_AREA_PX = 1500
ROI_CENTER_X_RATIO = (0.20, 0.80)
ROI_MIN_BOTTOM_RATIO = 0.40

# Simulated GPS route (for map markers)
TRAIN_ROUTE = [
    (22.5726, 88.3639), (22.5742, 88.3658), (22.5760, 88.3676),
    (22.5782, 88.3690), (22.5800, 88.3705), (22.5820, 88.3720),
    (22.5838, 88.3735), (22.5855, 88.3750),
]
def get_gps_from_route(frame_count):
    return TRAIN_ROUTE[frame_count % len(TRAIN_ROUTE)]

# ---------------- load model once ----------------
# (Ultralytics will auto-download if model path is a known name, but we use local path)
model = YOLO(MODEL_PATH)

# ---------------- helpers ----------------
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

def ai_decision(distance, ttc, speed_kmph, cls=None):
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
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)

def bbox_area(bbox):
    x1, y1, x2, y2 = bbox
    return max(0, x2 - x1) * max(0, y2 - y1)

def is_in_rail_roi(bbox, frame_shape):
    h, w = frame_shape[:2]
    cx, _ = center_of_bbox(bbox)
    if not (ROI_CENTER_X_RATIO[0] * w <= cx <= ROI_CENTER_X_RATIO[1] * w):
        return False
    _, _, _, y2 = bbox
    if (y2 / h) < ROI_MIN_BOTTOM_RATIO:
        return False
    return True

# ---------------- HUD drawing ----------------
def draw_hud(frame, speed_kmph, overall_decision, overall_risk, thumbnails):
    h, w = frame.shape[:2]
    # translucent panel on top
    overlay = frame.copy()
    cv2.rectangle(overlay, (0,0), (w,110), (10,10,10), -1)
    alpha = 0.45
    cv2.addWeighted(overlay, alpha, frame, 1-alpha, 0, frame)

    # title
    cv2.putText(frame, "TrackGuard HUD", (12, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)

    # Speed text
    sp_x, sp_y = 12, 48
    cv2.putText(frame, f"Speed: {int(speed_kmph)} km/h", (sp_x, sp_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200,200,255), 2)

    # small gauge arc
    center = (sp_x+80, sp_y+55)
    radius = 40
    cv2.ellipse(frame, center, (radius, radius), 180, 0, 180, (50,50,50), 8)
    angle = int(np.clip(speed_kmph, 0, 200) / 200.0 * 180.0)
    theta = math.radians(180 - angle)
    nx = int(center[0] + radius * math.cos(theta))
    ny = int(center[1] - radius * math.sin(theta))
    cv2.line(frame, center, (nx, ny), (0,255,255), 3)
    cv2.circle(frame, center, 4, (255,255,255), -1)

    # Decision strip
    ds_x = int(w*0.3); ds_y = 18; ds_w = int(w*0.4); ds_h = 34
    cv2.rectangle(frame, (ds_x, ds_y), (ds_x+ds_w, ds_y+ds_h), (30,30,30), -1)
    color_map = {"CLEAR": (0,200,0), "CAUTION": (0,165,255), "SLOW_DOWN": (0,165,255), "BRAKE_EMERGENCY": (0,0,255)}
    col = color_map.get(overall_decision, (200,200,200))
    cv2.putText(frame, f"Decision: {overall_decision}", (ds_x+8, ds_y+24), cv2.FONT_HERSHEY_SIMPLEX, 0.8, col, 2)

    # Risk bar (right)
    rb_x = w - 220; rb_y = 18; rb_w = 200; rb_h = 34
    cv2.rectangle(frame, (rb_x, rb_y), (rb_x+rb_w, rb_y+rb_h), (40,40,40), -1)
    cv2.putText(frame, f"Risk: {int(overall_risk)}%", (rb_x+8, rb_y+24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)
    fill_w = int((overall_risk/100.0) * (rb_w-8))
    bar_color = (0,0,255) if overall_risk>70 else (0,165,255) if overall_risk>30 else (0,200,0)
    cv2.rectangle(frame, (rb_x+4, rb_y+6), (rb_x+4+fill_w, rb_y+rb_h-6), bar_color, -1)

    # Thumbnails
    thumb_x = w - 160; thumb_y = 120; thumb_w = 140; thumb_h = 80; spacing = 8
    for i, img in enumerate(thumbnails[-5:]):
        try:
            th = cv2.resize(img, (thumb_w, thumb_h))
        except Exception:
            continue
        ty = thumb_y + i*(thumb_h + spacing)
        if ty + thumb_h > h - 10: break
        frame[ty:ty+thumb_h, thumb_x:thumb_x+thumb_w] = th
        cv2.rectangle(frame, (thumb_x, ty), (thumb_x+thumb_w, ty+thumb_h), (200,200,200), 2)
        cv2.putText(frame, f"#{len(thumbnails)-len(thumbnails[-5:])+i+1}", (thumb_x+6, ty+18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 1)

    return frame

# ---------------- Main pipeline (exposed) ----------------
def run_inference(input_path: str, sim_speed: float = 80.0, device: str = "cpu") -> dict:
    """
    Run the full TrackGuard pipeline on a video file.
    Returns dict with sessionized paths: video, csv, map, snaps_dir
    """
    out_video = f"{OUT_DIR}/output.mp4"
    out_csv = f"{OUT_DIR}/alerts.csv"
    out_map = f"{OUT_DIR}/map.html"
    snaps_dir = f"{OUT_DIR}/snaps"
    os.makedirs(snaps_dir, exist_ok=True)

    # Video reader/writer setup
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open input {input_path}")

    out_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    out_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out_fps = max(10, int(cap.get(cv2.CAP_PROP_FPS) or 20))
    writer = cv2.VideoWriter(out_video, cv2.VideoWriter_fourcc(*"avc1"), out_fps, (out_w, out_h))

    alerts = []
    persistence = {}   # (cls, gx, gy) -> {count, last_frame}
    RECENT_THUMBNAILS = []

    batch_frames = []
    batch_orig = []
    frame_count = 0
    start_t = time.time()

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            frame_count += 1
            if frame_count % FRAME_SKIP != 0:
                continue

            orig = frame.copy()
            h, w = orig.shape[:2]
            resized = cv2.resize(orig, (IMG_SIZE, IMG_SIZE))
            batch_frames.append(resized)
            batch_orig.append(orig)

            # When batch ready or at end
            if len(batch_frames) >= BATCH_SIZE:
                results = model.predict(batch_frames, imgsz=IMG_SIZE, conf=0.30, verbose=False, device=device)
                for idx, r in enumerate(results):
                    frame_orig = batch_orig[idx]
                    scale_x = frame_orig.shape[1] / IMG_SIZE
                    scale_y = frame_orig.shape[0] / IMG_SIZE

                    filtered_dets = []
                    if getattr(r, "boxes", None) is not None and len(r.boxes) > 0:
                        xyxy = r.boxes.xyxy.cpu().numpy()
                        cls_ids = r.boxes.cls.cpu().numpy().astype(int)
                        confs = r.boxes.conf.cpu().numpy()
                        names = r.names

                        for box, cid, conf in zip(xyxy, cls_ids, confs):
                            cls_name = names.get(int(cid), str(cid)).lower()
                            if cls_name in IGNORED_CLASSES:
                                continue
                            if cls_name not in WHITELIST_CLASSES:
                                continue
                            if conf < MIN_CONF_DEFAULT:
                                continue

                            x1, y1, x2, y2 = box
                            x1 *= scale_x; x2 *= scale_x; y1 *= scale_y; y2 *= scale_y
                            bbox = [x1, y1, x2, y2]

                            if (y2 - y1) < MIN_BBOX_HEIGHT_PX or bbox_area(bbox) < MIN_BBOX_AREA_PX:
                                continue
                            if not is_in_rail_roi(bbox, frame_orig.shape):
                                continue

                            gx = int(center_of_bbox(bbox)[0] // 20)
                            gy = int(center_of_bbox(bbox)[1] // 20)
                            key = (cls_name, gx, gy)
                            st = persistence.get(key, {"count":0, "last":0})
                            # forget stale
                            if frame_count - st["last"] > FORGET_FRAMES:
                                st = {"count":0, "last":0}

                            st["count"] += 1
                            st["last"] = frame_count
                            persistence[key] = st

                            if st["count"] >= PERSISTENCE_FRAMES:
                                filtered_dets.append({"bbox": bbox, "cls": cls_name, "conf": float(conf)})

                    # Draw + decisions for this frame
                    draw_frame = frame_orig.copy()
                    per_frame_risks = []
                    per_frame_decisions = []
                    for d in filtered_dets:
                        dist = estimate_distance_from_bbox(d["bbox"])
                        ttc = dist / max(0.1, sim_speed / 3.6)
                        score = risk_score(dist, d["conf"], d["cls"], sim_speed)
                        decision = ai_decision(dist, ttc, sim_speed, d["cls"])

                        x1, y1, x2, y2 = map(int, d["bbox"])
                        color = (0,255,0) if decision=="CLEAR" else (0,165,255) if decision in ["SLOW_DOWN","CAUTION"] else (0,0,255)
                        cv2.rectangle(draw_frame, (x1,y1), (x2,y2), color, 2)
                        cv2.putText(draw_frame, f"{d['cls']} {d['conf']:.2f} {decision}", (x1, max(20,y1-5)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

                        if decision != "CLEAR":
                            # save crop and thumbnail
                            crop = frame_orig[max(0,y1):min(frame_orig.shape[0],y2), max(0,x1):min(frame_orig.shape[1],x2)]
                            if crop.size > 0:
                                crop_name = f"{snaps_dir}/{frame_count}_{d['cls']}_{uuid.uuid4().hex[:6]}.jpg"
                                cv2.imwrite(crop_name, crop)
                                try:
                                    thumb = cv2.resize(crop, (140, 80))
                                    RECENT_THUMBNAILS.append(thumb)
                                except Exception:
                                    pass

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
                            })

                        per_frame_risks.append(score)
                        per_frame_decisions.append(decision)

                    # overall frame-level decision (worst-case)
                    if not per_frame_risks:
                        overall_risk = 0.0
                        overall_decision = "CLEAR"
                    else:
                        overall_risk = float(np.clip(max(per_frame_risks), 0, 100))
                        if any(d == "BRAKE_EMERGENCY" for d in per_frame_decisions):
                            overall_decision = "BRAKE_EMERGENCY"
                        elif any(d == "SLOW_DOWN" for d in per_frame_decisions):
                            overall_decision = "SLOW_DOWN"
                        elif any(d == "CAUTION" for d in per_frame_decisions):
                            overall_decision = "CAUTION"
                        else:
                            overall_decision = "CLEAR"

                    # draw HUD (uses RECENT_THUMBNAILS)
                    hud_frame = draw_hud(draw_frame, sim_speed, overall_decision, overall_risk, RECENT_THUMBNAILS)
                    writer.write(hud_frame)

                # clear batch
                batch_frames.clear()
                batch_orig.clear()

        # end while
    finally:
        cap.release()
        writer.release()

    # handle any leftover frames in batch (if any)
    if batch_frames:
        results = model.predict(batch_frames, imgsz=IMG_SIZE, conf=0.30, verbose=False, device=device)
        for idx, r in enumerate(results):
            frame_orig = batch_orig[idx]
            scale_x = frame_orig.shape[1] / IMG_SIZE
            scale_y = frame_orig.shape[0] / IMG_SIZE

            filtered_dets = []
            if getattr(r, "boxes", None) is not None and len(r.boxes) > 0:
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
                    if (y2 - y1) < MIN_BBOX_HEIGHT_PX or bbox_area(bbox) < MIN_BBOX_AREA_PX: continue
                    if not is_in_rail_roi(bbox, frame_orig.shape): continue

                    gx = int(center_of_bbox(bbox)[0] // 20)
                    gy = int(center_of_bbox(bbox)[1] // 20)
                    key = (cls_name, gx, gy)
                    st = persistence.get(key, {"count":0, "last":0})
                    if frame_count - st["last"] > FORGET_FRAMES:
                        st = {"count":0, "last":0}
                    st["count"] += 1
                    st["last"] = frame_count
                    persistence[key] = st
                    if st["count"] >= PERSISTENCE_FRAMES:
                        filtered_dets.append({"bbox": bbox, "cls": cls_name, "conf": float(conf)})

            # draw and write similar to above (simplified)
            draw_frame = frame_orig.copy()
            per_frame_risks = []; per_frame_decisions = []
            for d in filtered_dets:
                dist = estimate_distance_from_bbox(d["bbox"])
                ttc = dist / max(0.1, sim_speed / 3.6)
                score = risk_score(dist, d["conf"], d["cls"], sim_speed)
                decision = ai_decision(dist, ttc, sim_speed, d["cls"])
                x1,y1,x2,y2 = map(int, d["bbox"])
                color = (0,255,0) if decision=="CLEAR" else (0,165,255) if decision in ["SLOW_DOWN","CAUTION"] else (0,0,255)
                cv2.rectangle(draw_frame, (x1,y1), (x2,y2), color, 2)
                cv2.putText(draw_frame, f"{d['cls']} {d['conf']:.2f} {decision}", (x1, max(20,y1-5)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                if decision != "CLEAR":
                    crop = frame_orig[max(0,y1):min(frame_orig.shape[0],y2), max(0,x1):min(frame_orig.shape[1],x2)]
                    if crop.size > 0:
                        crop_name = f"{snaps_dir}/{frame_count}_{d['cls']}_{uuid.uuid4().hex[:6]}.jpg"
                        cv2.imwrite(crop_name, crop)
                        try:
                            RECENT_THUMBNAILS.append(cv2.resize(crop, (140,80)))
                        except Exception:
                            pass
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
                    })
                per_frame_risks.append(score); per_frame_decisions.append(decision)

            if not per_frame_risks:
                overall_risk=0.0; overall_decision="CLEAR"
            else:
                overall_risk = float(np.clip(max(per_frame_risks),0,100))
                if any(d=="BRAKE_EMERGENCY" for d in per_frame_decisions): overall_decision="BRAKE_EMERGENCY"
                elif any(d=="SLOW_DOWN" for d in per_frame_decisions): overall_decision="SLOW_DOWN"
                elif any(d=="CAUTION" for d in per_frame_decisions): overall_decision="CAUTION"
                else: overall_decision="CLEAR"

            hud_frame = draw_hud(draw_frame, sim_speed, overall_decision, overall_risk, RECENT_THUMBNAILS)
            writer.write(hud_frame)

        # Save CSV
        if alerts:
            pd.DataFrame(alerts).to_csv(out_csv, index=False)
        else:
            pd.DataFrame([{"frame":0, "event":"No issues"}]).to_csv(out_csv, index=False)

        # Save map with markers
        m = folium.Map(location=TRAIN_ROUTE[0], zoom_start=14)
        for a in alerts:
            color = "red" if "BRAKE" in a["decision"] else ("orange" if a["decision"]=="SLOW_DOWN" else "green")
            folium.Marker([a["lat"], a["lon"]],
                          popup=f"{a['label']} {a['distance_m']}m Risk:{a['risk_score']}",
                          icon=folium.Icon(color=color)).add_to(m)
        m.save(out_map)

        # 🔧 Convert video for browser playback
        final_video = f"{OUT_DIR}/output_avc1.mp4"
        convert_to_avc1(out_video, final_video)

        return {"video": final_video, "csv": out_csv, "map": out_map, "snaps": snaps_dir}

# If you want to test this module standalone:
if __name__ == "__main__":
    demo_in = "test_video.mp4"  # change to a real file to test
    if Path(demo_in).exists():
        print("Running demo inference...")
        res = run_inference(demo_in, sim_speed=80.0, device="cpu")
        print("Done. Artifacts:", res)
    else:
        print("No demo video found. Place a test_video.mp4 or call run_inference from your API.")
