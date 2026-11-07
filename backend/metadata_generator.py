import os
import re
import json
import random
from typing import Dict, Any, List, Optional
from backend.config import GEMINI_API_KEY

TRENDING_HASHTAGS = [
    "#shorts", "#youtubeshorts", "#viral", "#trending", 
    "#fyp", "#foryou", "#podcast", "#clips", "#reels",
    "#mindset", "#success", "#lifehacks", "#viralvideo"
]

def clean_text_for_title(text: str) -> str:
    """Strip unnecessary filler words and clean for title display."""
    text = re.sub(r'^(and|so|but|because|you know|i mean|like|well)\s+', '', text, flags=re.IGNORECASE)
    text = text.strip().capitalize()
    return text

def generate_with_gemini(
    clip_text: str,
    original_title: str,
    channel: str,
    gemini_key: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Generate high-CTR YouTube Shorts metadata using Google Gemini AI."""
    key = (gemini_key or GEMINI_API_KEY or "").strip()
    if not key:
        return None

    try:
        from google import genai
        client = genai.Client(api_key=key)

        prompt = f"""You are an elite YouTube Shorts growth strategist. 
Analyze this short clip from the video "{original_title}" by "{channel}".
Clip transcript: "{clip_text}"

Generate:
1. "titles": Array of 3 viral, curiosity-gap YouTube Shorts titles (each under 60 chars, with punchy emoji, ending in #shorts)
2. "description": Engaging YouTube Shorts description with hook, summary, subscribe call-to-action, and trending hashtags (#shorts, #youtubeshorts, #viral, #fyp)
3. "tags": Comma-separated list of 15+ high-ranking YouTube Studio SEO tags

Return ONLY valid JSON with keys "titles", "description", "tags".
"""
        for model_name in ['gemini-3.5-flash-lite', 'gemini-3.1-pro-preview', 'gemini-3.8-flash', 'gemini-flash-latest']:
            try:
                res = client.models.generate_content(model=model_name, contents=prompt)
                raw_text = res.text.strip()
                if "```json" in raw_text:
                    raw_text = raw_text.split("```json")[1].split("```")[0].strip()
                elif "```" in raw_text:
                    raw_text = raw_text.split("```")[1].split("```")[0].strip()
                
                data = json.loads(raw_text)
                if data.get("titles") and data.get("description"):
                    print(f"[Gemini] Successfully generated metadata with {model_name}")
                    return data
            except Exception as model_err:
                continue

    except Exception as e:
        print(f"[Gemini] Metadata generation failed: {e}")

    return None

def generate_shorts_metadata(
    clip: Dict[str, Any], 
    video_info: Dict[str, Any],
    gemini_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate all assets needed when uploading a clip to YouTube Shorts:
    - 3 High-CTR Title Options (via Gemini AI or NLP)
    - Formatted YouTube Shorts Description with hashtags
    - YouTube Studio Tags (comma separated)
    - Recommended Keyframe / Thumbnail timestamp
    - .SRT Subtitles for YouTube Studio
    """
    hook_text = clip.get("hook_text", "")
    full_text = clip.get("full_text", "")
    channel = video_info.get("channel", "Original Creator")
    original_title = video_info.get("title", "Video")
    start_time = clip.get("start_time", 0.0)

    # 1. Try Google Gemini AI First
    gemini_data = generate_with_gemini(
        clip_text=full_text or hook_text,
        original_title=original_title,
        channel=channel,
        gemini_key=gemini_key
    )

    if gemini_data:
        title_options = gemini_data.get("titles", [])
        description = gemini_data.get("description", "")
        tags_string = gemini_data.get("tags", "")
        tags = [t.strip() for t in tags_string.split(",") if t.strip()]
    else:
        # Algorithmic NLP Fallback
        first_sentence = hook_text.split('.')[0].split('?')[0].split('!')[0]
        cleaned_hook = clean_text_for_title(first_sentence)
        
        title_options = []
        if 10 < len(cleaned_hook) < 55:
            title_options.append(f"{cleaned_hook} 🤯 #shorts")
        else:
            title_options.append(f"The Truth About {original_title[:30]}... 😱 #shorts")
            
        title_options.append(f"Nobody Wants You To Know This... 🚨 #shorts")
        title_options.append(f"Did You Realize This? (Must Watch) 🧠 #shorts")

        triggers = clip.get("metrics", {}).get("trigger_words", [])
        if triggers:
            tw = triggers[0].capitalize()
            title_options[1] = f"The {tw} That Changes Everything! ⚡ #shorts"

        hook_summary = first_sentence.strip()
        if not hook_summary.endswith('.'):
            hook_summary += "..."
            
        description = f"""🔥 {hook_summary}

Watch till the end for the shocking realization! 
👉 Subscribe for more daily viral clips and high-value insights! 🔔

---
🎬 Original Video: {original_title}
🎙️ Speaker / Channel: {channel}
⏱️ Timestamp: {int(start_time // 60)}:{int(start_time % 60):02d}

#shorts #youtubeshorts #viral #trending #podcast #foryou #clips #shortsfeed #viralshorts #fyp
"""
        words = re.findall(r'[a-zA-Z]{4,}', f"{original_title} {hook_text}")
        unique_words = []
        for w in words:
            w_low = w.lower()
            if w_low not in unique_words and w_low not in ['this', 'that', 'with', 'from', 'have', 'were', 'what', 'your', 'about']:
                unique_words.append(w_low)
                
        tags = [
            "shorts",
            "youtube shorts",
            "viral shorts",
            "trending shorts",
            "podcast clips",
            channel.lower(),
            "motivation",
            "life advice",
            "self improvement",
            "viral clips",
            "yt shorts"
        ]
        tags.extend(unique_words[:8])
        tags_string = ", ".join(tags)

    # Keyframe Thumbnail & SRT Subtitles
    thumbnail_sec = round(start_time + 1.8, 1)

    from backend.assemblyai_transcriber import generate_srt_from_segments
    srt_content = generate_srt_from_segments(clip.get("segments", []), clip_start=start_time)

    return {
        "titles": title_options,
        "primary_title": title_options[0] if title_options else f"{original_title[:40]} #shorts",
        "description": description.strip(),
        "tags": tags,
        "tags_string": tags_string,
        "recommended_thumbnail_time": thumbnail_sec,
        "srt_subtitles": srt_content,
        "ai_powered": bool(gemini_data),
        "hashtags": ["#shorts", "#youtubeshorts", "#viral", "#trending", "#fyp", "#podcast", "#clips"]
    }
