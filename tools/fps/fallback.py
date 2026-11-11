"""Backup engines for when Gemini cannot be used (billing 402, quota, outage).
  - gemini_ok(): one tiny probe call per build; False -> the whole episode uses the backups (voices stay consistent)
  - tts(): Microsoft Edge neural voices (pip edge-tts, free) mapped from the Gemini voice names
  - image(): Pollinations (free, no key) -> PIL image, or None
Every use is counted in USED and written to <outdir>/engine.json by build.py."""
import hashlib, io, os, subprocess, sys, time, urllib.parse
import numpy as np

API = "https://generativelanguage.googleapis.com/v1beta"
FORCE = os.environ.get("FPS_FORCE_FALLBACK") == "1"
USED = {"tts": "gemini", "tts_fallback_chunks": 0, "img_gemini": 0, "img_pollinations": 0, "img_substituted": 0,
        "library_made": [], "gemini_error": ""}
_state = {"ok": None}

def mark_dead(why):
    if _state["ok"] is not False: print(f"[fallback] Gemini unavailable: {why}", flush=True)
    _state["ok"] = False; USED["gemini_error"] = USED["gemini_error"] or str(why)[:300]

def gemini_ok():
    if _state["ok"] is not None: return _state["ok"]
    key = os.environ.get("GEMINI_API_KEY")
    if FORCE: mark_dead("forced by FPS_FORCE_FALLBACK=1"); return False
    if not key: _state["ok"] = True; return True   # offline test mode is handled by voice/images
    import requests
    for model in ("gemini-2.5-flash-lite", "gemini-2.5-flash"):
        try:
            r = requests.post(f"{API}/models/{model}:generateContent?key={key}", timeout=60,
                              json={"contents": [{"parts": [{"text": "Say OK"}]}], "generationConfig": {"maxOutputTokens": 4}})
            if r.status_code in (401, 402, 403): mark_dead(f"HTTP {r.status_code}: {r.text[:200]}"); return False
            if r.status_code == 429 and "quota" in r.text.lower() and "day" in r.text.lower():
                mark_dead(f"daily quota: {r.text[:200]}"); return False
            if r.ok: _state["ok"] = True; return True
        except Exception as e:
            print("[fallback] probe error", model, e, flush=True)
    _state["ok"] = True; return True   # unclear -> let the normal retries decide

def is_billing_error(status, text=""):
    return status in (401, 402, 403) or (status == 429 and "quota" in text.lower() and "day" in text.lower())

# ---------------- voices ----------------
EDGE = {  # Gemini voice -> Edge neural voice
    "Gacrux": "en-US-JennyNeural", "Pulcherrima": "en-US-AriaNeural", "Sulafat": "en-US-MichelleNeural",
    "Leda": "en-US-EmmaNeural", "Autonoe": "en-US-AvaNeural", "Kore": "en-US-AriaNeural", "Aoede": "en-US-EmmaNeural",
    "Orus": "en-US-GuyNeural", "Charon": "en-US-ChristopherNeural", "Algenib": "en-US-EricNeural",
    "Sadaltager": "en-US-RogerNeural", "Iapetus": "en-US-SteffanNeural", "Fenrir": "en-US-BrianNeural",
    "Puck": "en-US-AndrewNeural", "Zephyr": "en-US-AnaNeural"}
RATE = 24000

def _edge_line(text, voice, rate):
    import asyncio, edge_tts
    async def go():
        c = edge_tts.Communicate(text, voice, rate=rate); buf = b""
        async for ch in c.stream():
            if ch["type"] == "audio": buf += ch["data"]
        return buf
    for attempt in range(4):
        try:
            mp3 = asyncio.run(go())
            if mp3: break
        except Exception as e:
            print(f"[fallback] edge-tts attempt {attempt+1}: {e}", flush=True); time.sleep(5 * (attempt + 1))
    else:
        raise RuntimeError("edge-tts failed")
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", "pipe:0", "-f", "s16le", "-ac", "1", "-ar", str(RATE), "-"],
                         input=mp3, capture_output=True, check=True).stdout
    return np.frombuffer(pcm, np.int16).astype(np.float32)

def tts(chunk, cast):
    """Same chunk format as voice.py; returns float32 audio at 24 kHz."""
    USED["tts"] = "edge"; USED["tts_fallback_chunks"] += 1
    pieces = []
    for l in chunk["lines"]:
        c = cast[l["who"]]; v = EDGE.get(c.get("voice", ""), "en-US-JennyNeural")
        rate = "-12%" if l["who"] == list(cast)[0] else "-6%"   # narrator a bit slower, radio feel
        pieces += [_edge_line(l["text"], v, rate), np.zeros(int(0.30 * RATE), np.float32)]
    return np.concatenate(pieces[:-1]) if pieces else np.zeros(RATE, np.float32)

# ---------------- pictures ----------------
_memo = {}
def image(prompt, ratio="16:9", tag="shot"):
    if (prompt, ratio) in _memo: return _memo[(prompt, ratio)]
    im = _image(prompt, ratio, tag); _memo[(prompt, ratio)] = im; return im

def _image(prompt, ratio, tag):
    import requests
    from PIL import Image
    w, h = (1344, 768) if ratio == "16:9" else (896, 1152)
    seed = int(hashlib.sha1(prompt.encode()).hexdigest()[:6], 16)
    p = prompt[:900] + ". Photorealistic cinematic film still, warm natural light, no text, no letters, no watermark."
    url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(p)}?width={w}&height={h}&nologo=true&model=flux&seed={seed}"
    for attempt in range(3):
        try:
            r = requests.get(url, timeout=180)
            if r.ok and r.headers.get("content-type", "").startswith("image"):
                USED["img_pollinations"] += 1; print(f"[fallback] pollinations {tag}", flush=True)
                im = Image.open(io.BytesIO(r.content)).convert("RGB")
                return im.crop((0, 0, im.width, int(im.height * 0.94)))   # trims the small corner mark
            print(f"[fallback] pollinations {tag} HTTP {r.status_code}", flush=True)
        except Exception as e:
            print(f"[fallback] pollinations {tag} attempt {attempt+1}: {e}", flush=True)
        time.sleep(10 * (attempt + 1))
    return None

def nearest_library(prompt, libtxt, imgdir, avoid=()):
    """Closest existing library picture by shared words (last resort, costs nothing)."""
    import re
    words = set(re.findall(r"[a-z]{4,}", prompt.lower()))
    best, score = None, -1
    for raw in open(libtxt, encoding="utf-8"):
        if not raw.startswith("IMG "): continue
        iid, _, pr = raw[4:].partition("|"); iid = iid.strip()
        if iid in avoid or not os.path.exists(os.path.join(imgdir, iid + ".jpg")): continue
        s = len(words & set(re.findall(r"[a-z]{4,}", pr.lower())))
        if s > score: best, score = iid, s
    if best: USED["img_substituted"] += 1
    return best
