"""
Sends the timestamped transcript to Claude and asks it to identify the
strongest short-form / viral moments, with start/end timestamps.
"""
import json
import anthropic
from app.config import settings

client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

SYSTEM_PROMPT = """You are an expert short-form video editor who finds viral-worthy moments in long YouTube videos for platforms like YouTube Shorts, Instagram Reels and TikTok.

You will receive a timestamped transcript of a video. Identify the {max_clips} strongest standalone moments that could each become a {min_dur}-{max_dur} second viral clip.

Good viral moments have: a strong hook in the first 2-3 seconds, an emotional peak, a surprising fact, a punchline, a controversial or bold claim, or a clear payoff/insight -- and they must make sense on their own without the rest of the video.

Respond ONLY with valid JSON, no markdown fences, no commentary, in this exact shape:
{{
  "clips": [
    {{
      "start": <number, seconds>,
      "end": <number, seconds>,
      "title": "<short punchy clip title, max 8 words>",
      "hook": "<the opening line/hook that grabs attention>",
      "reason": "<1 sentence on why this is viral-worthy>",
      "virality_score": <integer 1-100>
    }}
  ]
}}

Rules:
- end - start must be between {min_dur} and {max_dur} seconds.
- Only use timestamps that fall within the transcript's range.
- Order clips by virality_score, highest first.
- Clips must not overlap each other.
"""


def format_transcript(segments: list[dict]) -> str:
    lines = [f"[{s['start']:.1f}-{s['end']:.1f}] {s['text']}" for s in segments]
    return "\n".join(lines)


def find_viral_clips(segments: list[dict]) -> list[dict]:
    transcript_text = format_transcript(segments)

    system = SYSTEM_PROMPT.format(
        max_clips=settings.max_clips_per_video,
        min_dur=settings.clip_duration_min,
        max_dur=settings.clip_duration_max,
    )

    response = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=2000,
        system=system,
        messages=[{"role": "user", "content": f"Transcript:\n\n{transcript_text}"}],
    )

    text = "".join(block.text for block in response.content if block.type == "text").strip()
    text = text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    data = json.loads(text)
    return data.get("clips", [])
