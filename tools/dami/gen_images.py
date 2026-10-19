#!/usr/bin/env python3
"""Generate Dami images with the Gemini API.

Run by GitHub Actions (.github/workflows/dami-images.yml).
- No reference yet -> makes 4 reference candidates in dami/ref/ and stops.
  The first candidate becomes dami/ref/dami_ref.png (swap it later if another one is better).
- Reference exists -> makes the next N scenes from dami/scenes.json into dami/img/,
  always attaching the reference so Dami keeps the same face.
State lives in dami/state.json ({"next": index}).

Env: GEMINI_API_KEY (required), DAMI_PER_RUN (default 3), GEMINI_IMAGE_MODELS (optional, comma list).
"""
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "dami"
REF_DIR = D / "ref"
IMG_DIR = D / "img"
REF = REF_DIR / "dami_ref.png"
STATE = D / "state.json"

DEFAULT_MODELS = [
    "gemini-nano-banana-2.1",
    "gemini-3.1-flash-lite-image",
    "gemini-3.1-flash-image",
    "gemini-2.5-flash-image",
]
API = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def models():
    env = os.environ.get("GEMINI_IMAGE_MODELS", "").strip()
    return [m.strip() for m in env.split(",") if m.strip()] or DEFAULT_MODELS


def call(prompt, ref_png=None):
    key = os.environ["GEMINI_API_KEY"]
    parts = [{"text": prompt}]
    if ref_png is not None:
        parts.append({"inline_data": {"mime_type": "image/png",
                                      "data": base64.b64encode(ref_png).decode()}})
    body = {
        "contents": [{"parts": parts}],
        "generationConfig": {"responseModalities": ["IMAGE"],
                             "imageConfig": {"aspectRatio": "9:16"}},
    }
    last_err = None
    for model in models():
        req = urllib.request.Request(
            API.format(model=model), data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json", "x-goog-api-key": key})
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=180) as r:
                    data = json.load(r)
                for cand in data.get("candidates", []):
                    for p in cand.get("content", {}).get("parts", []):
                        inline = p.get("inlineData") or p.get("inline_data")
                        if inline and inline.get("data"):
                            print(f"  ok with {model}")
                            return base64.b64decode(inline["data"])
                last_err = f"{model}: no image in response: {json.dumps(data)[:300]}"
                break
            except urllib.error.HTTPError as e:
                msg = e.read().decode(errors="ignore")[:300]
                last_err = f"{model}: HTTP {e.code} {msg}"
                if e.code in (429, 500, 503):
                    time.sleep(10 * (attempt + 1))
                    continue
                break  # 400/404: try next model
            except Exception as e:  # network hiccup
                last_err = f"{model}: {e}"
                time.sleep(5)
        print("  " + last_err)
    raise RuntimeError(last_err)


def fill(tpl, persona, **kw):
    return tpl.format(identity=persona["identity"], style=persona["style"],
                      safety=persona["safety"], **kw)


def main():
    persona = json.loads((D / "persona.json").read_text())
    REF_DIR.mkdir(parents=True, exist_ok=True)
    IMG_DIR.mkdir(parents=True, exist_ok=True)

    if not REF.exists():
        prompt = fill(persona["reference_prompt"], persona)
        for i in range(1, 5):
            print(f"reference candidate {i}")
            png = call(prompt)
            (REF_DIR / f"candidate_{i}.png").write_bytes(png)
        REF.write_bytes((REF_DIR / "candidate_1.png").read_bytes())
        print("reference set: candidate_1 -> dami_ref.png")
        return

    scenes = json.loads((D / "scenes.json").read_text())
    state = json.loads(STATE.read_text()) if STATE.exists() else {"next": 0}
    per_run = int(os.environ.get("DAMI_PER_RUN", "3"))
    ref_png = REF.read_bytes()
    made = 0
    while made < per_run and state["next"] < len(scenes):
        s = scenes[state["next"]]
        out = IMG_DIR / f"{s['id']}.png"
        if not out.exists():
            print(f"scene {s['id']}: {s['scene'][:60]}")
            out.write_bytes(call(fill(persona["scene_prompt"], persona, scene=s["scene"]), ref_png))
            made += 1
        state["next"] += 1
        STATE.write_text(json.dumps(state))
    left = len(scenes) - state["next"]
    print(f"made {made}, scenes left in queue: {left}")
    if left < 6:
        print("::warning::Dami scene queue is running low - add scenes to dami/scenes.json")


if __name__ == "__main__":
    if not os.environ.get("GEMINI_API_KEY"):
        sys.exit("GEMINI_API_KEY secret is not set")
    main()
