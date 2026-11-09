"""Gemini TTS for Front Porch Stories: one voice per character, up to 2 speakers per request.
Lines are grouped into chunks (<= MAX_WORDS, <= 2 speakers). Each chunk is cached by content hash."""
import base64, hashlib, os, re, shutil, sys, time, wave
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mongki"))
import tts as MT   # decode / trim / analyze helpers from the Mongki pipeline

API = "https://generativelanguage.googleapis.com/v1beta"
RATE = 24000
MAX_WORDS = int(os.environ.get("FPS_CHUNK_WORDS", "230"))
CACHE = os.environ.get("FPS_TTS_CACHE", os.path.join(os.path.dirname(__file__), "..", "..", "fps", "cache", "tts"))
OFFLINE = os.environ.get("FPS_OFFLINE") == "1" or not os.environ.get("GEMINI_API_KEY")

def _write(path, a):
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE)
        w.writeframes(np.clip(np.asarray(a, np.float32), -32767, 32767).astype(np.int16).tobytes())

def read(path):
    with wave.open(path) as w: return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32)

def chunk_lines(lines, cast):
    """lines: [{'who','text','idx'}] -> chunks [{'lines': [...], 'speakers': [...]}]"""
    out, cur, spk, n = [], [], [], 0
    for ln in lines:
        w = len(ln["text"].split())
        new_spk = ln["who"] not in spk
        if cur and (n + w > MAX_WORDS or (new_spk and len(spk) == 2)):
            out.append({"lines": cur, "speakers": spk}); cur, spk, n = [], [], 0
        cur.append(ln); n += w
        if ln["who"] not in spk: spk.append(ln["who"])
    if cur: out.append({"lines": cur, "speakers": spk})
    return out

def _request(chunk, cast, style_intro):
    spk = chunk["speakers"]
    def name(k): return cast[k]["name"]
    if len(spk) == 1:
        c = cast[spk[0]]
        prompt = (f"{style_intro}\nRead this aloud as {name(spk[0])}: {c.get('style','')}. "
                  "Say exactly the words below, nothing else, no labels:\n\n" + " ".join(l["text"] for l in chunk["lines"]))
        sc = {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": c["voice"]}}}
    else:
        desc = " ".join(f"{name(k)}: {cast[k].get('style','')}." for k in spk)
        body = "\n".join(f"{name(l['who'])}: {l['text']}" for l in chunk["lines"])
        prompt = (f"{style_intro}\nTTS the following conversation between {name(spk[0])} and {name(spk[1])}. "
                  f"{desc} Speak only the words after each name.\n\n{body}")
        sc = {"multiSpeakerVoiceConfig": {"speakerVoiceConfigs": [
            {"speaker": name(k), "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": cast[k]["voice"]}}} for k in spk]}}
    return prompt, sc

def synth_chunk(chunk, cast, style_intro, path):
    """Write wav for one chunk, return seconds."""
    words = sum(len(l["text"].split()) for l in chunk["lines"])
    if OFFLINE:
        secs = words / 2.45; _write(path, np.zeros(int(secs * RATE))); return secs
    prompt, sc = _request(chunk, cast, style_intro)
    os.makedirs(CACHE, exist_ok=True)
    h = hashlib.sha1(("v2|" + prompt + repr(sc)).encode()).hexdigest()[:16]
    cached = os.path.join(CACHE, h + ".wav")
    if os.path.exists(cached):
        shutil.copy(cached, path); d = len(read(path)) / RATE
        print(f"[voice] cached {h} {d:.1f}s", flush=True); return d
    import requests
    key = os.environ["GEMINI_API_KEY"]; model = MT._pick_model(key)
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": sc}}
    best, last = None, None
    for attempt in range(6):
        try:
            r = requests.post(f"{API}/models/{model}:generateContent?key={key}", json=body, timeout=300)
            if r.status_code == 429 or r.status_code >= 500:
                raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
            r.raise_for_status()
            part = r.json()["candidates"][0]["content"]["parts"][0]["inlineData"]
            pcm = MT._trim(MT._decode(base64.b64decode(part["data"]), part.get("mimeType", "")))
            a = np.frombuffer(pcm, np.int16).astype(np.float32); d = len(a) / RATE
            wpm = words / max(d, 1) * 60
            ok = 95 <= wpm <= 205   # catches truncated or runaway (off-script) takes
            print(f"[voice] {h} take {attempt+1}: {d:.1f}s {wpm:.0f} wpm {'ok' if ok else 'REJECT'}", flush=True)
            if best is None or abs(wpm - 150) < abs(best[1] - 150): best = (a, wpm)
            if ok: break
            time.sleep(4)
        except Exception as e:
            last = e; print(f"[voice] attempt {attempt+1} failed: {e}", flush=True); time.sleep(min(60, 10 * (attempt + 1)))
    if best is None: raise RuntimeError(f"TTS failed: {last}")
    _write(path, best[0]); shutil.copy(path, cached)
    return len(best[0]) / RATE
