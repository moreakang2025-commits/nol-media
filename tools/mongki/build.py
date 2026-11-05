"""Build one episode: data -> narration -> scenes -> mp4 + srt + thumbnail + meta.json.
usage: python3 tools/mongki/build.py mongki/episodes/ep01.json out/ep01 [--max-seg N]"""
import json, os, re, subprocess, sys, wave
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from common import W, H, FPS
import data as D, tts, scenes as S, thumb

PAD = 0.35
BURN = False  # long form: captions go to YouTube as a CC track, not burned in

def chunks(text, dur):
    """Split narration into short caption chunks timed by character share."""
    words = text.split(); out = []; cur = []
    for w in words:
        cur.append(w)
        if len(cur) >= 6 or re.search(r"[.?!,]$", w) and len(cur) >= 3:
            out.append(" ".join(cur)); cur = []
    if cur: out.append(" ".join(cur))
    total = sum(len(c) for c in out) or 1; t = 0.0; res = []
    for c in out:
        d = dur * len(c) / total; res.append((t, t + d, c)); t += d
    return res

def render_segment(i, seg, dur, ctx, outdir, voice_dur, t_start=0.0, total=1.0):
    fn = S.SCENES[seg["scene"]["type"]]
    caps = chunks(seg["vo_filled"], voice_dur) if seg["vo_filled"] else []
    tmp = os.path.join(outdir, f"seg{i:02d}.tmp.mp4"); final = os.path.join(outdir, f"seg{i:02d}.mp4")
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                          "-pix_fmt", "yuv420p", "-r", str(FPS), tmp], stdin=subprocess.PIPE)
    n = int(round(dur * FPS))
    for f in range(n):
        t = f / FPS
        im = fn(t, dur, seg["scene"], ctx)
        k = next((j for j, (a, b, c) in enumerate(caps) if a <= t < b), None)
        if k is not None and seg["scene"]["type"] not in ("logo", "end", "smash"): im = S.punch(im, k)
        if BURN and k is not None and seg["scene"]["type"] not in ("logo",): S.caption_overlay(im, caps[k][2])
        if seg["scene"]["type"] not in ("logo", "end"): S.progress(im, (t_start + t) / total)
        p.stdin.write(im.convert("RGB").tobytes())
    p.stdin.close()
    if p.wait() != 0: raise SystemExit(f"render failed at segment {i}")
    os.replace(tmp, final); return final, caps

def srt_time(s):
    h, r = divmod(s, 3600); m, r = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(r):02d},{int((r - int(r)) * 1000):03d}"

def main():
    ep_path, outdir = sys.argv[1], sys.argv[2]
    max_seg = int(sys.argv[sys.argv.index("--max-seg") + 1]) if "--max-seg" in sys.argv else None
    os.makedirs(outdir, exist_ok=True)
    ep = json.load(open(ep_path))
    global BURN; BURN = bool(ep.get("burn_captions", False))
    ctx = D.compute(ep)
    json.dump({k: v for k, v in ctx.items() if not k.startswith("_") or k in ("_elections", "_event_moves")},
              open(os.path.join(outdir, "data.json"), "w"), indent=1, default=str)
    segs = ep["segments"][:max_seg] if max_seg else ep["segments"]
    files, srt, chapters, audio = [], [], [], []
    plan = []; qa = []
    for i, seg in enumerate(segs):
        seg["vo_filled"] = D.fill(seg.get("vo", ""), ctx)
        seg["scene"] = D.fill_obj(seg["scene"], ctx)
        if "{" in seg["vo_filled"]: print(f"[warn] unfilled placeholder in segment {i}: {seg['vo_filled']}")
        wav = os.path.join(outdir, f"seg{i:02d}.wav")
        vd, ck = tts.synth_clean(seg["vo_filled"], wav)
        qa.append({"seg": i, "clicks_after_retakes": ck})
        dur = seg["scene"].get("dur") or (vd + PAD + seg["scene"].get("tail", 0.0))
        plan.append((seg, wav, vd, round(dur * FPS) / FPS))
    total = sum(p[3] for p in plan); t0 = 0.0
    for i, (seg, wav, vd, dur) in enumerate(plan):
        f, caps = render_segment(i, seg, dur, ctx, outdir, vd, t0, total)
        files.append(f)
        with wave.open(wav) as w: pcm = tts.fade(np.frombuffer(w.readframes(w.getnframes()), np.int16))
        clip = np.zeros(int(round(dur * tts.RATE)), np.float32); clip[:min(len(pcm), len(clip))] = pcm[:len(clip)]
        audio.append(clip)
        for a, b, c in caps: srt.append((t0 + a, t0 + b, c))
        if seg.get("chapter"): chapters.append((t0, seg["chapter"]))
        print(f"[build] seg {i} {seg['scene']['type']} {dur:.1f}s", flush=True)
        t0 += dur
    with wave.open(os.path.join(outdir, "voice.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(tts.RATE); w.writeframes(np.clip(np.concatenate(audio), -32767, 32767).astype(np.int16).tobytes())
    with open(os.path.join(outdir, "list.txt"), "w") as f:
        for x in files: f.write(f"file '{os.path.basename(x)}'\n")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", os.path.join(outdir, "list.txt"),
                    "-c", "copy", os.path.join(outdir, "silent.mp4")], check=True)
    raw = os.path.join(outdir, "voice.wav"); clean = os.path.join(outdir, "voice_clean.wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af",
                    "highpass=f=60,adeclick=w=55:o=75:t=2,adeclip,lowpass=f=13000,alimiter=limit=0.9:level=false",
                    "-ar", str(tts.RATE), "-ac", "1", "-c:a", "pcm_s16le", clean], check=True)
    left = tts.clicks(clean)
    json.dump({"segments": qa, "final_clicks_left": left, "before_master": tts.clicks(raw)},
              open(os.path.join(outdir, "audio_qa.json"), "w"), indent=1)
    print("[audio] clicks left after master:", left[:20])
    os.replace(clean, raw)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(outdir, "silent.mp4"), "-i", os.path.join(outdir, "voice.wav"),
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-shortest",
                    os.path.join(outdir, "video.mp4")], check=True)
    with open(os.path.join(outdir, "transcript.txt"), "w") as f:
        f.write("\n".join(p[0]["vo_filled"] for p in plan if p[0]["vo_filled"]) + "\n")
    with open(os.path.join(outdir, "captions.srt"), "w") as f:
        for k, (a, b, c) in enumerate(srt, 1): f.write(f"{k}\n{srt_time(a)} --> {srt_time(b)}\n{c}\n\n")
    def mmss(s): return f"{int(s // 60)}:{int(s % 60):02d}"
    chap = "\n".join(f"{mmss(a)} {name}" for a, name in ([(0.0, chapters[0][1])] + chapters[1:] if chapters else []))
    desc = "\n".join(ep["description"]).replace("{chapters}", chap)
    meta = {"title": ep["title"], "description": desc, "tags": ep.get("tags", []), "duration": round(t0, 1),
            "prices_asof": ctx.get("prices_asof")}
    json.dump(meta, open(os.path.join(outdir, "meta.json"), "w"), indent=1)
    thumb.make(ep, os.path.join(outdir, "thumb.jpg"))
    for x in files + [os.path.join(outdir, "silent.mp4")]:
        os.remove(x)
    print("[build] done", round(t0, 1), "s")

if __name__ == "__main__":
    main()
