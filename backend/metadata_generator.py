import re
import random
from typing import Dict, Any, List

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

def generate_shorts_metadata(
    clip: Dict[str, Any], 
    video_info: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate all assets needed when uploading a clip to YouTube Shorts:
    - 3 High-CTR Title Options
    - Formatted YouTube Shorts Description with hashtags
    - YouTube Studio Tags (comma separated)
    - Recommended Keyframe / Thumbnail timestamp
    - Hook Breakdown & Retention Tips
    """
    hook_text = clip.get("hook_text", "")
    full_text = clip.get("full_text", "")
    channel = video_info.get("channel", "Original Creator")
    original_title = video_info.get("title", "Video")
    clip_id = clip.get("clip_id", "clip_1")
    start_time = clip.get("start_time", 0.0)

    # Clean the hook text
    first_sentence = hook_text.split('.')[0].split('?')[0].split('!')[0]
    cleaned_hook = clean_text_for_title(first_sentence)
    
    # 1. Generate 3 viral title variants
    title_options = []
    
    # Variant 1: Direct curiosity / Revelation
    if len(cleaned_hook) > 10 and len(cleaned_hook) < 55:
        title_options.append(f"{cleaned_hook} 🤯 #shorts")
    else:
        title_options.append(f"The Truth About {original_title[:30]}... 😱 #shorts")
        
    # Variant 2: High Urgency / Warning / Secret
    title_options.append(f"Nobody Wants You To Know This... 🚨 #shorts")
    
    # Variant 3: Mindset / Question
    title_options.append(f"Did You Realize This? (Must Watch) 🧠 #shorts")

    # If trigger words exist, craft tailored title
    triggers = clip.get("metrics", {}).get("trigger_words", [])
    if triggers:
        tw = triggers[0].capitalize()
        title_options[1] = f"The {tw} That Changes Everything! ⚡ #shorts"

    # 2. Generate YouTube Shorts Description
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

    # 3. Generate YouTube Studio Tags
    # Base tags + extracted keywords from original title and hook
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

    # 4. Best Keyframe Thumbnail Recommendation
    # Usually 1.5s - 2.5s into the clip where the speaker is animated
    thumbnail_sec = round(start_time + 1.8, 1)

    return {
        "titles": title_options,
        "primary_title": title_options[0],
        "description": description.strip(),
        "tags": tags,
        "tags_string": tags_string,
        "recommended_thumbnail_time": thumbnail_sec,
        "hook_summary": hook_summary,
        "hashtags": ["#shorts", "#youtubeshorts", "#viral", "#trending", "#fyp", "#podcast", "#clips"]
    }
