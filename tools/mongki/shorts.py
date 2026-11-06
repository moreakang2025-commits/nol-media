"""Build the vertical Shorts for an episode (1080x1920, <= 58 s, burned-in captions).
Each short in ep["shorts"] = {"key", "title", "hook", "segments": [{"vo", "scene"}]}; scenes are the normal
16:9 scenes, placed in a vertical frame with a big hook line on top and big captions below.
usage: python3 tools/mongki/shorts.py mongki/episodes/ep02.json out/ep02 [--max-seg N]"""
import json, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
from common import W, H, FPS, BG, FG, DIM, YEL, text_img, fit_text, paste_center, mascot
import data as D, tts, scenes as S, build as B

VW, VH = 1080, 1920
SC_W = VW; SC_H = int(H * VW / W)          # 1080 x 607 scene window
SC_Y = 520                                  # scene window top
CAP_Y = SC_Y + SC_H + 170                   # caption centre
MAX_LEN = 58.0
PAD = 0.25

def frame(scene_im, hook, cap, frac, t):
    im = Image.new("RGBA", (VW, VH), BG + (255,)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, VW, 14], fill=(30, 36, 52)); d.rectangle([0, 0, int(VW * frac), 14], fill=YEL)
    hw = hook.split(); mid = (len(hw) + 1) // 2
    hl = [" ".join(hw[:mid]), " ".join(hw[mid:])] if len(hook) > 18 else [hook]
    for j, ln in enumerate(hl):
        paste_center(im, fit_text(ln, "heavy", 150, VW - 70, YEL, 9), VW / 2, 250 + j * 165 - (len(hl) - 1) * 40)
    sc = scene_im.convert("RGB").resize((SC_W, SC_H), Image.BILINEAR)
    im.paste(sc, (0, SC_Y))
    if cap:
        words = cap.split(); lines = [" ".join(words[i:i + 3]) for i in range(0, len(words), 3)][:2]
        for j, ln in enumerate(lines):
            paste_center(im, fit_text(ln.upper(), "heavy", 96, VW - 90, FG, 9), VW / 2, CAP_Y + j * 120)
    paste_center(im, text_img("FULL VIDEO ON THE CHANNEL", "bold", 40, DIM), VW / 2, VH - 150)
    return im.convert("RGB")

def caps3(text, dur):
    """Short punchy caption chunks (3 words) timed by character share."""
    words = text.split(); out = [" ".join(words[i:i + 3]) for i in range(0, len(words), 3)]
    tot = sum(len(c) for c in out) or 1; t = 0.0; res = []
    for c in out:
        dd = dur * len(c) / tot; res.append((t, t + dd, c)); t += dd
    return res

def build_short(ep, sh, ctx, outdir, max_seg=None):
    os.makedirs(outdir, exist_ok=True)
    segs = sh["segments"][:max_seg] if max_seg else sh["segments"]
    plan, qa = [], []
    for i, seg in enumerate(segs):
        vo = D.fill(seg.get("vo", ""), ctx); spec = D.fill_obj(seg["scene"], ctx)
        wav = os.path.join(outdir, f"s{i:02d}.wav")
        vd, rep = tts.synth_clean(vo, wav); qa.append({"seg": i, **rep})
        dur = spec.get("dur") or (vd + PAD)
        plan.append((vo, spec, wav, vd, round(dur * FPS) / FPS))
    total = sum(p[4] for p in plan)
    if total > MAX_LEN: print(f"[shorts] WARNING {sh['key']} is {total:.1f}s (> {MAX_LEN}s)")
    hook = D.fill(sh.get("hook", sh["title"]), ctx)
    silent = os.path.join(outdir, "silent.mp4")
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{VW}x{VH}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                          "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
    audio, t0, srt = [], 0.0, []
    for vo, spec, wav, vd, dur in plan:
        fn = S.SCENES[spec["type"]]; caps = caps3(vo, vd) if vo else []
        for f in range(int(round(dur * FPS))):
            t = f / FPS
            k = next((j for j, (a, b, c) in enumerate(caps) if a <= t < b), None)
            im = fn(t, dur, spec, ctx)
            if k is not None and spec["type"] not in ("logo", "end", "smash"): im = S.punch(im, k)
            p.stdin.write(frame(im, hook, caps[k][2] if k is not None else "", (t0 + t) / total, t).tobytes())
        x = tts.fade(tts._read(wav)) if vd > 0 else np.zeros(0, np.float32)
        clip = np.zeros(int(round(dur * tts.RATE)), np.float32); clip[:min(len(x), len(clip))] = x[:len(clip)]
        audio.append(clip)
        for a, b, c in caps: srt.append((t0 + a, t0 + b, c))
        t0 += dur
    p.stdin.close()
    if p.wait() != 0: raise SystemExit("short render failed")
    raw = os.path.join(outdir, "voice.wav"); clean = os.path.join(outdir, "voice_clean.wav")
    with wave.open(raw, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(tts.RATE)
        w.writeframes(np.clip(np.concatenate(audio), -32767, 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af", B.MASTER,
                    "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le", clean], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", clean, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-shortest",
                    os.path.join(outdir, "video.mp4")], check=True)
    dec = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(outdir, "video.mp4"), "-vn", "-f", "s16le", "-ac", "1",
                          "-ar", "24000", "-"], capture_output=True).stdout
    fin = tts.analyze(np.frombuffer(dec, np.int16))
    json.dump({"segments": qa, "final_decoded": fin}, open(os.path.join(outdir, "audio_qa.json"), "w"), indent=1)
    with open(os.path.join(outdir, "captions.srt"), "w") as f:
        for k, (a, b, c) in enumerate(srt, 1): f.write(f"{k}\n{B.srt_time(a)} --> {B.srt_time(b)}\n{c}\n\n")
    title = D.fill(sh["title"], ctx)
    if "#shorts" not in title.lower(): title = (title[:90] + " #Shorts")
    desc = "\n".join([D.fill(sh.get("description", hook), ctx), "",
                      "Full breakdown on the channel: " + ep["title"], "",
                      "Not financial advice. For education only.", "", "#Shorts #MongkiMoney"])
    meta = {"title": title, "description": desc, "tags": ep.get("tags", []) + ["shorts"], "duration": round(t0, 1),
            "short": True, "key": sh["key"]}
    json.dump(meta, open(os.path.join(outdir, "meta.json"), "w"), indent=1)
    for x in (silent, raw, clean) + tuple(os.path.join(outdir, f"s{i:02d}.wav") for i in range(len(plan))):
        if os.path.exists(x): os.remove(x)
    print(f"[shorts] {sh['key']} done {t0:.1f}s audio={fin}")

def main():
    ep_path, outdir = sys.argv[1], sys.argv[2]
    max_seg = int(sys.argv[sys.argv.index("--max-seg") + 1]) if "--max-seg" in sys.argv else None
    ep = json.load(open(ep_path)); ctx = D.compute(ep)
    for sh in ep.get("shorts", []):
        build_short(ep, sh, ctx, os.path.join(outdir, "shorts", sh["key"]), max_seg)

if __name__ == "__main__":
    main()
