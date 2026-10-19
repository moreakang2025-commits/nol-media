#!/usr/bin/env python3
"""Daily Suyeong content builder.

1. Finds look pairs (lNN1 full-body + lNN2 half-body) in dami/scenes.json whose images exist
   in dami/img/ and are not yet in dami/used.json.
2. For each pair, builds a reel in the next trend format (rotation below), renders it,
   and writes it to dami/pending_posts.json for the scheduler (Claude + Buffer) to post.
3. Prints how many look scenes are still waiting for images, so the scheduler can add more.

Look scenes carry: {"id":"l401","kind":"look","look":{"title":"...","place":"...","items":["a + b","c + d"],"drink":["x","y"]},"scene":"..."}
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "dami"
FORMATS = ["diary", "fitcheck", "drink", "rate", "keepswap"]
AI = "\n\nAI character · AI-styled looks"


def load(p, default):
    return json.loads(p.read_text()) if p.exists() else default


def shots_and_caption(fmt, a, b, look, day):
    t, place = look["title"], look.get("place", "Seoul")
    i1, i2 = (look["items"] + ["", ""])[:2]
    S = lambda img, beats, text="", pos="bottom", zoom=(1.0, 1.08), pan=(0.5, 0.48, 0.5, 0.44): {
        "img": img, "beats": beats, "text": text, "pos": pos, "zoom": list(zoom), "pan": list(pan)}
    if fmt == "diary":
        return "lofi", [S(a, 4, f"Seoul outfit diary · day {day}", "top"), S(b, 4, i1, zoom=(1.02, 1.12)),
                        S(a, 4, i2, zoom=(1.3, 1.45), pan=(0.5, 0.62, 0.5, 0.66)), S(b, 4, "would you wear this?", "top", (1.12, 1.0))], \
            f"Seoul outfit diary · day {day} 🤍 {t.lower()}, {place}.\n\nwould you wear it? yes or no 👇 (follow for day {day + 1})" + AI + "\n#seoulstyle #ootd #koreanfashion #outfitdiary"
    if fmt == "fitcheck":
        return "moody", [S(a, 4, f"fit check · {place}", "top"), S(b, 4, i1, zoom=(1.0, 1.12)),
                         S(a, 4, i2, zoom=(1.35, 1.5), pan=(0.5, 0.7, 0.5, 0.75)), S(b, 4, "rate it 1-10", "top", (1.15, 1.0))], \
            f"fit check in {place} 🌙 {i1}, {i2}.\n\nrate it 1-10, be honest 👇" + AI + "\n#fitcheck #seoul #koreanfashion #ootd"
    if fmt == "drink":
        d1, d2 = (look.get("drink") or ["iced americano", "strawberry latte"])[:2]
        return "lofi", [S(a, 4, "pairing my outfit with a drink", "top"), S(b, 4, i1, zoom=(1.02, 1.12)),
                        S(a, 4, f"{d1} or {d2}?", "top", (1.3, 1.42), (0.5, 0.35, 0.5, 0.32)), S(b, 4, "comment your pick", "top", (1.12, 1.0))], \
            f"{t} in {place} ☕ {i1}, {i2}.\n\nwhich drink goes with this fit, {d1} or {d2}? 👇" + AI + "\n#koreanfashion #seoulstyle #ootd #cafeoutfit"
    if fmt == "rate":
        return "disco", [S(a, 2, f"{t.lower()} in Seoul", "top"), S(b, 2, zoom=(1.05, 1.15)), S(a, 2, i1, zoom=(1.2, 1.3)),
                         S(b, 2, i2, zoom=(1.1, 1.2)), S(a, 4, "1-10? comment below", "top", (1.1, 1.0))], \
            f"{t.lower()} 💫 {i1}, {i2}. {place}.\n\nscore it 1-10 👇" + AI + "\n#koreanfashion #outfitideas #seoulstyle #kfashion"
    # keepswap
    return "disco", [S(a, 2, "keep or swap?", "top"), S(a, 2, i1, zoom=(1.15, 1.25)), S(b, 2, i2, zoom=(1.05, 1.15)),
                     S(b, 2, zoom=(1.2, 1.3)), S(a, 4, "keep or swap? 👇", "top", (1.1, 1.0))], \
        f"keep or swap? 🤔 {t.lower()}: {i1}, {i2}.\n\ntell me what you'd change 👇" + AI + "\n#koreanfashion #ootd #seoulstyle #outfitideas"


def main():
    scenes = json.loads((D / "scenes.json").read_text())
    used = load(D / "used.json", {"pairs": [], "fmt_i": 0, "diary_day": 1})
    reels = json.loads((D / "reels.json").read_text())
    pending = load(D / "pending_posts.json", [])
    by_id = {s["id"]: s for s in scenes}
    looks = sorted({s["id"][:-1] for s in scenes if s.get("kind") == "look" and s.get("look")})
    built = []
    for base in looks:
        a, b = base + "1", base + "2"
        if base in used["pairs"] or a not in by_id or b not in by_id:
            continue
        if not ((D / "img" / f"{a}.png").exists() and (D / "img" / f"{b}.png").exists()):
            continue
        fmt = FORMATS[used["fmt_i"] % len(FORMATS)]
        music, shots, caption = shots_and_caption(fmt, a, b, by_id[a]["look"], used["diary_day"])
        rid = f"r{base[1:]}"
        reels = [r for r in reels if r["id"] != rid] + [{"id": rid, "format": fmt, "music": music, "shots": shots, "caption": caption}]
        (D / "reels.json").write_text(json.dumps(reels, ensure_ascii=False, indent=2))
        subprocess.run([sys.executable, str(ROOT / "tools/dami/make_reel.py"), rid], check=True)
        pending.append({"reel": rid, "video": f"dami/reels/{rid}.mp4", "caption": caption, "format": fmt})
        used["pairs"].append(base)
        used["fmt_i"] += 1
        if fmt == "diary":
            used["diary_day"] += 1
        built.append(rid)
    (D / "used.json").write_text(json.dumps(used, indent=2))
    (D / "pending_posts.json").write_text(json.dumps(pending, ensure_ascii=False, indent=2))
    waiting = [s["id"] for s in scenes if not (D / "img" / f"{s['id']}.png").exists()]
    waiting_looks = [x for x in waiting if x.startswith("l")]
    print(json.dumps({"built": built, "pending_posts": len(pending), "look_scenes_waiting": len(waiting_looks),
                      "scenes_waiting": len(waiting)}))


if __name__ == "__main__":
    main()
