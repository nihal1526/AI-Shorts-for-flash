import os
import uuid
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.config import (
    FRONTEND_DIR, DOWNLOADS_DIR, RENDERED_DIR, TEMP_DIR, 
    SUBTITLE_PRESETS, APIFY_API_TOKEN, ASSEMBLYAI_API_KEY
)
from backend.youtube_downloader import (
    get_video_info, get_transcript, download_video_clip_fast, clean_youtube_url
)
from backend.virality_engine import find_viral_clips
from backend.metadata_generator import generate_shorts_metadata
from backend.subtitle_generator import generate_ass_subtitles
from backend.video_processor import render_vertical_short, extract_thumbnail_frame

app = FastAPI(
    title="FlashKlap - Free AI YouTube Shorts Generator",
    description="Turn long YouTube videos into viral YouTube Shorts for free like Klap.app"
)

# Enable CORS for flexible local & cloud deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for active session jobs
JOBS: Dict[str, Dict[str, Any]] = {}

class AnalyzeRequest(BaseModel):
    url: str
    max_clips: Optional[int] = 4
    min_duration: Optional[int] = 25
    max_duration: Optional[int] = 58
    api_key: Optional[str] = None
    apify_token: Optional[str] = None
    assemblyai_key: Optional[str] = None

class RenderRequest(BaseModel):
    url: str
    clip_id: str
    start_time: float
    end_time: float
    hook_text: str
    full_text: str
    words: Optional[List[Dict[str, Any]]] = []
    segments: Optional[List[Dict[str, Any]]] = []
    layout_mode: Optional[str] = "blur_fill"  # 'blur_fill', 'smart_crop', 'letterbox'
    subtitle_style: Optional[str] = "hormozi" # 'hormozi', 'cyber_cyan', 'emerald', 'clean_white'
    uppercase: Optional[bool] = True
    apify_token: Optional[str] = None

@app.get("/api/health")
async def health():
    return {"status": "ok", "app": "FlashKlap AI", "version": "1.0.0"}

@app.get("/api/presets")
async def get_presets():
    return {
        "subtitle_styles": SUBTITLE_PRESETS,
        "layout_modes": [
            {"id": "blur_fill", "name": "Blur Fill (Podcast / Landscape)", "description": "16:9 video centered with aesthetically blurred background. No cutoff!"},
            {"id": "smart_crop", "name": "Smart 9:16 Center Crop", "description": "Full-bleed vertical crop filling the entire phone screen."},
            {"id": "letterbox", "name": "Fit with Letterbox", "description": "Classic clean letterbox with black bars."}
        ]
    }

@app.post("/api/analyze")
async def analyze_video(req: AnalyzeRequest):
    """Analyze YouTube video, fetch transcript, extract viral moments and generate Shorts upload kit."""
    url = clean_youtube_url(req.url)
    if not url:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL provided.")

    try:
        # Step 1: Fetch Video Information
        video_info = get_video_info(url)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch video info: {str(e)}")

    try:
        # Step 2: Fetch Subtitles / Transcript (Native YouTube or AssemblyAI)
        segments = get_transcript(url, assemblyai_key=req.assemblyai_key or ASSEMBLYAI_API_KEY)
    except Exception as e:
        segments = []

    if not segments:
        # If no transcript found, create placeholder highlight based on video length
        duration = min(video_info.get("duration", 60), 300)
        sample_step = max(30.0, duration / 3.0)
        segments = [
            {"start": 0.0, "end": min(duration, 45.0), "text": video_info.get("title", "High energy moment in this video"), "words": []},
            {"start": min(duration, 50.0), "end": min(duration, 95.0), "text": "Key takeaway and most important lesson", "words": []}
        ]

    # Step 3: AI Virality Engine - Extract Top Clips
    clips = find_viral_clips(
        segments=segments,
        min_duration=float(req.min_duration or 25),
        max_duration=float(req.max_duration or 58),
        target_count=req.max_clips or 4
    )

    # Step 4: Generate YouTube Shorts Upload Kit for each clip
    enriched_clips = []
    for c in clips:
        upload_kit = generate_shorts_metadata(c, video_info)
        c["upload_kit"] = upload_kit
        enriched_clips.append(c)

    job_id = str(uuid.uuid4())[:8]
    JOBS[job_id] = {
        "video_info": video_info,
        "clips": enriched_clips,
        "url": url
    }

    return {
        "job_id": job_id,
        "video_info": video_info,
        "clips_count": len(enriched_clips),
        "clips": enriched_clips
    }

@app.post("/api/render-clip")
async def render_clip(req: RenderRequest):
    """Render selected clip into a ready-to-upload 9:16 Shorts MP4 with subtitles."""
    task_id = str(uuid.uuid4())[:10]
    raw_clip_filename = f"raw_{task_id}.mp4"
    rendered_filename = f"short_{task_id}.mp4"
    ass_filename = f"subs_{task_id}.ass"
    thumb_filename = f"thumb_{task_id}.jpg"

    raw_path = str(DOWNLOADS_DIR / raw_clip_filename)
    rendered_path = str(RENDERED_DIR / rendered_filename)
    ass_path = str(TEMP_DIR / ass_filename)
    thumb_path = str(RENDERED_DIR / thumb_filename)

    try:
        # 1. Download only the specific section fast (via Apify actor streamers/youtube-video-downloader or local fallback)
        download_video_clip_fast(
            url=req.url,
            start_sec=req.start_time,
            end_sec=req.end_time,
            output_path=raw_path,
            apify_token=req.apify_token or APIFY_API_TOKEN
        )

        # 2. Generate ASS dynamic subtitles
        segments = req.segments if req.segments else [{
            "start": req.start_time,
            "end": req.end_time,
            "text": req.full_text,
            "words": req.words
        }]
        
        ass_content = generate_ass_subtitles(
            segments=segments,
            clip_start=req.start_time,
            clip_end=req.end_time,
            style_name=req.subtitle_style or "hormozi",
            uppercase=req.uppercase if req.uppercase is not None else True
        )

        with open(ass_path, "w", encoding="utf-8") as f:
            f.write(ass_content)

        # 3. Render 9:16 vertical short using FFmpeg
        render_vertical_short(
            input_video_path=raw_path,
            output_video_path=rendered_path,
            layout_mode=req.layout_mode or "blur_fill",
            ass_subtitle_path=ass_path
        )

        # 4. Extract thumbnail snapshot
        extract_thumbnail_frame(rendered_path, thumb_path, time_sec=1.5)

        return {
            "status": "success",
            "video_url": f"/api/video/{rendered_filename}",
            "download_url": f"/api/download/{rendered_filename}",
            "thumbnail_url": f"/api/thumbnail/{thumb_filename}",
            "filename": rendered_filename
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rendering failed: {str(e)}")

@app.get("/api/video/{filename}")
async def get_video(filename: str):
    file_path = RENDERED_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found.")
    return FileResponse(file_path, media_type="video/mp4")

@app.get("/api/download/{filename}")
async def download_video(filename: str):
    file_path = RENDERED_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(
        file_path, 
        media_type="application/octet-stream", 
        filename=f"YouTube_Short_{filename}"
    )

@app.get("/api/thumbnail/{filename}")
async def get_thumbnail(filename: str):
    file_path = RENDERED_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Thumbnail not found.")
    return FileResponse(file_path, media_type="image/jpeg")

# Serve frontend static assets
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(FRONTEND_DIR / "index.html")

    @app.get("/styles.css")
    async def serve_styles():
        return FileResponse(FRONTEND_DIR / "styles.css", media_type="text/css")

    @app.get("/app.js")
    async def serve_app_js():
        return FileResponse(FRONTEND_DIR / "app.js", media_type="application/javascript")

