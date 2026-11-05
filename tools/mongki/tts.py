"""Narration with Gemini text-to-speech (REST). Offline: silence sized to the text."""
import base64, os, time, wave
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
            pcm = base64.b64decode(part["data"])
            pcm = _trim(pcm)
            _write_wav(path, pcm); return len(pcm) / 2 / RATE
        except Exception as e:
            last = e; print(f"[tts] attempt {attempt+1} failed: {e}"); time.sleep(8 * (attempt + 1))
    raise RuntimeError(f"TTS failed: {last}")

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
