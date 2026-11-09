"""Gemini images for Front Porch Stories: one reference portrait per character, then every shot is
generated with the matching portraits attached so faces stay consistent. Cached by prompt hash."""
import base64, hashlib, io, os, re, sys, time
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mongki"))

API = "https://generativelanguage.googleapis.com/v1beta"
CACHE = os.environ.get("FPS_IMG_CACHE", os.path.join(os.path.dirname(__file__), "..", "..", "fps", "cache", "img"))
OFFLINE = os.environ.get("FPS_OFFLINE") == "1" or not os.environ.get("GEMINI_API_KEY")
STYLE = ("Photorealistic cinematic film still from an American family drama, small-town Ohio, autumn, "
         "warm natural window light, soft film grain, 35mm lens, shallow depth of field, muted warm color grade. "
         "Absolutely no text, no letters, no captions, no logos, no watermark, no subtitles.")
_model = None

def _image_model(key):
    global _model
    if _model: return _model
    if os.environ.get("FPS_IMAGE_MODEL"): _model = os.environ["FPS_IMAGE_MODEL"]; return _model
    import requests
    try:
        r = requests.get(f"{API}/models?key={key}&pageSize=200", timeout=30); r.raise_for_status()
        names = [m["name"].split("/")[-1] for m in r.json().get("models", [])
                 if "generateContent" in m.get("supportedGenerationMethods", [])]
    except Exception as e:
        print("[img] list models failed:", e); names = []
    img = [n for n in names if "image" in n and "gemini" in n and "lite" not in n]
    _model = sorted(img)[-1] if img else "gemini-2.5-flash-image"
    print("[img] model:", _model, flush=True); return _model

def _b64(im):
    buf = io.BytesIO(); im.convert("RGB").save(buf, "JPEG", quality=90); return base64.b64encode(buf.getvalue()).decode()

def _placeholder(prompt, ratio):
    w, h = (1344, 768) if ratio == "16:9" else (896, 1152)
    im = Image.new("RGB", (w, h), (60, 45, 40)); d = ImageDraw.Draw(im)
    d.text((40, 40), prompt[:90], fill=(240, 220, 200)); return im

def generate(prompt, refs=(), ratio="16:9", tag="shot"):
    """refs: [(label, PIL image)]. Returns PIL RGB image (cached)."""
    full = f"{prompt}\n\n{STYLE}"
    h = hashlib.sha1(("v1|" + ratio + full + "|".join(l for l, _ in refs)).encode()).hexdigest()[:16]
    os.makedirs(CACHE, exist_ok=True); path = os.path.join(CACHE, f"{tag}_{h}.jpg")
    if os.path.exists(path): return Image.open(path).convert("RGB")
    if OFFLINE:
        im = _placeholder(prompt, ratio); im.save(path, quality=88); return im
    import requests
    key = os.environ["GEMINI_API_KEY"]; model = _image_model(key)
    parts = []
    for label, im in refs:
        parts.append({"inlineData": {"mimeType": "image/jpeg", "data": _b64(im.resize((512, int(512 * im.height / im.width))))}})
        parts.append({"text": f"Reference photo of {label}. Keep this exact face, age, hair and build whenever {label} appears."})
    parts.append({"text": full})
    body = {"contents": [{"parts": parts}],
            "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": ratio}}}
    for attempt in range(5):
        try:
            r = requests.post(f"{API}/models/{model}:generateContent?key={key}", json=body, timeout=240)
            if r.status_code == 400 and "imageConfig" in r.text:
                body["generationConfig"].pop("imageConfig", None); continue
            if r.status_code == 429 or r.status_code >= 500: raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
            r.raise_for_status()
            for part in r.json()["candidates"][0]["content"].get("parts", []):
                if "inlineData" in part:
                    im = Image.open(io.BytesIO(base64.b64decode(part["inlineData"]["data"]))).convert("RGB")
                    im.save(path, quality=90); print(f"[img] {tag} {h} {im.size}", flush=True); return im
            raise RuntimeError("no image in response: " + str(r.json())[:300])
        except Exception as e:
            print(f"[img] {tag} attempt {attempt+1}: {e}", flush=True); time.sleep(min(60, 8 * (attempt + 1)))
    return None

def portraits(cast):
    """Reference portrait for every cast member with a look=."""
    out = {}
    for k, c in cast.items():
        if not c.get("look"): continue
        p = (f"Head-and-shoulders portrait photo of {c['name']}, {c['look']}. Neutral expression, plain softly lit "
             "background, looking slightly off camera.")
        im = generate(p, ratio="3:4", tag=f"ref_{c['name'].lower()}")
        if im is not None: out[k] = im
    return out

def refs_for(prompt, cast, refs, limit=3):
    found = []
    for k, c in cast.items():
        if k in refs and re.search(rf"\b{re.escape(c['name'])}\b", prompt, re.I):
            found.append((c["name"], refs[k]))
    return found[:limit]
