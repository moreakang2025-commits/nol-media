#!/usr/bin/env python3
"""Make a 9:16 Reel from Suyeong stills, modelled on 2026 trending outfit-reel formats:
beat-synced cuts, flash/zoom-punch transitions, vote badges (1/2/3), hook text in the
first second, and original music in three moods (no licensed tracks):
  disco  ~118 BPM four-on-the-floor (beat-drop transitions, try-ons)
  lofi   ~84 BPM soft chords (cozy diary / cafe)
  moody  ~76 BPM dark pad + slow kick (after-dark fit checks)

Usage: python3 tools/dami/make_reel.py r101   (reads dami/reels.json, writes dami/reels/r101.mp4)
Shot fields: img, beats (or dur seconds), text, pos (top|bottom), num (badge), zoom [a,b], pan [x0,y0,x1,y1]
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
W, H, FPS, SR = 720, 1280, 30, 44100
BOLD = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
if not Path(BOLD).exists():
    BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
MED = BOLD.replace("Bold", "Medium") if Path(BOLD.replace("Bold", "Medium")).exists() else BOLD
EMOJI_FREE = str.maketrans("", "")
BPM = {"disco": 118, "lofi": 84, "moody": 76}


# ---------------- picture ----------------
def cover(img, zoom, cx, cy):
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


def strip_emoji(s):
    return "".join(ch for ch in s if ord(ch) < 0x2190 or 0x3000 <= ord(ch) <= 0xD7AF)


def overlay(shot, t_in):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    text = strip_emoji(shot.get("text", "")).strip()
    if text:
        pop = min(1.0, t_in / 0.15)
        size = int((48 if shot.get("pos") == "top" else 46) * (0.85 + 0.15 * pop))
        f = ImageFont.truetype(BOLD, size)
        lines = wrap(d, text, f, W - 110)
        lh = int(size * 1.2)
        y = int(H * 0.13) if shot.get("pos") == "top" else int(H * 0.70)
        for L in lines:
            tw = d.textlength(L, font=f)
            d.text(((W - tw) / 2, y), L, font=f, fill="white", stroke_width=6, stroke_fill=(15, 15, 15))
            y += lh
    if shot.get("num"):
        r = 46
        cx, cy = W - 80, 150
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 255, 255, 235))
        nf = ImageFont.truetype(BOLD, 56)
        n = str(shot["num"])
        d.text((cx - d.textlength(n, font=nf) / 2, cy - 36), n, font=nf, fill=(20, 20, 20))
    small = ImageFont.truetype(MED, 21)
    label = "AI character"
    d.rounded_rectangle((24, 28, 24 + d.textlength(label, font=small) + 24, 64), radius=14, fill=(0, 0, 0, 110))
    d.text((36, 33), label, font=small, fill=(255, 255, 255, 230))
    return layer


# ---------------- music (original) ----------------
def env(n, a, d):
    t = np.arange(n) / SR
    return (1 - np.exp(-t * a)) * np.exp(-t * d)


def add(out, s, sig):
    e = min(len(out), s + len(sig))
    if s < len(out):
        out[s:e] += sig[: e - s]


def kick(n=0.35):
    t = np.arange(int(SR * n)) / SR
    f = 110 * np.exp(-t * 18) + 45
    return 0.9 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)


def noise_hit(n, decay, amp, rng, hp=True):
    x = rng.standard_normal(int(SR * n))
    if hp:
        x = np.diff(np.concatenate([[0], x]))
    return amp * x * np.exp(-np.arange(len(x)) / SR * decay)


def tone(freq, n, amp, a=200, d=3, harm=(1, 0.4, 0.15)):
    t = np.arange(int(SR * n)) / SR
    s = sum(h * np.sin(2 * np.pi * freq * (k + 1) * t) for k, h in enumerate(harm))
    return amp * s * env(len(t), a, d)


PROG = {  # A-minor-ish pop progressions (Hz roots + chord tones)
    "disco": [[220.0, 261.63, 329.63], [174.61, 220.0, 261.63], [196.0, 246.94, 293.66], [164.81, 207.65, 246.94]],
    "lofi": [[220.0, 261.63, 329.63, 392.0], [196.0, 246.94, 293.66, 349.23], [174.61, 220.0, 261.63, 329.63], [196.0, 246.94, 293.66, 392.0]],
    "moody": [[110.0, 164.81, 220.0, 261.63], [87.31, 130.81, 174.61, 220.0], [98.0, 146.83, 196.0, 246.94], [82.41, 123.47, 164.81, 207.65]],
}


def music(style, seconds, path, seed=11):
    rng = np.random.default_rng(seed)
    bpm = BPM[style]
    beat = 60 / bpm
    n = int(SR * (seconds + 0.5))
    out = np.zeros(n)
    nbeats = int(seconds / beat) + 2
    prog = PROG[style]
    for b in range(nbeats):
        s = int(b * beat * SR)
        bar, pos = divmod(b, 4)
        chord = prog[bar % 4]
        if style == "disco":
            add(out, s, kick())
            add(out, s + int(beat / 2 * SR), noise_hit(0.08, 60, 0.18, rng))          # offbeat open hat
            if pos in (1, 3):
                add(out, s, noise_hit(0.18, 22, 0.35, rng, hp=False))                  # clap
            add(out, s + int(beat / 2 * SR), tone(chord[0] / 2, beat / 2, 0.35, d=6, harm=(1, 0.2)))  # octave bass
            add(out, s, tone(chord[0] / 4, beat / 2, 0.3, d=8, harm=(1, 0.1)))
            if pos in (0, 2):
                for f in chord:
                    add(out, s + int(beat * 0.75 * SR), tone(f * 2, beat * 0.4, 0.06, d=7))  # chord stab
        elif style == "lofi":
            if pos in (0, 2):
                add(out, s, 0.6 * kick(0.3))
            if pos in (1, 3):
                add(out, s, noise_hit(0.15, 28, 0.18, rng, hp=False))
            for h in range(2):
                add(out, s + int(h * beat / 2 * SR), noise_hit(0.04, 90, 0.05, rng))
            if pos == 0:
                for f in chord:
                    add(out, s, tone(f, beat * 4, 0.05, a=8, d=0.4))                     # soft pad chord
                add(out, s, tone(chord[0] / 2, beat * 2, 0.22, a=60, d=1.2, harm=(1, 0.3)))
            add(out, s + int(beat / 2 * SR), tone(chord[(b * 2) % len(chord)] * 2, 0.3, 0.05, d=10))  # pluck
        else:  # moody
            if pos == 0 or (pos == 2 and bar % 2):
                add(out, s, 0.8 * kick(0.45))
            if pos == 2:
                add(out, s, noise_hit(0.1, 40, 0.12, rng))
            add(out, s + int(beat / 2 * SR), noise_hit(0.03, 120, 0.04, rng))
            if pos == 0:
                for f in chord:
                    add(out, s, tone(f, beat * 4.2, 0.07, a=3, d=0.25, harm=(1, 0.5, 0.25, 0.1)))
                add(out, s, tone(chord[0] / 2, beat * 3, 0.3, a=20, d=0.6, harm=(1, 0.2)))
    k = np.ones(40) / 40
    out = np.convolve(out, k, mode="same") * 0.35 + out * 0.65                          # soften highs
    out = out[: int(SR * seconds)]
    fade = int(0.35 * SR)
    out[:int(0.02 * SR)] *= np.linspace(0, 1, int(0.02 * SR))
    out[-fade:] *= np.linspace(1, 0, fade)
    out = np.tanh(out / (np.abs(out).max() + 1e-9) * 1.6)
    out = np.int16(out / np.abs(out).max() * 0.8 * 32767)
    with wave.open(str(path), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(out.tobytes())


# ---------------- render ----------------
def make(reel_id):
    reels = {r["id"]: r for r in json.loads((D / "reels.json").read_text())}
    r = reels[reel_id]
    style = r.get("music", "lofi")
    beat = 60 / BPM[style]
    for s in r["shots"]:
        s["_dur"] = s["beats"] * beat if "beats" in s else s["dur"]
    total = sum(s["_dur"] for s in r["shots"])
    out_dir = D / "reels"
    out_dir.mkdir(exist_ok=True)
    wav = out_dir / f"{reel_id}.wav"
    music(style, total, wav)
    out = out_dir / f"{reel_id}.mp4"
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", "-i", str(wav), "-c:v", "libx264", "-pix_fmt", "yuv420p",
         "-preset", "medium", "-crf", "20", "-c:a", "aac", "-b:a", "160k", "-shortest",
         "-movflags", "+faststart", str(out)], stdin=subprocess.PIPE)
    cache = {}
    punch = style == "disco"
    for idx, s in enumerate(r["shots"]):
        img = cache.setdefault(s["img"], Image.open(D / "img" / f"{s['img']}.png").convert("RGB"))
        z0, z1 = s.get("zoom", [1.0, 1.08])
        x0, y0, x1, y1 = s.get("pan", [0.5, 0.45, 0.5, 0.42])
        frames = max(1, round(s["_dur"] * FPS))
        for i in range(frames):
            p = i / max(frames - 1, 1)
            e = p * p * (3 - 2 * p)
            z = z0 + (z1 - z0) * e
            if punch and i < 4 and idx > 0:
                z *= 1.0 + 0.06 * (4 - i) / 4
            fr = cover(img, z, x0 + (x1 - x0) * e, y0 + (y1 - y0) * e).convert("RGBA")
            if idx > 0 and i < 3:
                a = int((0.55 if punch else 0.3) * 255 * (3 - i) / 3)
                fr = Image.alpha_composite(fr, Image.new("RGBA", (W, H), (255, 255, 255, a)))
            fr = Image.alpha_composite(fr, overlay(s, i / FPS)).convert("RGB")
            ff.stdin.write(fr.tobytes())
    ff.stdin.close()
    ff.wait()
    wav.unlink()
    print(out, f"{total:.1f}s", style)


if __name__ == "__main__":
    for rid in sys.argv[1:]:
        make(rid)
