import os
from typing import List, Dict, Any, Optional
from backend.config import ASSEMBLYAI_API_KEY

def format_srt_time(seconds: float) -> str:
    """Format seconds into standard SRT timestamp format: HH:MM:SS,mmm"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    ms = int(round((seconds - int(seconds)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def generate_srt_from_segments(segments: List[Dict[str, Any]], clip_start: float = 0.0) -> str:
    """Generate standard .SRT subtitle content from timed segments relative to clip start."""
    srt_lines = []
    idx = 1
    for seg in segments:
        s_start = max(0.0, seg["start"] - clip_start)
        s_end = max(s_start + 0.3, seg["end"] - clip_start)
        text = seg["text"].strip()
        if text:
            srt_lines.append(f"{idx}")
            srt_lines.append(f"{format_srt_time(s_start)} --> {format_srt_time(s_end)}")
            srt_lines.append(f"{text}\n")
            idx += 1
    return "\n".join(srt_lines)

def transcribe_with_assemblyai(
    audio_path_or_url: str, 
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Transcribe audio/video using AssemblyAI with high-accuracy word-level timestamps,
    speaker labels, auto-highlights, and ready-to-upload SRT subtitles.
    """
    key = (api_key or ASSEMBLYAI_API_KEY or "").strip()
    if not key:
        raise ValueError("AssemblyAI API key not provided.")

    try:
        import assemblyai as aai
        aai.settings.api_key = key

        config = aai.TranscriptionConfig(
            auto_highlights=True,
            speaker_labels=True,
            punctuate=True,
            format_text=True
        )

        transcriber = aai.Transcriber()
        print(f"[AssemblyAI] Transcribing with AssemblyAI: {audio_path_or_url[:60]}...")
        transcript = transcriber.transcribe(audio_path_or_url, config=config)

        if transcript.status == aai.TranscriptStatus.error:
            raise RuntimeError(f"AssemblyAI error: {transcript.error}")

        # Extract words with word-level timestamps
        all_words = []
        for w in (transcript.words or []):
            all_words.append({
                "word": w.text,
                "start": round(w.start / 1000.0, 2),
                "end": round(w.end / 1000.0, 2),
                "confidence": round(w.confidence, 2) if hasattr(w, 'confidence') else 1.0,
                "speaker": getattr(w, 'speaker', 'A')
            })

        # Group words into structured sentences / timed segments for virality scanning
        segments = []
        curr_words = []
        curr_text = []

        for w in all_words:
            curr_words.append(w)
            curr_text.append(w["word"])
            
            # Sentence boundary check
            ends_sentence = w["word"].rstrip().endswith((".", "!", "?", '"'))
            reached_chunk_limit = len(curr_words) >= 10

            if (ends_sentence or reached_chunk_limit) and curr_words:
                seg_text = " ".join(curr_text).strip()
                seg_start = curr_words[0]["start"]
                seg_end = curr_words[-1]["end"]
                segments.append({
                    "start": seg_start,
                    "end": seg_end,
                    "text": seg_text,
                    "words": list(curr_words)
                })
                curr_words = []
                curr_text = []

        if curr_words:
            segments.append({
                "start": curr_words[0]["start"],
                "end": curr_words[-1]["end"],
                "text": " ".join(curr_text).strip(),
                "words": list(curr_words)
            })

        # Export native SRT & VTT subtitles
        srt_subtitles = ""
        vtt_subtitles = ""
        try:
            srt_subtitles = transcript.export_subtitles_srt(chars_per_caption=32)
            vtt_subtitles = transcript.export_subtitles_vtt(chars_per_caption=32)
        except Exception:
            srt_subtitles = generate_srt_from_segments(segments)

        return {
            "text": transcript.text,
            "segments": segments,
            "words": all_words,
            "srt": srt_subtitles,
            "vtt": vtt_subtitles
        }

    except Exception as e:
        print(f"[AssemblyAI] Transcription failed: {e}")
        raise e
