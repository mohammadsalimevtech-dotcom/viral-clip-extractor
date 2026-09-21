import os
import uuid
import shutil
import threading
import traceback

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.transcriber import transcribe
from app.analyzer import find_viral_clips
from app.clipper import cut_clip, segments_to_srt

app = FastAPI(title="Viral Clip Extractor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten this to your frontend's domain in production
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(settings.output_dir, exist_ok=True)
os.makedirs(settings.download_dir, exist_ok=True)
app.mount("/clips", StaticFiles(directory=settings.output_dir), name="clips")

# Simple in-memory job store. For real production traffic, swap this for
# Redis + a proper task queue (Celery / RQ) -- see README.
JOBS: dict[str, dict] = {}


def process_job(job_id: str, video_path: str, video_title: str, burn_captions: bool):
    """Shared pipeline: transcribe -> find viral moments -> cut clips."""
    try:
        JOBS[job_id]["status"] = "transcribing"
        segments = transcribe(video_path)

        JOBS[job_id]["status"] = "analyzing"
        viral_clips = find_viral_clips(segments)

        JOBS[job_id]["status"] = "cutting"
        results = []
        for i, clip in enumerate(viral_clips):
            clip_id = f"{job_id}_{i}"
            out_path = os.path.join(settings.output_dir, f"{clip_id}.mp4")

            srt_path = None
            if burn_captions:
                srt_path = os.path.join(settings.output_dir, f"{clip_id}.srt")
                segments_to_srt(segments, clip["start"], clip["end"], srt_path)

            cut_clip(
                video_path, clip["start"], clip["end"], out_path,
                burn_subtitles=srt_path if burn_captions else None,
            )

            results.append({
                **clip,
                "clip_id": clip_id,
                "download_url": f"/clips/{clip_id}.mp4",
            })

        JOBS[job_id]["status"] = "done"
        JOBS[job_id]["video_title"] = video_title
        JOBS[job_id]["clips"] = results

    except Exception as e:
        JOBS[job_id]["status"] = "failed"
        JOBS[job_id]["error"] = str(e)
        traceback.print_exc()
    finally:
        # Clean up the uploaded source file once processing is done
        try:
            if os.path.exists(video_path):
                os.remove(video_path)
        except OSError:
            pass


@app.post("/jobs/upload")
def create_job_from_upload(
    file: UploadFile = File(...),
    burn_captions: bool = Form(True),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    job_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1] or ".mp4"
    dest_path = os.path.join(settings.download_dir, f"{job_id}{ext}")

    with open(dest_path, "wb") as out_file:
        shutil.copyfileobj(file.file, out_file)

    title = os.path.splitext(file.filename)[0]

    JOBS[job_id] = {"status": "queued", "clips": []}

    thread = threading.Thread(
        target=process_job, args=(job_id, dest_path, title, burn_captions), daemon=True
    )
    thread.start()

    return {"job_id": job_id}


@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/")
def root():
    return {"status": "ok", "service": "Viral Clip Extractor API"}
                
