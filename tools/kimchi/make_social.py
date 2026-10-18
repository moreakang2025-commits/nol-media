"""X + TikTok assets for every kimchi recipe, built from kimchi/pins.json and the pin images.

Usage: python3 tools/kimchi/make_social.py [--ids 61,72] [--limit N]
Writes kimchi/tt/tNNN.mp4 (720x1280, ~9s, original soundtrack) and kimchi/social.json
X posts reuse the 1000x1500 pin image (kimchi/pins/pNNN.png).
"""
import json, os, re, subprocess, sys, tempfile, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = "https://raw.githubusercontent.com/moreakang2025-commits/nol-media/main/"
FREE = "nolnull.gumroad.com/l/kimchi-free"
W, H, FPS = 720, 1280, 24
SERIF = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
SANS = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
SANSR = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
F = lambda p, s: ImageFont.truetype(p, int(s), index=1)  # index 1 = KR face
DEEP = (94, 17, 23); GOLD = (176, 136, 75); PAPER = (245, 238, 225); INK = (29, 25, 20); RED = (163, 35, 43); MUTE = (122, 111, 98)
HEAT = ["no chili", "mild", "spicy", "extra spicy"]


def parse(p):
    m = re.match(r"(.+?) \((.+?)\) \|", p["title"]) or re.match(r"(.+?) \|", p["title"])
    en = m.group(1).strip(); ko = m.group(2).strip() if m.lastindex and m.lastindex > 1 else ""
    if not ko:
        ko = re.search(r"\((.+?)\)", p["alt"]).group(1)
    d = p["description"]
    hook = d.split(f" {en}")[0].strip() if f" {en}" in d else d.split(". ")[0] + "."
    heat = next((h for h in HEAT[::-1] if f"is a {h.replace('no chili','no-chili')}" in d or f"is an {h}" in d), "")
    tm = re.search(r"Time: ([^.]+)\.", d); tm = tm.group(1) if tm else ""
    return dict(id=p["id"], en=en, ko=ko, hook=hook, heat=heat, time=tm, pin=os.path.join(ROOT, p["image"]), pin_url=p["image_url"])


def wrap(d, text, font, maxw):
    out, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) > maxw and cur: out.append(cur); cur = w
        else: cur = t
    return out + [cur]


def ctext(d, y, lines, font, fill, lh=1.18):
    for L in lines:
        d.text(((W - d.textlength(L, font=font)) / 2, y), L, font=font, fill=fill); y += int(font.size * lh)
    return y


def fit(d, text, path, size, maxw, maxlines):
    f = F(path, size); L = wrap(d, text, f, maxw)
    while len(L) > maxlines and size > 30:
        size -= 4; f = F(path, size); L = wrap(d, text, f, maxw)
    return f, L


def hook_card(r):
    im = Image.new("RGB", (W, H), PAPER); d = ImageDraw.Draw(im)
    d.rectangle([22, 22, W - 22, H - 22], outline=GOLD, width=3)
    f, L = fit(d, r["hook"], SERIF, 64, W - 120, 5)
    total = len(L) * int(f.size * 1.18)
    y = ctext(d, (H - total) / 2 - 170, L, f, INK)
    d.line([(W / 2 - 60, y + 40), (W / 2 + 60, y + 40)], fill=GOLD, width=3)
    y = ctext(d, y + 80, [r["ko"]], F(SERIF, 96), RED)
    fe, Le = fit(d, r["en"], SERIF, 50, W - 120, 2)
    y = ctext(d, y + 10, Le, fe, INK)
    meta = "  ·  ".join(x for x in [r["time"], r["heat"]] if x)
    ctext(d, y + 26, [meta.upper()], F(SANSR, 28), MUTE)
    ctext(d, H - 120, [f"RECIPE {r['id']} OF 101"], F(SANS, 26), GOLD)
    return im


def cta_card(r):
    im = Image.new("RGB", (W, H), DEEP); d = ImageDraw.Draw(im)
    d.rectangle([22, 22, W - 22, H - 22], outline=GOLD, width=3)
    y = ctext(d, 380, ["save this"], F(SERIF, 92), PAPER)
    y = ctext(d, y + 20, ["for kimchi day"], F(SERIF, 64), (220, 200, 170))
    d.line([(W / 2 - 60, y + 50), (W / 2 + 60, y + 50)], fill=GOLD, width=3)
    y = ctext(d, y + 100, ["5 recipes free"], F(SANS, 56), GOLD)
    ctext(d, y + 10, ["link in bio"], F(SANSR, 44), PAPER)
    return im


def pin_frames(r, n):
    from PIL import ImageFilter
    pin = Image.open(r["pin"]).convert("RGB")
    bg = pin.resize((int(pin.width * H / pin.height * 1.35), int(H * 1.35)), Image.BILINEAR)
    bx = (bg.width - W) // 2; by = (bg.height - H) // 2
    bg = bg.crop((bx, by, bx + W, by + H)).filter(ImageFilter.GaussianBlur(28))
    bg = Image.blend(bg, Image.new("RGB", (W, H), (20, 12, 10)), 0.35)
    for i in range(n):
        t = i / max(1, n - 1); e = t * t * (3 - 2 * t)
        s = 1.0 + 0.16 * e  # slow push-in toward the ingredients box
        pw = int(W * s); ph = int(pin.height * pw / pin.width)
        im = pin.resize((pw, ph), Image.BILINEAR)
        fr = bg.copy()
        x = (W - pw) // 2; y = (H - ph) // 2 - int(0.18 * ph * e) + int(0.06 * ph * e)
        fr.paste(im, (x, y))
        yield fr


def ease_in(img, i, n, base):
    """quick zoom punch-in for the first frames of a scene"""
    if i >= n: return img
    s = 1.06 - 0.06 * i / n
    big = img.resize((int(W * s), int(H * s)), Image.BILINEAR)
    x = (big.width - W) // 2; y = (big.height - H) // 2
    return big.crop((x, y, x + W, y + H))


def soundtrack(path, total, cuts, sr=44100):
    """Original, royalty-free: soft kick on cuts, pentatonic pluck melody, light shaker."""
    n = int(total * sr); t = np.arange(n) / sr; out = np.zeros(n)
    rng = np.random.default_rng(11)
    def add(at, sig):
        i = int(at * sr); m = min(len(sig), n - i)
        if m > 0: out[i:i + m] += sig[:m]
    def pluck(freq, amp=0.18, dur=0.45):
        tt = np.arange(int(dur * sr)) / sr
        return amp * np.sin(2 * np.pi * freq * tt) * np.exp(-tt * 7) + amp * 0.3 * np.sin(4 * np.pi * freq * tt) * np.exp(-tt * 12)
    def kick(amp=0.6):
        tt = np.arange(int(0.25 * sr)) / sr; f = 50 + 90 * np.exp(-tt * 30)
        return amp * np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-tt * 14)
    scale = [293.66, 329.63, 392.0, 440.0, 493.88, 587.33]  # D major pentatonic
    beat = 60 / 112
    x, k = 0.0, 0
    while x < total:
        if k % 2 == 0: add(x, kick(0.35))
        add(x, pluck(scale[[0, 2, 4, 3, 5, 4, 2, 1][k % 8]]))
        sh = rng.standard_normal(int(0.04 * sr)) * np.exp(-np.arange(int(0.04 * sr)) / sr * 80) * 0.05
        add(x + beat / 2, sh)
        x += beat; k += 1
    for c in cuts: add(c, kick(0.5))
    out += 0.05 * np.sin(2 * np.pi * 146.83 * t)
    fade = np.minimum(1, np.minimum(t / 0.15, (total - t) / 0.3))
    pcm = (np.tanh(out * 1.4) * 0.75 * fade * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())


def video(r, out):
    A, B, C, D = 2.4, 4.6, 1.8, 0.5  # hook, pin scroll, cta, loop-back
    total = A + B + C + D
    wav = tempfile.mktemp(suffix=".wav"); soundtrack(wav, total, [A, A + B, A + B + C])
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-i", wav, "-shortest", "-c:v", "libx264", "-preset", "veryfast", "-crf", "24", "-pix_fmt", "yuv420p",
                          "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    hk = hook_card(r); ct = cta_card(r)
    for i in range(int(A * FPS)): p.stdin.write(np.asarray(ease_in(hk, i, 5, hk)).tobytes())
    for fr in pin_frames(r, int(B * FPS)): p.stdin.write(np.asarray(fr).tobytes())
    for i in range(int(C * FPS)): p.stdin.write(np.asarray(ease_in(ct, i, 5, ct)).tobytes())
    for i in range(int(D * FPS)): p.stdin.write(np.asarray(hk).tobytes())
    p.stdin.close(); p.wait(); os.remove(wav)


def captions(r):
    meta = " · ".join(x for x in [r["time"], r["heat"]] if x)
    x_text = f"{r['hook']}\n\n{r['en']} ({r['ko']}) · {meta}\n\nRecipe {r['id']} of 101. Save it for later 🥬"
    x_link = f"Full recipe + 4 more, free → {FREE}"
    tt = f"{r['hook']} {r['en']} ({r['ko']}) 🥬 recipe {r['id']}/101 · 5 recipes free, link in bio #kimchi #koreanfood #kfood #recipe #fyp"
    return x_text, x_link, tt[:2200], f"{r['en']} recipe"


def main():
    pins = json.load(open(os.path.join(ROOT, "kimchi/pins.json"), encoding="utf-8"))
    ids = None
    if "--ids" in sys.argv: ids = {int(v) for v in sys.argv[sys.argv.index("--ids") + 1].split(",")}
    lim = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
    os.makedirs(os.path.join(ROOT, "kimchi/tt"), exist_ok=True)
    sp = os.path.join(ROOT, "kimchi/social.json")
    rows = {x["id"]: x for x in json.load(open(sp, encoding="utf-8"))} if os.path.exists(sp) else {}
    done = 0
    for p in pins:
        if ids and p["id"] not in ids: continue
        if lim is not None and done >= lim: break
        r = parse(p); vp = f"kimchi/tt/t{r['id']:03d}.mp4"
        if not os.path.exists(os.path.join(ROOT, vp)) or ids:
            video(r, os.path.join(ROOT, vp))
        xt, xl, tt, title = captions(r)
        rows[r["id"]] = dict(id=r["id"], x_text=xt, x_link=xl, x_image_url=r["pin_url"],
                             x_alt=f"Recipe card: {r['en']} ({r['ko']}) with ingredients", tt_caption=tt, tt_title=title,
                             tt_video_url=RAW + vp)
        done += 1; print(r["id"], r["en"], "|", r["hook"][:50])
    order = [p["id"] for p in pins if p["id"] in rows]
    json.dump([rows[i] for i in order], open(sp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
