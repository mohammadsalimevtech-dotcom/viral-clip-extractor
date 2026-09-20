import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    whisper_model_size: str = os.getenv("WHISPER_MODEL_SIZE", "base")
    output_dir: str = os.getenv("OUTPUT_DIR", "storage/clips")
    download_dir: str = os.getenv("DOWNLOAD_DIR", "storage/downloads")

    clip_duration_min: int = int(os.getenv("CLIP_DURATION_MIN", "30"))
    clip_duration_max: int = int(os.getenv("CLIP_DURATION_MAX", "40"))
    max_clips_per_video: int = int(os.getenv("MAX_CLIPS_PER_VIDEO", "5"))

    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


settings = Settings()
