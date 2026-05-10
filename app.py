#!/usr/bin/env python3
"""
Tiny local web UI: paste URL, pick folder path, optional playlist, progress bar.

Run (from this folder):

  ./yt-mp3

Then open http://127.0.0.1:5050 — only listens on this Mac (localhost).
"""

from __future__ import annotations

import contextlib
import io
import os
import secrets
import threading
from pathlib import Path
from urllib.parse import urlparse

from flask import Flask, jsonify, render_template_string, request

from download_mp3 import download_to_mp3

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_OUT = (PROJECT_ROOT / "youtube_mp3").resolve()


def ok_url(raw: str) -> bool:
    raw = raw.strip()
    if not raw or len(raw) > 2000:
        return False
    p = urlparse(raw)
    return p.scheme in ("http", "https") and bool(p.netloc)


def resolve_save_dir(raw: str | None) -> tuple[Path | None, str | None]:
    """
    Expand ~ and resolve path. Relative paths are resolved from the app's cwd
    (project folder when launched via ./yt-mp3).
    Returns (path, error_message).
    """
    if raw is None or not str(raw).strip():
        p = DEFAULT_OUT
    else:
        p = Path(os.path.expanduser(str(raw).strip()))
        try:
            p = p.expanduser().resolve(strict=False)
        except OSError as e:
            return None, str(e)
    try:
        p.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        return None, str(e)
    return p, None


app = Flask(__name__)

jobs_lock = threading.RLock()  # progress hook runs inside the worker thread — must nest
# job_id -> {status, pct, label, detail, resolved_dir}
_jobs: dict[str, dict] = {}


def _make_progress_hook(job_id: str):
    pulse = {"n": 0}

    def hook(d: dict) -> None:
        with jobs_lock:
            job = _jobs.get(job_id)
            if not job:
                return
            if job["status"] == "error":
                return

            job["status"] = "running"
            info = d.get("info_dict") or {}
            pidx = info.get("playlist_index")
            pcnt = info.get("playlist_count")

            st = d.get("status")

            def set_bar(pct: float, label: str, detail: str = "") -> None:
                job["pct"] = max(0.0, min(100.0, pct))
                job["label"] = label
                job["detail"] = detail[:500]

            if st == "finished":
                if pcnt and pidx:
                    frac = min(1.0, pidx / float(pcnt))
                    set_bar(88.0 * frac + 4.0, f"Fetched {pidx} of {pcnt}", "Encoding to MP3…")
                else:
                    set_bar(92.0, "Encoding to MP3…", "")
                return

            if st != "downloading":
                return

            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            dl = float(d.get("downloaded_bytes") or 0)
            file_frac = dl / total if total else None

            if file_frac is None:
                pulse["n"] = min(pulse["n"] + 1, 35)
                file_frac = 0.08 + pulse["n"] / 220.0

            playlist_pct = (
                (((pidx or 1) - 1) + file_frac) / float(pcnt) * 100.0 if pcnt and pcnt > 1 else file_frac * 100.0
            )

            if pcnt and pidx:
                lbl = f"Downloading track {pidx} of {pcnt}"
            else:
                lbl = "Downloading…"

            spd = d.get("speed")
            eta = d.get("eta")
            tail = ""
            if spd:
                mega = spd / (1024 * 1024)
                tail += f"{mega:.2f} MiB/s"
            if eta is not None and eta >= 0:
                tail += f" · ETA {int(eta)}s" if tail else f"ETA {int(eta)}s"
            set_bar(playlist_pct, lbl, tail)

    return hook


def _run_download(job_id: str, url: str, save_dir: Path, full_playlist: bool) -> None:
    hooks = [_make_progress_hook(job_id)]

    with jobs_lock:
        j0 = _jobs.get(job_id)
        if j0:
            j0["status"] = "running"
            j0["label"] = "Starting…"

    buf_out, buf_err = io.StringIO(), io.StringIO()

    with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
        code = download_to_mp3(
            [url],
            out_dir=save_dir,
            quality="192",
            no_playlist=not full_playlist,
            progress_hooks=hooks,
        )

    tail = (buf_out.getvalue() + buf_err.getvalue()).strip()

    with jobs_lock:
        j = _jobs.get(job_id)
        if not j:
            return
        if code == 0:
            j["status"] = "done"
            j["pct"] = 100.0
            j["label"] = "Finished"
            j["detail"] = ""
        else:
            j["status"] = "error"
            j["detail"] = (tail or "Download failed.")[:900]

    return


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
      width: min(480px, 92vw);
      padding: 1.75rem;
      border-radius: 12px;
      background: #1a2332;
      box-shadow: 0 12px 40px rgba(0,0,0,.35);
    }
    h1 { font-size: 1.15rem; margin: 0 0 1rem; font-weight: 600; }
    label { display: block; font-size: .85rem; margin-bottom: .4rem; color: #8899a6; }
    input[type="url"], input[type="text"] {
      width: 100%; box-sizing: border-box;
      padding: .65rem .75rem; border-radius: 8px;
      border: 1px solid #38444d;
      background: #0f1419; color: #e7e9ea; font-size: 1rem;
    }
    input:focus { outline: 2px solid #1d9bf0; border-color: #1d9bf0; }
    .row { margin-top: .85rem; }
    .chk {
      display: flex; align-items: flex-start; gap: .55rem;
      font-size: .9rem; color: #c8d2dc; cursor: pointer;
      user-select: none;
    }
    .chk input { margin-top: .2rem; }
    button {
      margin-top: 1rem; width: 100%;
      padding: .7rem 1rem; border: none; border-radius: 8px;
      background: #1d9bf0; color: #fff; font-size: 1rem; font-weight: 600;
      cursor: pointer;
    }
    button:hover { background: #1a8cd8; }
    button:disabled { opacity: .55; cursor: not-allowed; }
    #progressWrap {
      margin-top: 1rem;
      border-radius: 8px;
      background: #0f1419;
      border: 1px solid #38444d;
      height: 10px;
      overflow: hidden;
      display: none;
    }
    #progressWrap.active { display: block; }
    #progressBar {
      height: 100%;
      width: 0%;
      background: linear-gradient(90deg, #1d9bf0, #00ba7c);
      transition: width .25s ease;
    }
    #statusLine {
      margin-top: .55rem;
      font-size: .85rem;
      color: #8899a6;
      min-height: 2.8em;
      line-height: 1.4;
      white-space: pre-wrap;
      word-break: break-word;
    }
    #msgBox {
      margin-top: .75rem; padding: .65rem .75rem; border-radius: 8px;
      font-size: .9rem; line-height: 1.35; display: none;
    }
    #msgBox.show { display: block; }
    #msgBox.err { background: rgba(249,62,62,.15); color: #f96262; white-space: pre-wrap; }
    #msgBox.ok { background: rgba(0,186,124,.15); color: #00ba7c; white-space: pre-wrap; }
    .hint { margin-top: 1rem; font-size: .8rem; color: #697885; line-height: 1.45; }
    code { font-size: .78rem; word-break: break-all; color: #9bb0bf; }
  </style>
</head>
<body>
  <main>
    <h1>Paste link, choose folder</h1>
    <label for="url">YouTube URL</label>
    <input id="url" type="url" required
           placeholder="https://www.youtube.com/watch?v=..."
           autocomplete="off">

    <div class="row">
      <label for="outdir">Save MP3s to (folder path on this Mac)</label>
      <input id="outdir" type="text"
             value="{{ default_out }}"
             placeholder="/Users/you/Music/MyDownloads"
             spellcheck="false" autocomplete="off">
    </div>

    <div class="row">
      <label class="chk">
        <input type="checkbox" id="fullplaylist">
        <span>Download the <strong>entire playlist</strong> (off = only this video).</span>
      </label>
    </div>

    <button id="go" type="button">Download</button>

    <div id="progressWrap"><div id="progressBar"></div></div>
    <div id="statusLine"></div>
    <div id="msgBox"></div>

    <p class="hint">
      Browsers cannot pick a folder path for Python; paste the path here
      (e.g. Finder → drag folder into Terminal first, or <code>Cmd+Shift+G</code> in Finder and copy path).<br><br>
      Only runs on your computer (<code>127.0.0.1</code> — not exposed to the internet).
    </p>
  </main>

  <script>
    const urlEl = document.getElementById('url');
    const outEl = document.getElementById('outdir');
    const chkEl = document.getElementById('fullplaylist');
    const btn = document.getElementById('go');
    const pWrap = document.getElementById('progressWrap');
    const pBar = document.getElementById('progressBar');
    const statusLine = document.getElementById('statusLine');
    const msgBox = document.getElementById('msgBox');

    function showMsg(ok, text) {
      msgBox.textContent = text;
      msgBox.className = 'show ' + (ok ? 'ok' : 'err');
    }
    function clearMsg() {
      msgBox.className = ''; msgBox.textContent = '';
    }

    let pollTimer = null;
    function stopPoll() {
      if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
    }

    async function poll(jobId) {
      const r = await fetch('/api/job/' + jobId);
      if (!r.ok) throw new Error('Status request failed');
      const j = await r.json();

      const pct = Math.round(j.pct ?? 0);
      pWrap.classList.add('active');
      pBar.style.width = pct + '%';

      let t = j.label || '';
      if (j.detail) t += (t ? ' — ' : '') + j.detail;
      statusLine.textContent = t;

      if (j.status === 'done') {
        stopPoll();
        btn.disabled = false;
        clearMsg();
        showMsg(true, 'Done — MP3s are in:\\n' + (j.saved_to || ''));
        return;
      }
      if (j.status === 'error') {
        stopPoll();
        btn.disabled = false;
        pWrap.classList.remove('active');
        pBar.style.width = '0%';
        showMsg(false, j.detail || j.label || 'Error');
        statusLine.textContent = '';
      }
    }

    btn.addEventListener('click', async () => {
      clearMsg();
      statusLine.textContent = '';
      pBar.style.width = '0%';
      btn.disabled = true;

      try {
        const res = await fetch('/api/start', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            url: urlEl.value.trim(),
            output_dir: outEl.value.trim(),
            full_playlist: chkEl.checked,
          }),
        });
        const data = await res.json();
        if (!res.ok) {
          showMsg(false, data.error || res.statusText);
          btn.disabled = false;
          return;
        }

        stopPoll();
        pWrap.classList.add('active');
        const onPollErr = (e) => {
          stopPoll();
          btn.disabled = false;
          showMsg(false, String(e));
          pWrap.classList.remove('active');
          pBar.style.width = '0%';
        };
        pollTimer = setInterval(() => {
          poll(data.job_id).catch(onPollErr);
        }, 450);
        poll(data.job_id).catch(onPollErr);
      } catch (e) {
        showMsg(false, String(e));
        btn.disabled = false;
      }
    });
  </script>
</body>
</html>
"""


@app.route("/", methods=["GET"])
def home():
    return render_template_string(
        PAGE,
        default_out=str(DEFAULT_OUT),
    )


@app.post("/api/start")
def api_start():
    payload = request.get_json(silent=True) or {}
    url = str(payload.get("url") or "").strip()
    if not ok_url(url):
        return jsonify({"error": "That does not look like a valid http(s) URL."}), 400

    out_raw = payload.get("output_dir")
    save_dir, err = resolve_save_dir(out_raw)
    if save_dir is None:
        return jsonify({"error": err or "Invalid save folder."}), 400

    full_playlist = bool(payload.get("full_playlist"))

    job_id = secrets.token_hex(12)
    with jobs_lock:
        _jobs[job_id] = {
            "status": "queued",
            "pct": 0.0,
            "label": "Starting…",
            "detail": "",
            "saved_to": str(save_dir),
        }

    t = threading.Thread(
        target=_run_download,
        args=(job_id, url, save_dir, full_playlist),
        daemon=True,
    )
    t.start()

    return jsonify({"job_id": job_id, "saved_to": str(save_dir)})


@app.get("/api/job/<job_id>")
def api_job(job_id: str):
    with jobs_lock:
        job = _jobs.get(job_id)
    if not job:
        return jsonify({"error": "unknown job"}), 404
    out = {
        "status": job["status"],
        "pct": job["pct"],
        "label": job["label"],
        "detail": job["detail"],
    }
    if job["status"] == "done":
        out["saved_to"] = job.get("saved_to", "")
    return jsonify(out)


if __name__ == "__main__":
    DEFAULT_OUT.mkdir(parents=True, exist_ok=True)
    app.run(host="127.0.0.1", port=5050, debug=False, threaded=True)
