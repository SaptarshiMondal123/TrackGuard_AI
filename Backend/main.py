from fastapi import FastAPI, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.concurrency import run_in_threadpool
from pathlib import Path
import shutil
import mimetypes

from inference import run_inference  # your inference function

app = FastAPI(title="TrackGuard API", version="1.0")

# Directories
BASE_DIR = Path(__file__).parent.resolve()
UPLOAD_DIR = BASE_DIR / "uploads"
OUT_DIR = BASE_DIR / "outputs"
UPLOAD_DIR.mkdir(exist_ok=True)
OUT_DIR.mkdir(exist_ok=True)

CHUNK_SIZE = 1024 * 1024  # 1MB
STREAM_THRESHOLD = 10 * 1024 * 1024  # 10MB


def iterfile(path: Path):
    """Stream a file in chunks."""
    with open(path, "rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            yield chunk


@app.post("/analyze")
async def analyze_video(file: UploadFile, speed: float = Form(80.0)):
    """Upload video -> run inference -> return artifact download URLs."""
    dest = UPLOAD_DIR / Path(file.filename).name

    with open(dest, "wb") as out_f:
        shutil.copyfileobj(file.file, out_f)

    # Run inference
    try:
        results = await run_in_threadpool(run_inference, str(dest), float(speed), "cpu")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {e}")

    artifacts = {
        "video": "/download/video",
        "csv": "/download/csv",
        "map": "/download/map",
    }

    return JSONResponse(content={"message": "Analysis complete", "artifacts": artifacts})


# ---------------- DOWNLOAD ENDPOINTS ---------------- #

@app.get("/download/video")
async def download_video():
    """Download processed video (MP4, AVC1 browser-compatible)."""
    video_file = OUT_DIR / "output_avc1.mp4"
    if not video_file.exists():
        raise HTTPException(status_code=404, detail="Video not found")

    return FileResponse(
        video_file,
        media_type="video/mp4",
        filename="output.mp4"   # still downloads as output.mp4, but codec-safe
    )

@app.get("/download/csv")
async def download_csv():
    """Download alerts CSV (fixed filename)."""
    csv_file = OUT_DIR / "alerts.csv"
    if not csv_file.exists():
        raise HTTPException(status_code=404, detail="CSV not found")
    return FileResponse(csv_file, media_type="text/csv")


@app.get("/download/map")
async def download_map():
    """Download analysis map (fixed filename)."""
    map_file = OUT_DIR / "map.html"
    if not map_file.exists():
        raise HTTPException(status_code=404, detail="Map not found")
    return FileResponse(map_file, media_type="text/html")