import os
from typing import List, Dict, Any
from backend.config import SUBTITLE_PRESETS

def format_ass_time(seconds: float) -> str:
    """Format seconds into ASS timestamp format: H:MM:SS.cs (centiseconds)."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"

def generate_ass_subtitles(
    segments: List[Dict[str, Any]], 
    clip_start: float, 
    clip_end: float, 
    style_name: str = "hormozi",
    uppercase: bool = True
) -> str:
    """
    Generate Advanced SubStation Alpha (.ass) subtitle content with word-level
    dynamic karaoke / highlight animations for 9:16 vertical shorts.
    """
    preset = SUBTITLE_PRESETS.get(style_name, SUBTITLE_PRESETS["hormozi"])
    font = preset["fontname"]
    fontsize = preset["fontsize"]
    primary_color = preset["primary_color"]
    highlight_color = preset["highlight_color"]
    outline_color = preset["outline_color"]
    outline = preset["outline"]
    shadow = preset["shadow"]
    bold = preset["bold"]
    alignment = preset["alignment"] # 2 = bottom center
    margin_v = preset["margin_v"]   # 130px above bottom to avoid YouTube Shorts UI overlay

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font},{fontsize},{primary_color},&H000000FF,{outline_color},&H80000000,{bold},0,0,0,100,100,0,0,1,{outline},{shadow},{alignment},40,40,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    dialogue_lines = []

    # Gather all word tokens relative to clip start
    all_words = []
    for seg in segments:
        words = seg.get("words", [])
        if words:
            for w in words:
                w_start = w["start"] - clip_start
                w_end = w["end"] - clip_start
                if w_end > 0 and w_start < (clip_end - clip_start):
                    w_text = w["word"].strip()
                    if uppercase:
                        w_text = w_text.upper()
                    all_words.append({
                        "word": w_text,
                        "start": max(0.0, w_start),
                        "end": min(clip_end - clip_start, w_end)
                    })
        else:
            # Segment without word timestamps: synthesize words
            seg_start = max(0.0, seg["start"] - clip_start)
            seg_end = min(clip_end - clip_start, seg["end"] - clip_start)
            seg_dur = max(0.4, seg_end - seg_start)
            tokens = seg.get("text", "").split()
            if tokens:
                step = seg_dur / len(tokens)
                for idx, t in enumerate(tokens):
                    t_text = t.strip()
                    if uppercase:
                        t_text = t_text.upper()
                    all_words.append({
                        "word": t_text,
                        "start": seg_start + idx * step,
                        "end": seg_start + (idx + 1) * step
                    })

    if not all_words:
        return header

    # Chunk words into small punchy phrases (3 to 5 words max for vertical shorts readability)
    chunk_size = 4
    for i in range(0, len(all_words), chunk_size):
        phrase = all_words[i:i + chunk_size]
        if not phrase:
            continue

        phrase_start = phrase[0]["start"]
        phrase_end = phrase[-1]["end"]

        # For each word in the phrase, render a dialogue state where that word is highlighted
        for active_idx, target_word in enumerate(phrase):
            w_start = target_word["start"]
            w_end = target_word["end"]
            if w_end <= w_start:
                w_end = w_start + 0.3

            # Format words with the active word in the highlight color
            formatted_words = []
            for j, w in enumerate(phrase):
                if j == active_idx:
                    # Highlight color (strip &H and prefix with \c)
                    color_tag = highlight_color.replace("&H00", "&H").replace("&H", r"{\c&H") + r"&}"
                    formatted_words.append(f"{color_tag}{w['word']}{{\\c{primary_color.replace('&H00', '&H')}&}}")
                else:
                    formatted_words.append(w["word"])

            text_content = " ".join(formatted_words)
            start_str = format_ass_time(w_start)
            end_str = format_ass_time(w_end)
            dialogue_lines.append(f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{text_content}")

    return header + "\n".join(dialogue_lines) + "\n"
