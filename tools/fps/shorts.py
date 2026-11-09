"""Cut up to N vertical Shorts (1080x1920) out of a built Front Porch Stories episode.
Uses the episode's own voice and pictures, so Shorts cost nothing extra.
Each Short starts at a [SHORT] marker in the script (or at chapter starts if there are none),
runs up to ~58 s, has the hook title on top, burned captions, and a 'full story' end card.
usage: python3 tools/fps/shorts.py out/fps_ep02 [N]"""
import json, os, re, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "mongki"))
from common import fit_text, paste_center

W, H, FPS = 1080, 1920, 30
MAX, END = 57.0, 2.5
CREAM, GOLD, YEL = (255, 246, 227), (246, 196, 107), (250, 214, 60)

def wrap(text, n):
    words, out, cur = text.split(), [], []
    for w in words:
        cur.append(w)
        if len(" ".join(cur)) >= n: out.append(" ".join(cur)); cur = []
    if cur: out.append(" ".join(cur))
    return out

def caption_chunks(lines, a):
    """[(start, end, text)] relative to the Short, <= 5 words each, timed by character share."""
    out = []
    for l in lines:
        ws = l["text"].split(); parts = [" ".join(ws[i:i + 5]) for i in range(0, len(ws), 5)]
        tot = sum(len(p) for p in parts) or 1; t = l["t"]
        for p in parts:
            d = (l["end"] - l["t"]) * len(p) / tot; out.append((t - a, t - a + d, p)); t += d
    return out

_comp = {}
def composite(img):
    if img in _comp: return _comp[img]
    src = Image.open(img).convert("RGB")
    r = max(W / src.width, H / src.height); bg = src.resize((int(src.width * r) + 1, int(src.height * r) + 1))
    bg = bg.crop(((bg.width - W) // 2, (bg.height - H) // 2, (bg.width - W) // 2 + W, (bg.height - H) // 2 + H))
    bg = ImageEnhance.Brightness(bg.filter(ImageFilter.GaussianBlur(28))).enhance(0.45)
    fg = src.resize((W, int(src.height * W / src.width)), Image.LANCZOS)
    _comp[img] = (bg.convert("RGBA"), fg); return _comp[img]

def frame(img, k, title_imgs, cap):
    bg, fg = composite(img)
    im = bg.copy()
    z = 1.0 + 0.06 * k          # slow push-in over each picture
    fz = fg.resize((int(fg.width * z), int(fg.height * z)), Image.BILINEAR)
    fz = fz.crop(((fz.width - W) // 2, (fz.height - fg.height) // 2, (fz.width - W) // 2 + W, (fz.height - fg.height) // 2 + fg.height))
    im.paste(fz, (0, 640))
    y = 260
    for t in title_imgs: paste_center(im, t, W / 2, y); y += t.height + 14
    if cap: paste_center(im, cap, W / 2, 1460)
    return im

def end_card(img, title):
    bg, _ = composite(img); im = bg.copy()
    paste_center(im, fit_text("WANT TO KNOW", "heavy", 120, 960, CREAM, 6), W / 2, 760)
    paste_center(im, fit_text("WHAT HAPPENED NEXT?", "heavy", 120, 960, GOLD, 6), W / 2, 900)
    paste_center(im, fit_text("Full story on our channel", "bold", 64, 960, CREAM), W / 2, 1080)
    paste_center(im, fit_text("Front Porch Stories", "bold", 56, 960, GOLD), W / 2, 1180)
    return im

def make(outdir, n=4):
    tl = json.load(open(os.path.join(outdir, "timeline.json"))); L = tl["lines"]
    for i, l in enumerate(L):
        nxt = L[i + 1]["t"] if i + 1 < len(L) else tl["speech_end"]
        l["end"] = min(nxt, tl["line_end"][i]) if tl.get("line_end") else nxt
    starts = [(i, l["short"]) for i, l in enumerate(L) if l.get("short")]
    if not starts:
        starts = [(i, l["chapter"]) for i, l in enumerate(L) if l.get("chapter")][::2]
    made = []
    for k, (i0, title) in enumerate(starts[:n], 1):
        seg = [L[i0]]
        for l in L[i0 + 1:]:
            if l["end"] - L[i0]["t"] > MAX: break
            seg.append(l)
        a = max(0.0, L[i0]["t"] - 0.1); b = seg[-1]["end"] + 0.5; dur = b - a; total = dur + END
        d = os.path.join(outdir, "shorts", f"s{k}"); os.makedirs(d, exist_ok=True)
        caps = caption_chunks(seg, a)
        title_imgs = [fit_text(t.upper(), "heavy", 96, 980, (255, 255, 255), 7) for t in wrap(title, 18)[:3]]
        cap_cache = {}
        vid = os.path.join(d, "video.mp4")
        p = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                              "-ss", f"{a:.3f}", "-t", f"{dur:.3f}", "-i", os.path.join(outdir, "voice_clean.wav"),
                              "-filter_complex", f"[1:a]afade=t=out:st={max(0, dur - 0.4):.3f}:d=0.4,apad[a]", "-map", "0:v", "-map", "[a]",
                              "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p",
                              "-c:a", "aac", "-b:a", "160k", vid], stdin=subprocess.PIPE)
        last_img = None
        for f in range(int(total * FPS)):
            tau = f / FPS; g = a + tau
            clip = next((c for c in tl["clips"] if c["a"] <= g < c["b"]), tl["clips"][-1])
            last_img = clip["img"] if tau < dur else last_img
            if tau >= dur:
                im = end_card(last_img, title)
            else:
                ci = next((j for j, (s0, e0, _) in enumerate(caps) if s0 <= tau < e0), None)
                cap = None
                if ci is not None:
                    if ci not in cap_cache: cap_cache[ci] = fit_text(caps[ci][2].upper(), "heavy", 92, 1000, YEL, 8)
                    cap = cap_cache[ci]
                pa, pb = max(clip["a"], a), min(clip["b"], b)
                im = frame(clip["img"], (g - pa) / max(pb - pa, 0.1), title_imgs, cap)
            p.stdin.write(im.convert("RGB").tobytes())
        p.stdin.close()
        if p.wait() != 0: raise SystemExit(f"short {k} render failed")
        meta = {"title": f"{title} #Shorts"[:100],
                "description": f"{title}\n\nWatch the full story: {{long}}\n\nFiction for entertainment. Narration and visuals made with the help of AI tools.\n\n#familydrama #storytime #shorts",
                "tags": tl["tags"][:8] + ["shorts"], "duration": round(total, 1)}
        json.dump(meta, open(os.path.join(d, "meta.json"), "w"), indent=1)
        print(f"[shorts] s{k}: {total:.1f}s '{title}'", flush=True); made.append(d)
    return made

if __name__ == "__main__":
    make(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 4)
