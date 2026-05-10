#!/usr/bin/env python3
"""
Download audio from YouTube (or other sites yt-dlp supports) as MP3.

Requires:
  - Python 3.9+
  - FFmpeg installed and on PATH (brew install ffmpeg)

Usage:
  python download_mp3.py "https://www.youtube.com/watch?v=..."
  python download_mp3.py -o ~/Music/youtube url1 url2
  python download_mp3.py --quality 320 playlist_url
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    print("Missing dependency: pip install -r requirements.txt", file=sys.stderr)
    sys.exit(1)


def build_opts(
    out_dir: Path,
    quality: str,
    no_playlist: bool,
) -> dict:
    return {
        "format": "bestaudio/best",
        "outtmpl": str(out_dir / "%(title)s.%(ext)s"),
        "noplaylist": no_playlist,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": quality,
            }
        ],
        # Safer filenames on all platforms
        "restrictfilenames": False,
        "windowsfilenames": True,
    }


def download_to_mp3(
    urls: list[str],
    *,
    out_dir: Path | None = None,
    quality: str = "192",
    no_playlist: bool = False,
) -> int:
    """Download URLs to MP3. Returns 0 on success, 1 on yt-dlp error."""
    out = out_dir or Path("youtube_mp3")
    out.mkdir(parents=True, exist_ok=True)
    opts = build_opts(out.resolve(), quality, no_playlist)
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download(urls)
    except yt_dlp.utils.DownloadError as e:
        print(e, file=sys.stderr)
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download YouTube (etc.) audio as MP3 via yt-dlp + FFmpeg."
    )
    parser.add_argument(
        "urls",
        nargs="+",
        help="One or more video or playlist URLs",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("youtube_mp3"),
        help="Folder for MP3 files (default: ./youtube_mp3)",
    )
    parser.add_argument(
        "-q",
        "--quality",
        default="192",
        help="MP3 bitrate in kbps (default: 192). Examples: 128, 192, 320",
    )
    parser.add_argument(
        "--no-playlist",
        action="store_true",
        help="If URL is a playlist, download only the single video",
    )
    args = parser.parse_args()

    return download_to_mp3(
        list(args.urls),
        out_dir=args.output_dir,
        quality=args.quality,
        no_playlist=args.no_playlist,
    )


if __name__ == "__main__":
    raise SystemExit(main())
