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

def get_transcript(url: str) -> List[Dict[str, Any]]:
    """Retrieve full transcript from YouTube using available automatic or uploaded subtitles."""
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
        
        # Priority order for language keys: en, en-US, en-GB, then any available
        all_subs = {**auto_subs, **subs}
        lang_keys = list(all_subs.keys())
        
        if not lang_keys:
            return []

        chosen_key = None
        for pref in ['en', 'en-US', 'en-GB', 'en-auto']:
            if pref in lang_keys:
                chosen_key = pref
                break
        if not chosen_key:
            chosen_key = lang_keys[0]

        formats = all_subs.get(chosen_key, [])
        
        # Prefer json3 for high precision word timing, else vtt
        json3_url = next((f['url'] for f in formats if f.get('ext') == 'json3'), None)
        vtt_url = next((f['url'] for f in formats if f.get('ext') == 'vtt'), None)
        
        req_headers = {'User-Agent': 'Mozilla/5.0'}
        
        if json3_url:
            req = urllib.request.Request(json3_url, headers=req_headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                return parse_json3_subtitles(data)
        
        if vtt_url:
            req = urllib.request.Request(vtt_url, headers=req_headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read().decode('utf-8')
                return parse_vtt_subtitles(data)

    return []

def download_video_clip_fast(url: str, start_sec: float, end_sec: float, output_path: str) -> str:
    """Download only the exact clip section using yt-dlp section download."""
    url = clean_youtube_url(url)
    duration = end_sec - start_sec

    # Format time section for yt-dlp e.g. "*12.5-45.0"
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
