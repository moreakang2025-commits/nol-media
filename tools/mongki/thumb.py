"""Thumbnail: Gemini photorealistic background (no text, no logos, no real people) + text drawn in code."""
import base64, io, os, time
from PIL import Image, ImageDraw, ImageFilter
from common import OFFLINE, YEL, RED, FG, BLUE, text_img, fit_text, mascot

API = "https://generativelanguage.googleapis.com/v1beta"
TW, TH = 1280, 720

def _pick_image_model(key):
    import requests
    want = os.environ.get("MONGKI_IMAGE_MODEL")
    if want: return want
    try:
        r = requests.get(f"{API}/models?key={key}&pageSize=200", timeout=30); r.raise_for_status()
        names = [m["name"].split("/")[-1] for m in r.json().get("models", [])
                 if "generateContent" in m.get("supportedGenerationMethods", [])]
        img = [n for n in names if "image" in n and "gemini" in n]
        if img: return sorted(img)[-1]
    except Exception as e:
        print("[thumb] list models failed:", e)
    return "gemini-2.5-flash-image"

def _gemini_bg(prompt):
    import requests
    key = os.environ["GEMINI_API_KEY"]; model = _pick_image_model(key); print("[thumb] model:", model)
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": "16:9"}}}
    for attempt in range(4):
        try:
            r = requests.post(f"{API}/models/{model}:generateContent?key={key}", json=body, timeout=180)
            if r.status_code == 400 and "imageConfig" in r.text:
                body["generationConfig"].pop("imageConfig", None); continue
            r.raise_for_status()
            for part in r.json()["candidates"][0]["content"]["parts"]:
                if "inlineData" in part:
                    return Image.open(io.BytesIO(base64.b64decode(part["inlineData"]["data"]))).convert("RGB")
            raise RuntimeError("no image in response")
        except Exception as e:
            print(f"[thumb] attempt {attempt+1}: {e}"); time.sleep(6 * (attempt + 1))
    return None

def _fallback_bg():
    im = Image.new("RGBA", (TW, TH), (11, 15, 26, 255)); d = ImageDraw.Draw(im)
    d.line([(300, 170), (380, 230), (430, 205), (500, 300), (560, 270), (640, 420), (700, 400), (790, 600)], fill=RED, width=22, joint="curve")
    m = mascot("muscle", 700); im.alpha_composite(m, (TW - 640, TH - 600))
    return im.convert("RGB")

def _cover(im):
    s = max(TW / im.width, TH / im.height)
    im = im.resize((int(im.width * s + 1), int(im.height * s + 1)), Image.LANCZOS)
    x, y = (im.width - TW) // 2, (im.height - TH) // 2
    return im.crop((x, y, x + TW, y + TH))

def make(ep, out):
    spec = ep["thumb"]; bg = None
    if not OFFLINE and os.environ.get("GEMINI_API_KEY"):
        bg = _gemini_bg(spec["bg_prompt"])
    im = _cover(bg if bg else _fallback_bg()).convert("RGBA")
    shade = Image.new("RGBA", (TW, TH), (0, 0, 0, 0)); sd = ImageDraw.Draw(shade)
    for x in range(0, 760, 4): sd.rectangle([x, 0, x + 4, TH], fill=(0, 0, 0, int(170 * (1 - x / 760))))
    im.alpha_composite(shade)
    big = fit_text(spec["big"], "heavy", 170, 700, YEL, 8); im.alpha_composite(big, (36, 20))
    sub = fit_text(spec["sub"], "heavy", 130, 700, FG, 8); im.alpha_composite(sub, (40, 20 + big.height - 6))
    badge = text_img(spec["badge"], "heavy", 70, FG); bw, bh = badge.width + 40, badge.height + 20
    b = Image.new("RGBA", (bw + 10, bh + 10), (0, 0, 0, 0)); bd = ImageDraw.Draw(b)
    bd.rectangle([0, 0, bw + 9, bh + 9], fill=(0, 0, 0)); bd.rectangle([5, 5, bw + 4, bh + 4], fill=RED)
    b.alpha_composite(badge, (25, 15)); b = b.rotate(4, expand=True, resample=Image.BICUBIC)
    im.alpha_composite(b, (60, TH - b.height - 40))
    if spec.get("corner"):
        c = text_img(spec["corner"], "heavy", 56, FG, 5); im.alpha_composite(c, (TW - c.width - 30, 20))
    im.convert("RGB").save(out, quality=92)
    print("[thumb] saved", out, "(gemini)" if bg else "(fallback)")
