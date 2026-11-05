"""Thumbnail.
Main path: Gemini makes the whole thumbnail from the title (with the Mongki mascot as a reference image),
then a Gemini vision check rejects anything with misspelled text, a real person's face, or a brand logo,
and scores click appeal. Best passing candidate wins.
Fallback: Gemini background + text drawn in code (the old path), or a fully drawn offline thumbnail."""
import base64, io, json, os, re, time
from PIL import Image, ImageDraw
from common import OFFLINE, YEL, RED, FG, ASSETS, text_img, fit_text, mascot

API = "https://generativelanguage.googleapis.com/v1beta"
TW, TH = 1280, 720
CANDIDATES = int(os.environ.get("MONGKI_THUMB_CANDIDATES", "3"))

_models = None
def _list_models(key):
    global _models
    if _models is not None: return _models
    import requests
    try:
        r = requests.get(f"{API}/models?key={key}&pageSize=200", timeout=30); r.raise_for_status()
        _models = [m["name"].split("/")[-1] for m in r.json().get("models", [])
                   if "generateContent" in m.get("supportedGenerationMethods", [])]
    except Exception as e:
        print("[thumb] list models failed:", e); _models = []
    return _models

def _image_model(key):
    if os.environ.get("MONGKI_IMAGE_MODEL"): return os.environ["MONGKI_IMAGE_MODEL"]
    img = [n for n in _list_models(key) if "image" in n and "gemini" in n and "lite" not in n]
    return sorted(img)[-1] if img else "gemini-2.5-flash-image"

def _text_model(key):
    """Stable multimodal Flash model, highest version (e.g. gemini-3.5-flash), never preview/omni/lite."""
    if os.environ.get("MONGKI_TEXT_MODEL"): return os.environ["MONGKI_TEXT_MODEL"]
    best = None
    for n in _list_models(key):
        m = re.fullmatch(r"gemini-(\d+(?:\.\d+)?)-flash(-latest)?", n)
        if m and (best is None or float(m.group(1)) > best[0]): best = (float(m.group(1)), n)
    return best[1] if best else "gemini-2.5-flash"

def _b64(im, fmt="PNG"):
    buf = io.BytesIO(); im.save(buf, fmt); return base64.b64encode(buf.getvalue()).decode()

def _gemini_image(parts):
    import requests
    key = os.environ["GEMINI_API_KEY"]; model = _image_model(key)
    body = {"contents": [{"parts": parts}],
            "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": "16:9"}}}
    for attempt in range(3):
        try:
            r = requests.post(f"{API}/models/{model}:generateContent?key={key}", json=body, timeout=180)
            if r.status_code == 400 and "imageConfig" in r.text:
                body["generationConfig"].pop("imageConfig", None); continue
            r.raise_for_status()
            for part in r.json()["candidates"][0]["content"]["parts"]:
                if "inlineData" in part:
                    print("[thumb] image model:", model)
                    return Image.open(io.BytesIO(base64.b64decode(part["inlineData"]["data"]))).convert("RGB")
            raise RuntimeError("no image in response")
        except Exception as e:
            print(f"[thumb] image attempt {attempt+1}: {e}"); time.sleep(6 * (attempt + 1))
    return None

def _review(im, required_text):
    """Ask a Gemini vision model to check the thumbnail. Returns dict or None."""
    import requests
    key = os.environ["GEMINI_API_KEY"]; model = _text_model(key)
    q = ("You are checking a YouTube thumbnail. Answer ONLY with JSON: "
         '{"text_found": "<all text you can read, exactly>", "text_correct": true|false, '
         '"real_person": true|false, "brand_logo": true|false, "score": 1-10}. '
         f'text_correct is true only if the main headline reads exactly "{required_text}" with no spelling mistakes and no extra gibberish text. '
         "real_person is true if any face looks like a specific real, identifiable person (celebrity, politician, athlete). "
         "brand_logo is true if any real company logo or trademark appears. "
         "score = how likely a curious viewer is to click (bold, readable at small size, clear emotion, strong contrast).")
    body = {"contents": [{"parts": [{"inlineData": {"mimeType": "image/jpeg", "data": _b64(im.resize((640, 360)), "JPEG")}}, {"text": q}]}],
            "generationConfig": {"responseMimeType": "application/json"}}
    try:
        r = requests.post(f"{API}/models/{model}:generateContent?key={key}", json=body, timeout=90); r.raise_for_status()
        txt = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(re.search(r"\{.*\}", txt, re.S).group(0))
    except Exception as e:
        print("[thumb] review failed:", e); return None

def _full_prompt(ep):
    t = ep["thumb"]; headline = f'{t["big"]} {t.get("sub", "")}'.strip()
    return headline, (
        "Design the single most clickable YouTube thumbnail for a money/finance channel called Mongki Money. "
        f'Video title: "{ep["title"]}". '
        f'Put this headline in huge, bold, perfectly spelled letters, at most two lines: "{headline}". '
        + (f'Add a small red tag that says "{t["badge"]}". ' if t.get("badge") else "")
        + "Include the attached cartoon monkey mascot as the main character, redrawn bigger, furious and muscular, with a strong emotion. "
        + (f'Scene idea: {t["bg_prompt"]} ' if t.get("bg_prompt") else "")
        + "Style: high contrast, saturated, cinematic lighting, uncluttered, readable on a phone at small size, 16:9. "
        "Rules: no real people or recognizable faces, no company logos or trademarks, no other text besides the headline and tag, "
        "nothing sexual or gory.")

def _cover(im):
    s = max(TW / im.width, TH / im.height)
    im = im.resize((int(im.width * s + 1), int(im.height * s + 1)), Image.LANCZOS)
    x, y = (im.width - TW) // 2, (im.height - TH) // 2
    return im.crop((x, y, x + TW, y + TH))

def _overlay(bg, spec):
    """Old path: background + text drawn in code (always spelled right)."""
    im = _cover(bg).convert("RGBA")
    shade = Image.new("RGBA", (TW, TH), (0, 0, 0, 0)); sd = ImageDraw.Draw(shade)
    for x in range(0, 760, 4): sd.rectangle([x, 0, x + 4, TH], fill=(0, 0, 0, int(170 * (1 - x / 760))))
    im.alpha_composite(shade)
    big = fit_text(spec["big"], "heavy", 170, 700, YEL, 8); im.alpha_composite(big, (36, 20))
    if spec.get("sub"):
        sub = fit_text(spec["sub"], "heavy", 130, 700, FG, 8); im.alpha_composite(sub, (40, 20 + big.height - 6))
    if spec.get("badge"):
        badge = text_img(spec["badge"], "heavy", 70, FG); bw, bh = badge.width + 40, badge.height + 20
        b = Image.new("RGBA", (bw + 10, bh + 10), (0, 0, 0, 0)); bd = ImageDraw.Draw(b)
        bd.rectangle([0, 0, bw + 9, bh + 9], fill=(0, 0, 0)); bd.rectangle([5, 5, bw + 4, bh + 4], fill=RED)
        b.alpha_composite(badge, (25, 15)); b = b.rotate(4, expand=True, resample=Image.BICUBIC)
        im.alpha_composite(b, (60, TH - b.height - 40))
    if spec.get("corner"):
        c = text_img(spec["corner"], "heavy", 56, FG, 5); im.alpha_composite(c, (TW - c.width - 30, 20))
    return im.convert("RGB")

def _drawn_bg():
    im = Image.new("RGBA", (TW, TH), (11, 15, 26, 255)); d = ImageDraw.Draw(im)
    d.line([(300, 170), (380, 230), (430, 205), (500, 300), (560, 270), (640, 420), (700, 400), (790, 600)], fill=RED, width=22, joint="curve")
    m = mascot("muscle", 700); im.alpha_composite(m, (TW - 640, TH - 600))
    return im.convert("RGB")

def make(ep, out):
    spec = ep["thumb"]; report = {"mode": None, "candidates": []}
    if not OFFLINE and os.environ.get("GEMINI_API_KEY"):
        headline, prompt = _full_prompt(ep)
        ref = Image.open(os.path.join(ASSETS, "mongki_muscle.png")).convert("RGB")
        parts = [{"inlineData": {"mimeType": "image/png", "data": _b64(ref.resize((600, 600)))}}, {"text": prompt}]
        best = None
        for k in range(CANDIDATES):
            im = _gemini_image(parts)
            if im is None: continue
            rv = _review(im, headline) or {}
            ok = rv.get("text_correct") is True and rv.get("real_person") is False and rv.get("brand_logo") is False
            report["candidates"].append({"ok": ok, **{x: rv.get(x) for x in ("text_found", "real_person", "brand_logo", "score")}})
            print(f"[thumb] candidate {k+1}: ok={ok} review={rv}")
            if ok and (best is None or (rv.get("score") or 0) > best[0]):
                best = ((rv.get("score") or 0), im)
        if best:
            _cover(best[1]).save(out, quality=92); report["mode"] = "gemini_full"
        else:
            bg = _gemini_image([{"text": spec["bg_prompt"]}]) if spec.get("bg_prompt") else None
            _overlay(bg if bg else _drawn_bg(), spec).save(out, quality=92)
            report["mode"] = "gemini_bg+code_text" if bg else "drawn"
    else:
        _overlay(_drawn_bg(), spec).save(out, quality=92); report["mode"] = "drawn"
    json.dump(report, open(os.path.splitext(out)[0] + "_report.json", "w"), indent=1, default=str)
    print("[thumb] saved", out, report["mode"])
