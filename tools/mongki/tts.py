"""Narration with Gemini text-to-speech (REST). Offline: silence sized to the text."""
import base64, os, re, time, wave
import numpy as np
from common import OFFLINE

API = "https://generativelanguage.googleapis.com/v1beta"
RATE = 24000
VOICE = os.environ.get("MONGKI_VOICE", "Puck")
STYLE = ("Read this as a punchy, high-energy YouTube money-channel narrator. Confident, fast, "
         "a little playful, with short dramatic pauses at full stops. Say exactly: ")

_model = None

def _pick_model(key):
    global _model
    if _model: return _model
    import requests
    want = os.environ.get("MONGKI_TTS_MODEL")
    if want:
        _model = want; return _model
    names = []
    try:
        r = requests.get(f"{API}/models?key={key}&pageSize=200", timeout=30); r.raise_for_status()
        names = [m["name"].split("/")[-1] for m in r.json().get("models", [])
                 if "generateContent" in m.get("supportedGenerationMethods", [])]
    except Exception as e:
        print("[tts] list models failed:", e)
    tts = [n for n in names if "tts" in n]
    pref = [n for n in tts if "flash" in n and "pro" not in n] or tts
    _model = sorted(pref)[-1] if pref else "gemini-2.5-flash-preview-tts"
    print("[tts] model:", _model); return _model

def _write_wav(path, pcm):
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE); w.writeframes(pcm)

def synth(text, path):
    """Write a 24 kHz mono wav for `text`. Returns duration in seconds."""
    if not text.strip():
        _write_wav(path, b""); return 0.0
    if OFFLINE or not os.environ.get("GEMINI_API_KEY"):
        secs = max(1.0, len(text.split()) / 2.7)
        _write_wav(path, np.zeros(int(secs * RATE), np.int16).tobytes()); return secs
    import requests
    key = os.environ["GEMINI_API_KEY"]; model = _pick_model(key)
    body = {"contents": [{"parts": [{"text": STYLE + text}]}],
            "generationConfig": {"responseModalities": ["AUDIO"],
                                 "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": VOICE}}}}}
    last = None
    for attempt in range(5):
        try:
            r = requests.post(f"{API}/models/{model}:generateContent?key={key}", json=body, timeout=180)
            if r.status_code == 429 or r.status_code >= 500:
                raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
            r.raise_for_status()
            part = r.json()["candidates"][0]["content"]["parts"][0]["inlineData"]
            pcm = _decode(base64.b64decode(part["data"]), part.get("mimeType", ""))
            pcm = _trim(pcm)
            _write_wav(path, pcm); return len(pcm) / 2 / RATE
        except Exception as e:
            last = e; print(f"[tts] attempt {attempt+1} failed: {e}"); time.sleep(8 * (attempt + 1))
    raise RuntimeError(f"TTS failed: {last}")

def _decode(raw, mime):
    """Gemini TTS returns 16-bit mono PCM (audio/L16;rate=24000). Strip a WAV header if one is present
    and resample to RATE if the reported rate differs, so nothing is misread as noise."""
    rate = RATE
    m = re.search(r"rate=(\d+)", mime or "")
    if m: rate = int(m.group(1))
    if raw[:4] == b"RIFF":
        import io
        with wave.open(io.BytesIO(raw)) as w: rate = w.getframerate(); raw = w.readframes(w.getnframes())
    a = np.frombuffer(raw[: len(raw) // 2 * 2], np.int16).astype(np.float32)
    if rate != RATE and len(a):
        n = int(len(a) * RATE / rate); a = np.interp(np.linspace(0, len(a) - 1, n), np.arange(len(a)), a)
    return np.clip(a, -32767, 32767).astype(np.int16).tobytes()

CACHE = os.path.join(os.path.dirname(__file__), "..", "..", "mongki", "cache", "tts")
CALLS = {"n": 0}; BUDGET = int(os.environ.get("MONGKI_TTS_BUDGET", "40"))

def analyze(x):
    """Real defects only, measured on raw samples (int16 array):
    clipped = samples pinned at full scale in runs of 3+ (digital clipping = crackle),
    jumps  = times where one sample step is huge versus the local signal (a discontinuity/click)."""
    x = np.asarray(x, np.float32)
    if len(x) < 100: return {"clipped": 0, "jumps": []}
    hot = np.abs(x) >= 32000
    runs = np.convolve(hot.astype(np.int8), np.ones(3, np.int8), "valid") == 3
    d = np.abs(np.diff(x)); n = 240
    k = len(d) // n
    loc = np.median(d[: k * n].reshape(k, n), axis=1).repeat(n)
    loc = np.pad(loc, (0, len(d) - len(loc)), mode="edge")
    bad = np.where((d > 12000) & (d > 25 * (loc + 50)))[0]
    jumps = []
    for b in bad:
        t = round(float(b) / RATE, 2)
        if not jumps or t - jumps[-1] > 0.05: jumps.append(t)
    return {"clipped": int(runs.sum()), "jumps": jumps}

def _read(path):
    with wave.open(path) as w: return np.frombuffer(w.readframes(w.getnframes()), np.int16)

def clicks(path):
    return analyze(_read(path))["jumps"]

def synth_clean(text, path, tries=2):
    """Synthesize once (cached by text), check for real defects, retake once only if it is actually broken.
    Returns (duration, report)."""
    import hashlib, shutil
    os.makedirs(CACHE, exist_ok=True)
    h = hashlib.sha1(f"{VOICE}|{STYLE}|{text}".encode()).hexdigest()[:16]
    cached = os.path.join(CACHE, h + ".wav")
    live = not (OFFLINE or not os.environ.get("GEMINI_API_KEY"))
    if live and text.strip() and os.path.exists(cached):
        shutil.copy(cached, path); x = _read(path); rep = analyze(x)
        print(f"[tts] cached {h}: {len(x)/RATE:.1f}s {rep}"); return len(x) / RATE, rep
    best = None
    for k in range(tries):
        tmp = path + f".take{k}.wav"
        if live and text.strip():
            if CALLS["n"] >= BUDGET and best: break
            CALLS["n"] += 1
        d = synth(text, tmp); rep = analyze(_read(tmp)) if d > 0 else {"clipped": 0, "jumps": []}
        score = rep["clipped"] + 50 * len(rep["jumps"])
        print(f"[tts] take {k+1}: {d:.1f}s {rep}")
        if best is None or score < best[3]: best = (tmp, d, rep, score)
        if score == 0 or not live: break
    os.replace(best[0], path)
    for k in range(tries):
        f = path + f".take{k}.wav"
        if os.path.exists(f): os.remove(f)
    if live and text.strip(): shutil.copy(path, cached)
    return best[1], best[2]

def desmack(a, q=None, max_amp=None, fr=60, quiet_need=6, max_len=6):
    """Remove isolated ticks/lip-smacks inside pauses (the audible 'tsk/chik' crackle): a burst of at most
    max_len*2.5 ms, quieter than max_amp, with at least quiet_need*2.5 ms of near-silence on both sides.
    Word onsets are kept because they are followed by continuing sound. Returns (float32 array, count)."""
    a = np.asarray(a, np.float32).copy(); m = len(a) // fr
    if m < 3 * quiet_need: return a, 0
    act = a[np.abs(a) > 0.02 * (np.abs(a).max() + 1)]
    rms = float(np.sqrt((act ** 2).mean())) if len(act) else 0.0
    if q is None: q = max(40.0, 0.07 * rms)            # 250 at a typical TTS level (rms ~3600)
    if max_amp is None: max_amp = max(400.0, 0.8 * rms)
    env = np.abs(a[: m * fr]).reshape(m, fr).max(axis=1); quiet = env < q
    i = 0; n = 0
    while i < m:
        if quiet[i]: i += 1; continue
        j = i
        while j < m and not quiet[j]: j += 1
        if (j - i) <= max_len and env[i:j].max() < max_amp and i >= quiet_need and j + quiet_need <= m \
                and quiet[i - quiet_need:i].all() and quiet[j:j + quiet_need].all():
            a[i * fr:j * fr] = 0.0; n += 1
        i = j
    return a, n

def _trim(pcm):
    a = np.frombuffer(pcm, np.int16).astype(np.float32)
    loud = np.where(np.abs(a) > 300)[0]
    if len(loud): a = a[max(0, loud[0] - int(0.08 * RATE)): min(len(a), loud[-1] + int(0.20 * RATE))]
    return fade(a).astype(np.int16).tobytes()

def fade(a, fin=0.015, fout=0.04):
    """Short fade-in/out so clips never start or stop mid-waveform (that is what makes clicks)."""
    a = np.asarray(a, np.float32).copy(); n_in, n_out = int(fin * RATE), int(fout * RATE)
    if len(a) > n_in + n_out:
        a[:n_in] *= np.linspace(0, 1, n_in); a[-n_out:] *= np.linspace(1, 0, n_out)
    return a


def master(raw_wav, out_wav, chain):
    """ffmpeg master chain, then remove pause ticks again at the new level (filters can ring into pauses)."""
    import subprocess
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", raw_wav, "-af", chain, "-ar", "48000", "-ac", "1",
                        "-f", "s16le", "-"], capture_output=True, check=True)
    y = np.frombuffer(p.stdout, np.int16).astype(np.float32)
    y, n = desmack(y, fr=120)                           # 2.5 ms frames at 48 kHz
    with wave.open(out_wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(48000)
        w.writeframes(np.clip(y, -32767, 32767).astype(np.int16).tobytes())
    return n
