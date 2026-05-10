#!/usr/bin/env python3
"""
Tiny local web UI: paste URL, download MP3 into ./youtube_mp3.

Run (from this folder):

  ./yt-mp3-web
  # or:  source .venv/bin/activate && python app.py

Then open http://127.0.0.1:5050 — only listens on this Mac (localhost).
"""

from __future__ import annotations

import io
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from urllib.parse import urlparse

from flask import Flask, render_template_string, request

from download_mp3 import download_to_mp3

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_OUT = PROJECT_ROOT / "youtube_mp3"

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>YouTube → MP3</title>
  <style>
    :root {
      font-family: system-ui, sans-serif;
      background: #0f1419;
      color: #e7e9ea;
    }
    body { margin: 0; min-height: 100vh; display: grid; place-items: center; }
    main {
      width: min(440px, 92vw);
      padding: 1.75rem;
      border-radius: 12px;
      background: #1a2332;
      box-shadow: 0 12px 40px rgba(0,0,0,.35);
    }
    h1 { font-size: 1.15rem; margin: 0 0 1rem; font-weight: 600; }
    label { display: block; font-size: .85rem; margin-bottom: .4rem; color: #8899a6; }
    input[type="url"] {
      width: 100%; box-sizing: border-box;
      padding: .65rem .75rem; border-radius: 8px;
      border: 1px solid #38444d;
      background: #0f1419; color: #e7e9ea; font-size: 1rem;
    }
    input:focus { outline: 2px solid #1d9bf0; border-color: #1d9bf0; }
    button {
      margin-top: 1rem; width: 100%;
      padding: .7rem 1rem; border: none; border-radius: 8px;
      background: #1d9bf0; color: #fff; font-size: 1rem; font-weight: 600;
      cursor: pointer;
    }
    button:hover { background: #1a8cd8; }
    button:disabled { opacity: .55; cursor: not-allowed; }
    .msg {
      margin-top: 1rem; padding: .65rem .75rem; border-radius: 8px;
      font-size: .9rem; line-height: 1.4;
    }
    .ok { background: rgba(0,186,124,.15); color: #00ba7c; }
    .err { background: rgba(249,62,62,.15); color: #f96262; }
    .hint { margin-top: 1rem; font-size: .8rem; color: #697885; line-height: 1.45; }
  </style>
</head>
<body>
  <main>
    <h1>Paste link, download MP3</h1>
    <form method="post" action="{{ url_for('home') }}">
      <label for="url">YouTube URL</label>
      <input id="url" name="url" type="url" required
             placeholder="https://www.youtube.com/watch?v=..."
             autocomplete="off" value="{{ url or '' }}">
      <button type="submit">Download</button>
    </form>
    {% if message %}<div class="msg {{ mtype }}">{{ message }}</div>{% endif %}
    <p class="hint">
      Files go to:<br><code>{{ out_dir }}</code><br><br>
      Only runs on your computer (not exposed to the internet).
    </p>
  </main>
</body>
</html>
"""


def ok_url(raw: str) -> bool:
    raw = raw.strip()
    if not raw or len(raw) > 2000:
        return False
    p = urlparse(raw)
    return p.scheme in ("http", "https") and bool(p.netloc)


app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def home():
    url = ""
    message = ""
    mtype = "ok"

    if request.method == "POST":
        url = request.form.get("url", "").strip()
        if not ok_url(url):
            message = "That does not look like a valid http(s) link."
            mtype = "err"
        else:
            buf_out, buf_err = io.StringIO(), io.StringIO()
            with redirect_stdout(buf_out), redirect_stderr(buf_err):
                code = download_to_mp3(
                    [url],
                    out_dir=DEFAULT_OUT,
                    quality="192",
                    no_playlist=False,
                )
            log = (buf_out.getvalue() + buf_err.getvalue()).strip()
            if code == 0:
                message = "Done — check the folder below for your MP3."
                mtype = "ok"
            else:
                message = (
                    log or "Download failed."
                )[:900]
                mtype = "err"

    return render_template_string(
        PAGE,
        url=url if request.method == "POST" else "",
        message=message,
        mtype=mtype,
        out_dir=str(DEFAULT_OUT),
    )


if __name__ == "__main__":
    DEFAULT_OUT.mkdir(parents=True, exist_ok=True)
    app.run(host="127.0.0.1", port=5050, debug=False)
