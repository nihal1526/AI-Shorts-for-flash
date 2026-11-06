import re
import math
from typing import List, Dict, Any

# High-impact curiosity words and emotional triggers for YouTube Shorts hooks
HOOK_KEYWORDS = {
    "secret": 3.0, "mistake": 3.5, "never": 2.5, "always": 2.0, "truth": 3.0,
    "nobody": 3.0, "stop": 2.5, "shocking": 3.0, "crazy": 2.5, "insane": 2.5,
    "money": 2.5, "million": 2.5, "hack": 3.0, "trick": 2.5, "why": 2.0,
    "how to": 2.5, "rule": 2.5, "danger": 3.0, "worst": 3.0, "best": 2.0,
    "proven": 2.5, "destroy": 3.0, "change": 2.0, "life": 2.0, "hidden": 3.0,
    "warning": 3.5, "exposed": 3.5, "formula": 2.5, "reason": 2.0, "lies": 3.5
}

QUESTION_WORDS = ["why", "how", "what", "who", "when", "where", "did", "can", "should", "would", "is", "are"]

def score_hook_sentence(text: str) -> float:
    """Calculate hook score for an opening sentence."""
    text_lower = text.lower()
    score = 40.0 # base score
    
    # Check for question hook
    if "?" in text or any(text_lower.startswith(q) for q in QUESTION_WORDS):
        score += 20.0
        
    # Check for curiosity & emotional trigger words
    for kw, weight in HOOK_KEYWORDS.items():
        if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
            score += weight * 4.0
            
    # First-person / Direct address bonus ("you", "I had to", "listen to this")
    if re.search(r'\b(you|your|you\'re|i discovered|here is|look at)\b', text_lower):
        score += 15.0
        
    # Punchiness bonus (short, punchy opening sentences between 4 and 14 words perform best)
    words = text.split()
    if 4 <= len(words) <= 14:
        score += 10.0
    elif len(words) > 25:
        score -= 10.0
        
    return min(99.0, max(45.0, score))

def calculate_clip_virality(clip_text: str, duration: float, opening_hook_score: float) -> Dict[str, Any]:
    """Calculate multifaceted virality metrics for a candidate short clip."""
    words = clip_text.split()
    total_words = len(words)
    
    # 1. Pacing & Cadence score (ideal shorts word rate is 2.5 to 3.8 words per second)
    wps = total_words / max(1.0, duration)
    if 2.4 <= wps <= 4.0:
        pacing_score = 92.0
    elif 1.8 <= wps < 2.4:
        pacing_score = 82.0
    else:
        pacing_score = 70.0
        
    # 2. Topic Cohesion & Energy
    text_lower = clip_text.lower()
    matched_triggers = [kw for kw in HOOK_KEYWORDS if re.search(r'\b' + re.escape(kw) + r'\b', text_lower)]
    energy_score = min(98.0, 60.0 + len(matched_triggers) * 6.0)
    
    # 3. Overall virality formula
    virality_score = round(
        (opening_hook_score * 0.45) +
        (pacing_score * 0.25) +
        (energy_score * 0.30)
    )
    virality_score = min(98, max(68, virality_score))
    
    # Determine virality badge and hook reasoning
    if virality_score >= 90:
        tier = "Ultra Viral"
        reason = "Explosive opening hook with high emotional engagement and rapid pacing. Ideal for 100%+ retention."
    elif virality_score >= 80:
        tier = "High Potential"
        reason = "Strong narrative flow with clear curiosity payoff. Very high likelihood of audience shares."
    else:
        tier = "Solid Performer"
        reason = "Engaging topic segment that delivers a concise, practical takeaway."

    return {
        "virality_score": virality_score,
        "hook_score": round(opening_hook_score),
        "pacing_score": round(pacing_score),
        "energy_score": round(energy_score),
        "words_per_second": round(wps, 1),
        "tier": tier,
        "reason": reason,
        "trigger_words": list(set(matched_triggers))[:5]
    }

def find_viral_clips(
    segments: List[Dict[str, Any]], 
    min_duration: float = 25.0, 
    max_duration: float = 58.0, 
    target_count: int = 4
) -> List[Dict[str, Any]]:
    """Scan transcript segments and extract the most viral standalone clip candidates."""
    if not segments:
        return []

    candidates = []
    num_segs = len(segments)

    # Walk through segments to find potential clip starting points with strong hooks
    for i in range(num_segs):
        start_seg = segments[i]
        start_time = start_seg["start"]
        hook_text = start_seg["text"]
        hook_score = score_hook_sentence(hook_text)

        curr_duration = 0.0
        clip_segments = []
        clip_words = []
        full_clip_text = []

        for j in range(i, num_segs):
            seg = segments[j]
            clip_segments.append(seg)
            full_clip_text.append(seg["text"])
            if "words" in seg:
                clip_words.extend(seg["words"])

            end_time = seg["end"]
            curr_duration = end_time - start_time

            # If clip is in the golden Shorts zone (25 - 58s)
            if min_duration <= curr_duration <= max_duration:
                # End on a sentence boundary or strong punctuation if possible
                text_so_far = " ".join(full_clip_text)
                is_sentence_end = seg["text"].rstrip().endswith((".", "!", "?", '”', '"'))
                
                # Bonus if it finishes cleanly
                current_hook_score = hook_score + (5.0 if is_sentence_end else 0.0)
                metrics = calculate_clip_virality(text_so_far, curr_duration, current_hook_score)

                candidates.append({
                    "start_time": round(start_time, 2),
                    "end_time": round(end_time, 2),
                    "duration": round(curr_duration, 1),
                    "hook_text": hook_text,
                    "full_text": text_so_far,
                    "words": clip_words,
                    "segments": clip_segments,
                    "metrics": metrics
                })
                
                # If we've found a great sentence ending, break to look for next starting hook
                if is_sentence_end and curr_duration >= 35.0:
                    break

            if curr_duration > max_duration:
                break

    if not candidates:
        # Fallback: create chunked clips from whatever segments exist
        total_time = segments[-1]["end"] - segments[0]["start"]
        step = max(30.0, total_time / max(1, target_count))
        cur = segments[0]["start"]
        fallback_clips = []
        
        while cur < segments[-1]["end"] and len(fallback_clips) < target_count:
            end = min(segments[-1]["end"], cur + min(45.0, step))
            sub_segs = [s for s in segments if s["start"] >= cur and s["end"] <= end]
            text = " ".join(s["text"] for s in sub_segs)
            words = []
            for s in sub_segs:
                words.extend(s.get("words", []))
            
            metrics = calculate_clip_virality(text or "Highlights clip", end - cur, 75.0)
            fallback_clips.append({
                "start_time": round(cur, 2),
                "end_time": round(end, 2),
                "duration": round(end - cur, 1),
                "hook_text": text[:80] + "..." if text else "Engaging highlight clip",
                "full_text": text or "Highlights clip",
                "words": words,
                "segments": sub_segs,
                "metrics": metrics
            })
            cur = end + 5.0
        return fallback_clips

    # Sort candidates by virality score descending
    candidates.sort(key=lambda c: c["metrics"]["virality_score"], reverse=True)

    # Filter out heavily overlapping clips (ensure diverse highlights across the video)
    selected_clips = []
    for cand in candidates:
        overlaps = False
        for sel in selected_clips:
            # Overlap threshold: if they share more than 15 seconds
            overlap_start = max(cand["start_time"], sel["start_time"])
            overlap_end = min(cand["end_time"], sel["end_time"])
            if (overlap_end - overlap_start) > 15.0:
                overlaps = True
                break
        if not overlaps:
            cand["clip_id"] = f"clip_{len(selected_clips) + 1}"
            selected_clips.append(cand)
            if len(selected_clips) >= target_count:
                break

    return selected_clips

