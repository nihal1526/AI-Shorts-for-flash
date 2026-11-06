import os
import subprocess
from pathlib import Path
from typing import Optional
from backend.config import TEMP_DIR, RENDERED_DIR
from backend.subtitle_generator import generate_ass_subtitles

def escape_ffmpeg_path(path_str: str) -> str:
    """Escape file path for FFmpeg filter argument on Windows."""
    # FFmpeg requires forward slashes and escaped colons in filter graph paths
    clean = str(Path(path_str).resolve()).replace('\\', '/')
    clean = clean.replace(':', r'\:')
    return clean

def render_vertical_short(
    input_video_path: str,
    output_video_path: str,
    layout_mode: str = "blur_fill",
    ass_subtitle_path: Optional[str] = None
) -> str:
    """
    Render 9:16 vertical (1080x1920) YouTube Short using FFmpeg.
    Layout options:
      - 'blur_fill': 16:9 video centered with aesthetically blurred background filling 9:16
      - 'smart_crop': 9:16 centered crop filling entire screen
      - 'letterbox': Centered with black borders
    """
    input_path = str(Path(input_video_path).resolve())
    output_path = str(Path(output_video_path).resolve())
    
    # 1. Base video filter graph for 9:16 framing
    if layout_mode == "smart_crop":
        # Scale to match height 1920, then crop width to 1080
        filter_graph = "scale=-2:1920,crop=1080:1920:(in_w-1080)/2:0"
    elif layout_mode == "letterbox":
        # Fit inside 1080x1920 and pad with black
        filter_graph = "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black"
    else: # Default: blur_fill
        # Background: scaled and cropped to 1080x1920 with boxblur.
        # Foreground: scaled to 1080 width preserving aspect ratio, centered.
        filter_graph = (
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:5[bg];"
            "[0:v]scale=1080:-2:force_original_aspect_ratio=decrease[fg];"
            "[bg][fg]overlay=(W-w)/2:(H-h)/2"
        )

    # 2. Add subtitle burning filter if provided
    if ass_subtitle_path and os.path.exists(ass_subtitle_path):
        escaped_ass = escape_ffmpeg_path(ass_subtitle_path)
        if layout_mode == "blur_fill":
            filter_graph += f"[vfinal];[vfinal]ass='{escaped_ass}'"
        else:
            filter_graph += f",ass='{escaped_ass}'"

    # 3. Build FFmpeg command
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-filter_complex" if layout_mode == "blur_fill" else "-vf", filter_graph,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "22",
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "44100",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output_path
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        # If ass filter had an issue (e.g. font missing), retry without subtitles
        if "ass" in filter_graph:
            simple_filter = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"
            fallback_cmd = [
                "ffmpeg", "-y",
                "-i", input_path,
                "-vf", simple_filter,
                "-c:v", "libx264", "-preset", "ultrafast",
                "-c:a", "aac",
                output_path
            ]
            subprocess.run(fallback_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            raise RuntimeError(f"FFmpeg error: {result.stderr[-500:]}")

    return output_path

def extract_thumbnail_frame(video_path: str, output_image_path: str, time_sec: float = 1.5) -> str:
    """Extract a high-quality keyframe snapshot for YouTube Shorts thumbnail."""
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(time_sec),
        "-i", video_path,
        "-vframes", "1",
        "-q:v", "2",
        output_image_path
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return output_image_path
