# YouTube → MP3 (local)

Small Python tool to download audio as MP3 using [yt-dlp](https://github.com/yt-dlp/yt-dlp) and FFmpeg. Includes a simple web page (localhost only) and shell wrappers so you don’t have to activate the virtualenv each time.

## Prerequisites

- **Python 3.9+**
- **FFmpeg** on your `PATH` (macOS: `brew install ffmpeg`)
- **Git** (to clone this repo)

## Setup

```bash
git clone <your-repo-url>
cd youtube-download   # or whatever you named the folder

python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

## CLI

```bash
./yt-mp3 "https://www.youtube.com/watch?v=VIDEO_ID"
./yt-mp3 -o ~/Music -q 320 "URL"
```

## Web UI (optional)

Starts a page on **this computer only** (`127.0.0.1`):

```bash
./yt-mp3-web
```

Open [http://127.0.0.1:5050](http://127.0.0.1:5050), paste a link, download. MP3s go to `./youtube_mp3`.

## Sharing on GitHub

1. Create a **new empty repository** on GitHub (no README if you’ll push existing files).
2. In this folder, add the remote and push:

   ```bash
   cd /path/to/this-repo
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   git branch -M main
   git push -u origin main
   ```

3. Send your friend the repo URL. They clone and follow **Setup** above.

Do **not** commit `.venv/`, downloads, or `__pycache__/` — they are listed in `.gitignore`.

## Legal note

Only download content you’re allowed to use. Respect copyright and each site’s terms of service.
