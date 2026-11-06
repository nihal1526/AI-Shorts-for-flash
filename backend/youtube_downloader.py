import os
import json
import re
import urllib.request
from typing import Dict, Any, List, Optional
import yt_dlp
from backend.config import TEMP_DIR, DOWNLOADS_DIR

def clean_youtube_url(url: str) -> str:
    """Normalize YouTube URL to standard watch or share format."""
    url = url.strip()
    # Handle shorts URL: https://www.youtube.com/shorts/VIDEO_ID
    shorts_match = re.search(r'youtube\.com/shorts/([a-zA-Z0-9_-]+)', url)
    if shorts_match:
        return f"https://www.youtube.com/watch?v={shorts_match.group(1)}"
    return url

def get_video_info(url: str) -> Dict[str, Any]:
    """Fetch video metadata without downloading video stream."""
    url = clean_youtube_url(url)
    ydl_opts = {
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        
        # Pick highest resolution thumbnail
        thumbnails = info.get('thumbnails', [])
        thumbnail_url = info.get('thumbnail')
        if thumbnails:
            # Sort by width or preference
            valid_thumbs = [t for t in thumbnails if t.get('url')]
            if valid_thumbs:
                thumbnail_url = valid_thumbs[-1]['url']
        
        duration = info.get('duration', 0)
        minutes, seconds = divmod(duration, 60)
        hours, minutes = divmod(minutes, 60)
        if hours > 0:
            duration_str = f"{int(hours)}:{int(minutes):02d}:{int(seconds):02d}"
        else:
            duration_str = f"{int(minutes):02d}:{int(seconds):02d}"

        return {
            "id": info.get('id'),
            "title": info.get('title', 'Unknown Title'),
            "channel": info.get('uploader') or info.get('channel', 'Unknown Creator'),
            "channel_url": info.get('uploader_url') or info.get('channel_url', ''),
            "duration": duration,
            "duration_str": duration_str,
            "thumbnail": thumbnail_url,
            "view_count": info.get('view_count', 0),
            "description": (info.get('description') or '')[:500],
            "webpage_url": info.get('webpage_url', url),
            "subtitles": bool(info.get('subtitles') or info.get('automatic_captions'))
        }

def parse_json3_subtitles(json_data: dict) -> List[Dict[str, Any]]:
    """Parse YouTube JSON3 subtitle format into structured timed segments with word data."""
    events = json_data.get('events', [])
    segments = []

    for event in events:
        if 'segs' not in event or 'tStartMs' not in event:
            continue
        
        start_ms = event['tStartMs']
        duration_ms = event.get('dDurationMs', 0)
        end_ms = start_ms + duration_ms
        
        # Combine segments into text and extract word tokens
        full_text = ""
        words = []
        curr_offset_ms = 0
        
        for seg in event.get('segs', []):
            text = seg.get('utf8', '')
            if text == '\n':
                continue
            full_text += text
            t_offset = seg.get('tOffsetMs', curr_offset_ms)
            curr_offset_ms = t_offset
            
            clean_word = text.strip()
            if clean_word:
                word_start = (start_ms + t_offset) / 1000.0
                words.append({
                    "word": clean_word,
                    "start": word_start,
                    "end": word_start + max(0.2, (seg.get('dDurationMs', 300) / 1000.0))
                })
        
        clean_full_text = full_text.strip().replace('\n', ' ')
        if clean_full_text:
            segments.append({
                "start": start_ms / 1000.0,
                "end": end_ms / 1000.0,
                "text": clean_full_text,
                "words": words
            })

    return segments

def parse_vtt_subtitles(vtt_text: str) -> List[Dict[str, Any]]:
    """Parse WebVTT subtitle text into timed segments."""
    segments = []
    lines = vtt_text.splitlines()
    i = 0
    time_regex = re.compile(r'(\d{2}:\d{2}:\d{2}\.\d{3}|\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3}|\d{2}:\d{2}\.\d{3})')

    def to_seconds(t_str: str) -> float:
        parts = t_str.strip().split(':')
        if len(parts) == 3:
            h, m, s = parts
            return int(h) * 3600 + int(m) * 60 + float(s)
        elif len(parts) == 2:
            m, s = parts
            return int(m) * 60 + float(s)
        return 0.0

    while i < len(lines):
        line = lines[i].strip()
        match = time_regex.search(line)
        if match:
            start_sec = to_seconds(match.group(1))
            end_sec = to_seconds(match.group(2))
            i += 1
            text_lines = []
            while i < len(lines) and lines[i].strip() and not time_regex.search(lines[i]):
                # Remove html/formatting tags like <c> </c>
                clean_line = re.sub(r'<[^>]+>', '', lines[i].strip())
                if clean_line:
                    text_lines.append(clean_line)
                i += 1
            
            raw_text = " ".join(text_lines).strip()
            if raw_text:
                # Synthesize word timing for dynamic subtitles
                word_tokens = raw_text.split()
                words = []
                if word_tokens:
                    duration = max(0.5, end_sec - start_sec)
                    step = duration / len(word_tokens)
                    for idx, w in enumerate(word_tokens):
                        words.append({
                            "word": w,
                            "start": round(start_sec + idx * step, 2),
                            "end": round(start_sec + (idx + 1) * step, 2)
                        })

                segments.append({
                    "start": start_sec,
                    "end": end_sec,
                    "text": raw_text,
                    "words": words
                })
        else:
            i += 1

    return segments

def get_transcript(url: str, assemblyai_key: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieve transcript with word-level subtitles.
    1. Checks native YouTube captions (json3/vtt).
    2. If missing or if AssemblyAI key is provided, transcribes audio using AssemblyAI.
    """
    url = clean_youtube_url(url)
    ydl_opts = {
        'skip_download': True,
        'quiet': True,
        'no_warnings': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        
        subs = info.get('subtitles') or {}
        auto_subs = info.get('automatic_captions') or {}
        all_subs = {**auto_subs, **subs}
        lang_keys = list(all_subs.keys())

        # If native YouTube captions exist, use them
        if lang_keys:
            chosen_key = None
            for pref in ['en', 'en-US', 'en-GB', 'en-auto']:
                if pref in lang_keys:
                    chosen_key = pref
                    break
            if not chosen_key:
                chosen_key = lang_keys[0]

            formats = all_subs.get(chosen_key, [])
            json3_url = next((f['url'] for f in formats if f.get('ext') == 'json3'), None)
            vtt_url = next((f['url'] for f in formats if f.get('ext') == 'vtt'), None)
            req_headers = {'User-Agent': 'Mozilla/5.0'}

            if json3_url:
                try:
                    req = urllib.request.Request(json3_url, headers=req_headers)
                    with urllib.request.urlopen(req, timeout=15) as resp:
                        data = json.loads(resp.read().decode('utf-8'))
                        return parse_json3_subtitles(data)
                except Exception:
                    pass

            if vtt_url:
                try:
                    req = urllib.request.Request(vtt_url, headers=req_headers)
                    with urllib.request.urlopen(req, timeout=15) as resp:
                        data = resp.read().decode('utf-8')
                        return parse_vtt_subtitles(data)
                except Exception:
                    pass

        # If no native captions or AssemblyAI key provided: use AssemblyAI
        from backend.config import ASSEMBLYAI_API_KEY
        key_to_use = assemblyai_key or ASSEMBLYAI_API_KEY
        if key_to_use:
            try:
                from backend.assemblyai_transcriber import transcribe_with_assemblyai
                # Find an audio stream URL
                formats = info.get('formats', [])
                audio_stream = next((f['url'] for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none'), None)
                if not audio_stream and formats:
                    audio_stream = formats[-1].get('url')
                
                if audio_stream:
                    print("[AssemblyAI] Transcribing stream via AssemblyAI...")
                    res = transcribe_with_assemblyai(audio_stream, key_to_use)
                    if res.get("segments"):
                        return res["segments"]
            except Exception as e:
                print(f"[AssemblyAI] Fallback transcription error: {e}")

    return []

def download_with_apify(url: str, apify_token: str, output_path: str) -> Optional[str]:
    """
    Download YouTube video using Apify Actor: streamers/youtube-video-downloader
    """
    try:
        from apify_client import ApifyClient
        import requests
        
        url = clean_youtube_url(url)
        print(f"[Apify] Initializing download with Apify actor streamers/youtube-video-downloader for {url}")
        client = ApifyClient(apify_token.strip())

        run_input = { 
            "videos": [{ "url": url }]
        }

        # Run the actor and wait for it to finish
        run = client.actor("streamers/youtube-video-downloader").call(run_input=run_input)
        if not run or "default_dataset_id" not in run:
            print("[Apify] Actor run did not return a default_dataset_id")
            return None

        # Fetch results from the run's dataset
        dataset_id = run["default_dataset_id"] if isinstance(run, dict) else getattr(run, "default_dataset_id")
        for item in client.dataset(dataset_id).iterate_items():
            # Check for direct media download URL in dataset
            media_url = (
                item.get("downloadedFileUrl") or
                item.get("downloadUrl") or 
                item.get("mediaUrl") or 
                item.get("fileUrl") or 
                item.get("videoOnlyUrl") or
                item.get("url") or 
                item.get("videoUrl")
            )
            if media_url and isinstance(media_url, str) and (media_url.startswith("http://") or media_url.startswith("https://")):
                print(f"[Apify] Streaming video from Apify dataset asset: {media_url[:80]}...")
                with requests.get(media_url, stream=True, timeout=120) as r:
                    r.raise_for_status()
                    with open(output_path, "wb") as f:
                        for chunk in r.iter_content(chunk_size=1024 * 1024):
                            if chunk:
                                f.write(chunk)
                print(f"[Apify] Successfully downloaded video to {output_path}")
                return output_path

    except Exception as e:
        print(f"[Apify] Error running streamers/youtube-video-downloader: {e}")
        return None

    return None

def download_video_clip_fast(
    url: str, 
    start_sec: float, 
    end_sec: float, 
    output_path: str,
    apify_token: Optional[str] = None
) -> str:
    """
    Download video clip section.
    If apify_token is provided, uses Apify streamers/youtube-video-downloader actor,
    then cuts the clip with FFmpeg.
    Otherwise uses local yt-dlp section download.
    """
    url = clean_youtube_url(url)
    duration = end_sec - start_sec

    # 1. Try Apify if token is provided
    if apify_token and apify_token.strip():
        temp_full_video = output_path.replace(".mp4", "_full.mp4")
        apify_file = download_with_apify(url, apify_token.strip(), temp_full_video)
        if apify_file and os.path.exists(apify_file):
            import subprocess
            # Cut the specific section using fast FFmpeg seek
            cut_cmd = [
                "ffmpeg", "-y",
                "-ss", str(start_sec),
                "-to", str(end_sec),
                "-i", apify_file,
                "-c", "copy",
                output_path
            ]
            subprocess.run(cut_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # Remove full video
            try:
                os.remove(apify_file)
            except Exception:
                pass
            if os.path.exists(output_path) and os.path.getsize(output_path) > 1000:
                return output_path

    # 2. Fallback to yt-dlp section download
    section_arg = f"*{start_sec:.2f}-{end_sec:.2f}"
    
    ydl_opts = {
        'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best',
        'outtmpl': output_path,
        'download_ranges': yt_dlp.utils.download_range_func(None, [(start_sec, end_sec)]),
        'force_keyframes_at_cuts': True,
        'quiet': False,
        'no_warnings': True,
        'overwrites': True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return output_path
