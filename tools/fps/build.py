"""Build one Front Porch Stories episode: story txt -> voices -> pictures -> 1080p mp4 + thumbnail + meta.
usage: python3 tools/fps/build.py fps/episodes/ep01.txt out/fps_ep01 [--max-lines N]"""
import json, os, subprocess, sys, wave
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "mongki"))
import story as ST, voice as V, images as IM
import tts as MT
from common import fit_text, text_img, paste_center

W, H, FPS = 1920, 1080, 30
GAP, CHAPTER_GAP, END_HOLD = 0.55, 1.6, 12.0
MASTER = ("volume=-6dB,adeclip,adeclick=w=20:o=75:t=1,highpass=f=70,lowpass=f=10000,"
          "loudnorm=I=-16:TP=-2:LRA=11,aresample=48000")
MOVES = ["zin", "panl", "zout", "panr"]
SPLIT = float(os.environ.get("FPS_SPLIT", "15"))
GEN_ANGLES = os.environ.get("FPS_GEN_ANGLES", "0") == "1"   # extra generated camera angles (EP01 used this)
ANGLES = ["Same moment, tighter close-up on the faces and their emotions", "Same moment, wide establishing angle showing the whole room",
          "Same moment, over-the-shoulder angle", "Same moment, detail shot of hands and the important object",
          "Same moment, side angle with soft background blur"]

def cover(im, w, h):
    r = max(w / im.width, h / im.height)
    im = im.resize((int(im.width * r + 0.5), int(im.height * r + 0.5)), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))

def zoompan(move, n):
    d = max(n, 1)
    if move == "zin":  return f"z='1.0+0.10*on/{d}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
    if move == "zout": return f"z='1.10-0.10*on/{d}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
    if move == "panl": return f"z='1.10':x='(iw-iw/zoom)*on/{d}':y='ih/2-(ih/zoom/2)'"
    return f"z='1.10':x='(iw-iw/zoom)*(1-on/{d})':y='ih/2-(ih/zoom/2)'"

def render_clip(img_path, n, move, fade_in, fade_out, out):
    dur = n / FPS; vf = [f"scale=3840:2160:flags=lanczos,zoompan={zoompan(move, n)}:d={n}:s={W}x{H}:fps={FPS}"]
    if fade_in: vf.append("fade=t=in:st=0:d=0.6")
    if fade_out: vf.append(f"fade=t=out:st={max(0, dur - 0.6):.3f}:d=0.6")
    vf.append("format=yuv420p")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", img_path, "-frames:v", str(n), "-vf", ",".join(vf),
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-r", str(FPS), "-threads", "2", out], check=True)
    return out

def end_card(im):
    im = im.convert("RGBA"); ov = Image.new("RGBA", im.size, (0, 0, 0, 150)); im.alpha_composite(ov)
    paste_center(im, fit_text("Thank you for sitting with me.", "bold", 84, 1600, (255, 246, 227)), W / 2, H / 2 - 120)
    paste_center(im, fit_text("A NEW STORY EVERY WEEK", "heavy", 110, 1600, (246, 196, 107), 4), W / 2, H / 2 + 20)
    paste_center(im, fit_text("Subscribe and tell me your story in the comments.", "reg", 56, 1600, (255, 246, 227)), W / 2, H / 2 + 150)
    return im.convert("RGB")

def thumbnail(ep, refs, out):
    prompt = ep.get("thumb_prompt", "")
    rf = IM.refs_for(prompt, ep["cast"], refs)
    im = IM.generate(prompt, rf, tag="thumb") or Image.new("RGB", (1344, 768), (40, 30, 30))
    im = cover(im, 1280, 720).convert("RGBA")
    g = Image.new("L", (1280, 720), 0); d = ImageDraw.Draw(g)
    for x in range(1280):   # darken the right side where the words go
        d.line([(x, 0), (x, 720)], fill=int(max(0, (x - 520) / 760) * 200))
    im.alpha_composite(Image.merge("RGBA", (*[Image.new("L", (1280, 720), 0)] * 3, g)))
    top, bot = ep.get("thumb_top", ""), ep.get("thumb_bottom", "")
    paste_center(im, fit_text(top, "heavy", 150, 640, (255, 255, 255), 8), 935, 250)
    paste_center(im, fit_text(bot, "heavy", 170, 640, (255, 52, 52), 8), 935, 450)
    im.convert("RGB").save(out, quality=92)

def main():
    src, outdir = sys.argv[1], sys.argv[2]
    max_lines = int(sys.argv[sys.argv.index("--max-lines") + 1]) if "--max-lines" in sys.argv else None
    os.makedirs(outdir, exist_ok=True); os.makedirs(os.path.join(outdir, "shots"), exist_ok=True)
    ep = ST.parse(src); cast = ep["cast"]; print("[build]", ST.stats(ep), flush=True)

    # 1) lines with their shot and chapter
    lines, shots, chapters = [], [], []
    pend_chapter = None; pend_short = None
    for it in ep["items"]:
        if it["kind"] == "short": pend_short = it["title"]; continue
        if it["kind"] == "chapter": pend_chapter = it["name"]
        elif it["kind"] == "shot": shots.append({"prompt": it["prompt"], "lib": it.get("lib"), "first_line": None})
        else:
            txt = ST.spoken(it["text"])
            if not txt: continue
            ln = {"idx": len(lines), "who": it["who"], "text": txt, "shot": len(shots) - 1, "chapter": pend_chapter, "short": pend_short}
            pend_chapter = None; pend_short = None
            if shots and shots[-1]["first_line"] is None: shots[-1]["first_line"] = ln["idx"]
            lines.append(ln)
            if max_lines and len(lines) >= max_lines: break
    shots = [s for s in shots if s["first_line"] is not None]

    # 2) voice: chunks never cross a chapter start
    groups, cur = [], []
    for ln in lines:
        if ln["chapter"] and cur: groups.append(cur); cur = []
        cur.append(ln)
    if cur: groups.append(cur)
    chunks = []
    for gi, g in enumerate(groups):
        for c in V.chunk_lines(g, cast): c["chapter_start"] = (c["lines"][0]["chapter"] is not None); chunks.append(c)
    print(f"[build] {len(lines)} lines -> {len(chunks)} voice chunks", flush=True)
    t, audio_parts, qa = 0.0, [], []
    for ci, c in enumerate(chunks):
        if ci: t += CHAPTER_GAP if c["chapter_start"] else GAP
        wav = os.path.join(outdir, f"v{ci:03d}.wav"); d = V.synth_chunk(c, cast, ep.get("voice_style", ""), wav)
        a = V.read(wav); a = MT.fade(a); a, nsm = MT.desmack(a); a = MT.pause_gate(a)
        qa.append({"chunk": ci, "secs": round(d, 1), "smacks": nsm, **MT.analyze(a)})
        tot = sum(len(l["text"]) for l in c["lines"]) or 1; off = 0.0
        for l in c["lines"]:
            l["t"] = t + d * off / tot; off += len(l["text"])
        audio_parts.append((t, a)); c["t0"] = t; c["dur"] = d; t += d
    speech_end = t; total = speech_end + END_HOLD
    print(f"[build] speech {speech_end/60:.1f} min", flush=True)

    # 3) pictures: library pictures cost nothing; [SHOT] lines are generated (one image each)
    refs = IM.portraits(cast)
    prev = None; libdir = os.path.join(HERE, "..", "..", "fps", "library", "img"); new_images = 0
    for si, s in enumerate(shots):
        s["imgs"] = []
        if s["lib"]:
            for j, lid in enumerate(s["lib"]):
                src_p = os.path.join(libdir, lid + ".jpg")
                if not os.path.exists(src_p): print("[build] missing library picture", lid); continue
                pth = os.path.join(outdir, "shots", f"s{si:03d}_{j}.png"); cover(Image.open(src_p).convert("RGB"), W, H).save(pth)
                s["imgs"].append(pth)
            if s["imgs"]: prev = Image.open(s["imgs"][-1]); continue
            s["prompt"] = s["prompt"] or "A quiet lakeside house at dusk"
        im = IM.generate(s["prompt"], IM.refs_for(s["prompt"], cast, refs), tag=f"s{si:03d}"); new_images += 1
        if im is None: im = prev
        if im is None: im = IM._placeholder(s["prompt"], "16:9")
        prev = im; pth = os.path.join(outdir, "shots", f"s{si:03d}.png"); cover(im, W, H).save(pth); s["imgs"].append(pth)
    print(f"[build] new generated images: {new_images}", flush=True)
    endimg = os.path.join(outdir, "shots", "end.png"); end_card(Image.open(shots[-1]["imgs"][-1])).save(endimg)

    # 4) timeline -> frames (cumulative rounding keeps video length exact). Long shots get extra camera
    #    angles of the same moment so the picture changes every ~SPLIT seconds.
    starts = [0.0] + [lines[s["first_line"]]["t"] - 0.15 for s in shots[1:]] + [speech_end + 1.0]
    clips = []; mv = 0
    for si, s in enumerate(shots):
        a, b = starts[si], starts[si + 1]
        need = max(1, int(round((b - a) / SPLIT)))
        imgs = list(s["imgs"])
        if GEN_ANGLES and not s["lib"]:
            for j in range(1, need):
                im = IM.generate(f"{s['prompt']}. {ANGLES[(si + j) % len(ANGLES)]}", IM.refs_for(s["prompt"], cast, refs), tag=f"s{si:03d}_{j}")
                if im is not None:
                    pth = os.path.join(outdir, "shots", f"s{si:03d}_a{j}.png"); cover(im, W, H).save(pth); imgs.append(pth)
        k = len(imgs)
        for j, img in enumerate(imgs):
            clips.append({"img": img, "a": a + (b - a) * j / k, "b": a + (b - a) * (j + 1) / k, "move": MOVES[mv % 4],
                          "fade_in": j == 0 and (si == 0 or lines[s["first_line"]]["chapter"] is not None),
                          "fade_out": j == k - 1 and si + 1 < len(shots) and lines[shots[si + 1]["first_line"]]["chapter"] is not None})
            mv += 1
    clips[-1]["fade_out"] = True
    clips.append({"img": endimg, "a": starts[-1], "b": total, "move": "zin", "fade_in": True, "fade_out": True})
    jobs = []
    for k, c in enumerate(clips):
        n = int(round(c["b"] * FPS)) - int(round(c["a"] * FPS))
        jobs.append((c["img"], max(n, 1), c["move"], c["fade_in"], c["fade_out"], os.path.join(outdir, f"c{k:03d}.mp4")))
    with ThreadPoolExecutor(int(os.environ.get("FPS_JOBS", "2"))) as ex:
        files = list(ex.map(lambda j: render_clip(*j), jobs))
    with open(os.path.join(outdir, "list.txt"), "w") as f:
        for x in files: f.write(f"file '{os.path.basename(x)}'\n")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", os.path.join(outdir, "list.txt"),
                    "-c", "copy", os.path.join(outdir, "silent.mp4")], check=True)

    # contact sheet of every picture for quick review (saved to fps/results by the workflow)
    th = [Image.open(c["img"]).resize((320, 180)) for c in clips]
    cols = 8; sheet = Image.new("RGB", (cols * 320, ((len(th) + cols - 1) // cols) * 180), (0, 0, 0))
    for k, t_ in enumerate(th): sheet.paste(t_, ((k % cols) * 320, (k // cols) * 180))
    sheet.save(os.path.join(outdir, "contact.jpg"), quality=80)

    # 5) audio mix + master + mux
    buf = np.zeros(int(total * V.RATE) + V.RATE, np.float32)
    for t0, a in audio_parts:
        i = int(t0 * V.RATE); buf[i:i + len(a)] += a[: max(0, len(buf) - i)]
    buf = buf[: int(total * V.RATE)]
    raw = os.path.join(outdir, "voice.wav"); clean = os.path.join(outdir, "voice_clean.wav")
    with wave.open(raw, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(V.RATE); w.writeframes(np.clip(buf, -32767, 32767).astype(np.int16).tobytes())
    post = MT.master(raw, clean, MASTER)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", os.path.join(outdir, "silent.mp4"), "-i", clean, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", os.path.join(outdir, "video.mp4")], check=True)
    dec = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(outdir, "video.mp4"), "-vn", "-f", "s16le", "-ac", "1", "-ar", "24000", "-"],
                         capture_output=True).stdout
    x = np.frombuffer(dec, np.int16)
    json.dump({"chunks": qa, "post_master_ticks_removed": post, "final_decoded": MT.analyze(x),
               "final_isolated_ticks": MT.desmack(x)[1], "final_peak": int(np.abs(x).max()) if len(x) else 0},
              open(os.path.join(outdir, "audio_qa.json"), "w"), indent=1)

    # 6) captions transcript, description, thumbnail, meta
    open(os.path.join(outdir, "transcript.txt"), "w").write("\n".join(l["text"] for l in lines) + "\n")
    def mmss(s): return f"{int(s // 60)}:{int(s % 60):02d}"
    chap = [(0.0 if not k else l["t"], l["chapter"]) for k, l in enumerate([l for l in lines if l["chapter"]])]
    desc = ep["description"].replace("{chapters}", "\n".join(f"{mmss(a)} {n}" for a, n in chap))
    thumbnail(ep, refs, os.path.join(outdir, "thumb.jpg"))
    meta = {"title": ep["title"], "description": desc, "tags": ep["tags"], "duration": round(total, 1),
            "stats": ST.stats(ep), "shots": len(shots), "voice_chunks": len(chunks)}
    json.dump(meta, open(os.path.join(outdir, "meta.json"), "w"), indent=1)
    # timeline for the Shorts maker (voice_clean.wav and shots/ stay in outdir)
    json.dump({"lines": [{k: l.get(k) for k in ("idx", "who", "text", "t", "chapter", "short")} for l in lines],
               "line_end": [c["t0"] + c["dur"] for c in chunks for _ in c["lines"]],
               "clips": [{"img": c["img"], "a": c["a"], "b": c["b"]} for c in clips], "speech_end": speech_end,
               "title": ep["title"], "tags": ep["tags"]},
              open(os.path.join(outdir, "timeline.json"), "w"), indent=1)
    for f in files + [os.path.join(outdir, "silent.mp4")] + [os.path.join(outdir, f"v{i:03d}.wav") for i in range(len(chunks))]:
        if os.path.exists(f): os.remove(f)
    print("[build] done", round(total / 60, 1), "min", flush=True)

if __name__ == "__main__":
    main()
