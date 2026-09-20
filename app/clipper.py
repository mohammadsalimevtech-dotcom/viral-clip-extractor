"""
Cuts a clip out of the source video with ffmpeg, optionally burning in
subtitles generated from the transcript segments.
"""
import subprocess


def cut_clip(input_path: str, start: float, end: float, output_path: str,
             burn_subtitles: str | None = None) -> str:
    duration = max(end - start, 0.1)

    cmd = ["ffmpeg", "-y", "-ss", str(start), "-i", input_path, "-t", str(duration)]

    if burn_subtitles:
        # Escape path for the ffmpeg subtitles filter
        escaped = burn_subtitles.replace(":", "\\:")
        cmd += ["-vf", f"subtitles={escaped}"]

    cmd += ["-c:v", "libx264", "-c:a", "aac", "-preset", "fast", output_path]

    subprocess.run(cmd, check=True, capture_output=True)
    return output_path


def _fmt_srt_time(t: float) -> str:
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    ms = int(round((s - int(s)) * 1000))
    return f"{h:02d}:{m:02d}:{int(s):02d},{ms:03d}"


def segments_to_srt(segments: list[dict], start_offset: float, end_offset: float, srt_path: str) -> str:
    """Writes an SRT file containing only the transcript overlapping [start_offset, end_offset],
    with timestamps shifted so 0 = start_offset (i.e. relative to the cut clip)."""
    idx = 1
    with open(srt_path, "w", encoding="utf-8") as f:
        for seg in segments:
            if seg["end"] <= start_offset or seg["start"] >= end_offset:
                continue
            s = max(seg["start"], start_offset) - start_offset
            e = min(seg["end"], end_offset) - start_offset
            f.write(f"{idx}\n{_fmt_srt_time(s)} --> {_fmt_srt_time(e)}\n{seg['text'].strip()}\n\n")
            idx += 1
    return srt_path
