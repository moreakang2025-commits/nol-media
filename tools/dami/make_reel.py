#!/usr/bin/env python3
"""Make a 9:16 Reel from Dami stills: slow zoom/pan per shot, TikTok-style captions,
a small 'AI character' label, and an original soft lo-fi loop (no licensed music).

Usage: python3 tools/dami/make_reel.py r001        (reads dami/reels.json, writes dami/reels/r001.mp4)
"""
import json
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "dami"
W, H, FPS = 720, 1280, 30
BOLD = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
if not Path(BOLD).exists():
    BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
REG = BOLD.replace("Bold", "Medium") if Path(BOLD.replace("Bold", "Medium")).exists() else BOLD


def cover(img, zoom, cx, cy):
    """Crop a 9:16 window of the image at the given zoom, centred on (cx, cy) in 0..1."""
    iw, ih = img.size
    base = min(iw / W, ih / H)
    cw, ch = W * base / zoom, H * base / zoom
    x0 = min(max(cx * iw - cw / 2, 0), iw - cw)
    y0 = min(max(cy * ih - ch / 2, 0), ih - ch)
    return img.resize((W, H), Image.LANCZOS, box=(x0, y0, x0 + cw, y0 + ch))


def wrap(d, text, font, maxw):
    out, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) > maxw and cur:
            out.append(cur)
            cur = w
        else:
            cur = t
    return out + ([cur] if cur else [])


def overlay(text, t_in):
    """Caption layer (RGBA) with a quick pop-in during the first 0.2 s."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    size = 52 if t_in > 0.2 else int(40 + 60 * t_in)
    f = ImageFont.truetype(BOLD, size)
    lines = wrap(d, text, f, W - 120)
    y = int(H * 0.66)
    for L in lines:
        tw = d.textlength(L, font=f)
        d.text(((W - tw) / 2, y), L, font=f, fill="white", stroke_width=6, stroke_fill=(20, 20, 20))
        y += int(size * 1.22)
    small = ImageFont.truetype(REG, 22)
    d.rounded_rectangle((24, 28, 24 + d.textlength("AI character", font=small) + 24, 66),
                        radius=14, fill=(0, 0, 0, 110))
    d.text((36, 34), "AI character", font=small, fill=(255, 255, 255, 230))
    return layer


def music(seconds, path, seed=7):
    """Original gentle lo-fi loop: soft chords + muted pluck + light hat."""
    sr = 44100
    n = int(sr * seconds)
    t = np.arange(n) / sr
    bpm = 84
    beat = 60 / bpm
    chords = [[220.0, 261.63, 329.63], [196.0, 246.94, 293.66],
              [174.61, 220.0, 261.63], [196.0, 246.94, 329.63]]
    out = np.zeros(n)
    rng = np.random.default_rng(seed)
    bar = beat * 4
    for i in range(int(seconds / bar) + 1):
        s = int(i * bar * sr)
        e = min(n, int((i + 1) * bar * sr))
        if s >= n:
            break
        tt = t[s:e] - t[s]
        for f in chords[i % 4]:
            out[s:e] += 0.05 * np.sin(2 * np.pi * f * tt) * (1 - np.exp(-tt * 6)) * np.exp(-tt * 0.35)
    for k in range(int(seconds / (beat / 2))):
        s = int(k * beat / 2 * sr)
        e = min(n, s + int(0.25 * sr))
        if s >= n:
            break
        tt = t[s:e] - t[s]
        if k % 2 == 0:
            f = chords[(k // 8) % 4][k % 3] * 2
            out[s:e] += 0.06 * np.sin(2 * np.pi * f * tt) * np.exp(-tt * 12)
        out[s:e] += 0.012 * rng.standard_normal(e - s) * np.exp(-(t[s:e] - t[s]) * 60)
    fade = int(0.4 * sr)
    out[:fade] *= np.linspace(0, 1, fade)
    out[-fade:] *= np.linspace(1, 0, fade)
    out = np.int16(np.clip(out / (np.abs(out).max() + 1e-9) * 0.6, -1, 1) * 32767)
    with wave.open(str(path), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(out.tobytes())


def make(reel_id):
    reels = {r["id"]: r for r in json.loads((D / "reels.json").read_text())}
    r = reels[reel_id]
    out_dir = D / "reels"
    out_dir.mkdir(exist_ok=True)
    tmp_wav = out_dir / f"{reel_id}.wav"
    total = sum(s["dur"] for s in r["shots"])
    music(total, tmp_wav)
    out = out_dir / f"{reel_id}.mp4"
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", str(tmp_wav),
         "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "20",
         "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", str(out)],
        stdin=subprocess.PIPE)
    cache = {}
    for s in r["shots"]:
        img = cache.setdefault(s["img"], Image.open(D / "img" / f"{s['img']}.png").convert("RGB"))
        z0, z1 = s.get("zoom", [1.0, 1.12])
        cx0, cy0, cx1, cy1 = s.get("pan", [0.5, 0.45, 0.5, 0.42])
        frames = int(s["dur"] * FPS)
        for i in range(frames):
            p = i / max(frames - 1, 1)
            e = p * p * (3 - 2 * p)
            fr = cover(img, z0 + (z1 - z0) * e, cx0 + (cx1 - cx0) * e, cy0 + (cy1 - cy0) * e)
            fr = Image.alpha_composite(fr.convert("RGBA"), overlay(s["text"], i / FPS)).convert("RGB")
            ff.stdin.write(fr.tobytes())
    ff.stdin.close()
    ff.wait()
    tmp_wav.unlink()
    print(out)


if __name__ == "__main__":
    make(sys.argv[1])
