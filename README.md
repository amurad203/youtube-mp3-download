# YouTube → MP3 (local)

Download YouTube (and other sites [yt-dlp](https://github.com/yt-dlp/yt-dlp) supports) as **MP3** using **FFmpeg**. Single entry script **`./yt-mp3`**: no arguments starts a small **web UI** on your machine; with a URL it runs the CLI. No need to activate the virtualenv for day-to-day use.

## Prerequisites

| Tool | Why |
|------|-----|
| **Python 3.9+** | Runs the app |
| **FFmpeg** on your `PATH` | Encodes audio to MP3 *(not installable via pip — see `requirements.txt` comments)* |
| **Node.js** (recommended) | Faster, more reliable YouTube extraction for yt-dlp (`brew install node` on macOS) |
| **Git** | Clone this repo |

Install FFmpeg: **macOS** `brew install ffmpeg` · **Ubuntu/Debian** `sudo apt install ffmpeg` · **Windows** [ffmpeg.org](https://ffmpeg.org/download.html) (add `ffmpeg.exe` to `PATH`).

Verify it works anywhere:

```bash
ffmpeg -version
```

### Friend only sees `.webm` or `.m4a`, no `.mp3`?

That almost always means the **conversion step didn’t run** — usually FFmpeg is **missing** or **not on PATH** (common on Windows). YouTube’s stream is downloaded first (often WebM), then FFmpeg is supposed to produce the MP3.

1. Install FFmpeg and restart the terminal — run `ffmpeg -version` until it prints a version.
2. On Windows you can install the full “ Essentials build ” zip and add the `bin` folder to **PATH**.
3. If FFmpeg is installed in a weird place, set the env var **`FFMPEG_LOCATION`** to the **`ffmpeg`** binary (folder or `.exe`), then run `./yt-mp3` again:

   ```bash
   export FFMPEG_LOCATION="/full/path/to/ffmpeg"   # Windows (Git Bash): FFMPEG_LOCATION="/c/path/to/ffmpeg.exe"
   ```

4. CLI only: `./yt-mp3 --ffmpeg-location /path/to/ffmpeg "URL"`

## Setup

```bash
git clone https://github.com/amurad203/youtube-mp3-download.git
cd youtube-mp3-download

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Deactivate when finished with `deactivate` — optional if you only use `./yt-mp3`.

## Web UI (recommended)

From the project folder:

```bash
./yt-mp3
```

Same as `./yt-mp3 web` (or `gui`). Open [**http://127.0.0.1:5050**](http://127.0.0.1:5050) — only your computer, not the public internet.

- Paste a video or playlist URL.
- **Save folder:** full path where MP3s should go. Default is **`youtube_mp3` inside this repo** (shown as an absolute path on the form). Change it to e.g. `~/Music/my-rips` anytime.
- **“Download the entire playlist”** is **unchecked by default** → only the **one linked video** downloads. Check it when you want every track.
- A **progress bar** and status line update while the download runs.

**Windows:** run `python app.py` from the project dir, or use Git Bash for `./yt-mp3`.

## CLI

Run from the **project directory** (so the default output folder is predictable):

```bash
cd /path/to/youtube-mp3-download
./yt-mp3 "https://www.youtube.com/watch?v=VIDEO_ID"
./yt-mp3 -o ~/Music -q 320 "URL"
./yt-mp3 --no-playlist "PLAYLIST_URL"
```

With any arguments (other than `web` / `gui`), `./yt-mp3` forwards to `download_mp3.py`.

## Where files go

- **Web UI:** whatever path is in the form (default: `<this repo>/youtube_mp3/`).
- **CLI:** `./yt-mp3 …` uses `youtube_mp3` **relative to your current shell directory** unless you pass `-o`.

The `youtube_mp3/` folder is **gitignored** — it is not uploaded to GitHub; each clone gets its own local downloads.

## Updating yt-dlp

If downloads break or get slow after YouTube changes:

```bash
source .venv/bin/activate
pip install -U yt-dlp
```

The app allows yt-dlp to fetch **`ejs:github`** helper scripts when YouTube demands extra JS solving (recommended by yt-dlp; needs outbound access to GitHub).

## Legal

Only download content you are allowed to use. Respect copyright and each site’s terms of service.
