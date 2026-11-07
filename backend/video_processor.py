import os
import subprocess
from pathlib import Path
from typing import Optional, Tuple
from backend.config import TEMP_DIR, RENDERED_DIR
from backend.subtitle_generator import generate_ass_subtitles

def escape_ffmpeg_path(path_str: str) -> str:
    """Escape file path for FFmpeg filter argument on Windows."""
    clean = str(Path(path_str).resolve()).replace('\\', '/')
    clean = clean.replace(':', r'\:')
    return clean

def detect_speaker_x_offset(video_path: str) -> Tuple[int, int, int]:
    """
    Analyze video frames with OpenCV to detect the speaker's face/body center
    and calculate optimal 9:16 crop offset.
    Returns: (crop_x, crop_width, height)
    """
    try:
        import cv2
        import numpy as np

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return 0, 0, 0

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if width <= 0 or height <= 0:
            cap.release()
            return 0, 0, 0

        # Target 9:16 crop width for input height
        crop_w = int(height * (9.0 / 16.0))
        if crop_w % 2 != 0:
            crop_w -= 1

        if crop_w >= width:
            cap.release()
            return 0, width, height

        # Sample 4 frames near the beginning of the clip for ultra-fast speaker positioning
        sample_indices = [
            int(min(total_frames - 1, 20)),
            int(min(total_frames - 1, 45)),
            int(min(total_frames - 1, 75)),
            int(min(total_frames - 1, 110))
        ]
        sample_indices = [i for i in sample_indices if i >= 0]
        detected_x_centers = []

        for f_idx in sample_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(f_idx))
            ret, frame = cap.read()
            if not ret or frame is None:
                continue

            # Focus on upper half (where human faces and heads reside)
            upper_half = frame[0:int(height * 0.65), :]

            # Convert to HSV for skin-tone and human presence detection
            hsv = cv2.cvtColor(upper_half, cv2.COLOR_BGR2HSV)
            # Standard human skin tone range in HSV
            lower_skin = np.array([0, 30, 60], dtype=np.uint8)
            upper_skin = np.array([25, 255, 255], dtype=np.uint8)
            mask = cv2.inRange(hsv, lower_skin, upper_skin)

            # Find center of mass of the skin mask
            moments = cv2.moments(mask)
            if moments["m00"] > 500:
                cx = int(moments["m10"] / moments["m00"])
                detected_x_centers.append(cx)

        cap.release()

        if detected_x_centers:
            # Use median speaker X coordinate to ignore outliers
            median_x = int(np.median(detected_x_centers))
            # Center the 9:16 box on speaker
            target_x = median_x - (crop_w // 2)
            # Clamp inside boundaries [0, width - crop_w]
            clamped_x = max(0, min(width - crop_w, target_x))
            if clamped_x % 2 != 0:
                clamped_x -= 1
            print(f"[FaceTracking] Detected speaker center X: {median_x} -> Crop X: {clamped_x} (Width: {crop_w}, Height: {height})")
            return clamped_x, crop_w, height

    except Exception as e:
        print(f"[FaceTracking] Error during face tracking: {e}")

    # Fallback to center
    return -1, 0, 0

def render_vertical_short(
    input_video_path: str,
    output_video_path: str,
    layout_mode: str = "face_tracking",
    ass_subtitle_path: Optional[str] = None
) -> str:
    """
    Render 1080x1920 High-Resolution 9:16 vertical YouTube Short using FFmpeg.
    Layout options:
      - 'face_tracking' / 'smart_crop': Auto-centers on speaker's face using OpenCV detection
      - 'blur_fill': 16:9 video centered with aesthetically blurred background filling 9:16
      - 'letterbox': Centered with black borders
    """
    input_path = str(Path(input_video_path).resolve())
    output_path = str(Path(output_video_path).resolve())

    # 1. Base video filter graph for 9:16 framing
    if layout_mode in ["face_tracking", "smart_crop"]:
        crop_x, crop_w, h = detect_speaker_x_offset(input_path)
        if crop_x >= 0 and crop_w > 0:
            # Dynamic speaker-centered crop scaled to crisp 1080x1920 HD with fast bicubic scaling
            filter_graph = f"crop={crop_w}:{h}:{crop_x}:0,scale=1080:1920:flags=bicubic"
        else:
            # Full-bleed 9:16 center crop filling the entire 1080x1920 screen with zero black bars
            filter_graph = "crop=ih*(9/16):ih:(iw-ow)/2:0,scale=1080:1920:flags=bicubic"

    elif layout_mode == "letterbox":
        filter_graph = "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black"

    else: # Default: blur_fill
        filter_graph = (
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=15:3[bg];"
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

    # 3. High-Resolution 1080x1920 MP4 encoding parameters (optimized for ultra-fast render)
    cmd = [
        "ffmpeg", "-y",
        "-threads", "0",            # Utilize all CPU cores simultaneously
        "-i", input_path,
        "-filter_complex" if layout_mode == "blur_fill" else "-vf", filter_graph,
        "-c:v", "libx264",
        "-preset", "veryfast",      # 3x faster encoding with crisp high quality
        "-crf", "20",               # Visually indistinguishable from source, much faster render
        "-c:a", "aac",
        "-b:a", "192k",
        "-ar", "48000",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output_path
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
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
