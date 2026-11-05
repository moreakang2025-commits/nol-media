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

def clicks(path, thresh=900, win=0.01):
    """Times (s) of impulsive noise: windows where ffmpeg's adeclick had to change the signal a lot."""
    import subprocess
    with wave.open(path) as w: x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32)
    if len(x) < RATE // 10: return []
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-af", "adeclick=w=55:o=75:t=2", "-f", "s16le", "-ac", "1",
                        "-ar", str(RATE), "-"], capture_output=True)
    y = np.frombuffer(p.stdout, np.int16).astype(np.float32)[: len(x)]
    if len(y) < len(x): y = np.pad(y, (0, len(x) - len(y)))
    n = int(win * RATE); k = len(x) // n
    d = np.abs(x[: k * n] - y[: k * n]).reshape(k, n).max(axis=1)
    hits = [h for h in np.where(d > thresh)[0] if 3 <= h < k - 3]   # ignore filter edge effects
    out = []
    for h in hits:
        t = float(round(h * win, 2))
        if not out or t - out[-1] > 0.05: out.append(t)
    return out

def synth_clean(text, path, tries=3):
    """Synthesize, check for clicks, and regenerate (up to `tries`) keeping the cleanest take."""
    best = None
    for k in range(tries):
        tmp = path + f".take{k}.wav"
        d = synth(text, tmp)
        c = clicks(tmp) if d > 0 else []
        print(f"[tts] take {k+1}: {d:.1f}s, clicks={c[:8]}")
        if best is None or len(c) < len(best[2]): best = (tmp, d, c)
        if not c or OFFLINE or not os.environ.get("GEMINI_API_KEY"): break
    os.replace(best[0], path)
    for k in range(tries):
        f = path + f".take{k}.wav"
        if os.path.exists(f): os.remove(f)
    return best[1], best[2]

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
