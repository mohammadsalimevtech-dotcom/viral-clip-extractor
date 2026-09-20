"""
Downloads a YouTube video to disk using yt-dlp and returns basic metadata.
"""
import os
import yt_dlp


def download_youtube_video(url: str, output_dir: str) -> dict:
    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
        "format": "bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": os.path.join(output_dir, "%(id)s.%(ext)s"),
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "extractor_args": {"youtube": {"player_client": ["android", "web"]}},
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filepath = ydl.prepare_filename(info)

        base, _ = os.path.splitext(filepath)
        mp4_path = base + ".mp4"
        if not os.path.exists(mp4_path):
            mp4_path = filepath

        return {
            "video_id": info.get("id"),
            "title": info.get("title"),
            "duration": info.get("duration"),
            "filepath": mp4_path,
        }
