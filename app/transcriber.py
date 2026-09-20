"""
Transcribes a video/audio file to a timestamped transcript using faster-whisper.
Runs locally on CPU (no external API needed for this step).
"""
from faster_whisper import WhisperModel
from app.config import settings

_model = None


def get_model() -> WhisperModel:
    global _model
    if _model is None:
        _model = WhisperModel(
            settings.whisper_model_size,
            device="cpu",
            compute_type="int8",
        )
    return _model


def transcribe(filepath: str) -> list[dict]:
    """Returns a list of {start, end, text} segments in chronological order."""
    model = get_model()
    segments, _info = model.transcribe(filepath, vad_filter=True)

    result = []
    for seg in segments:
        result.append({
            "start": round(seg.start, 2),
            "end": round(seg.end, 2),
            "text": seg.text.strip(),
        })
    return result
