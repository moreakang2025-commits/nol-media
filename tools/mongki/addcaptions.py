"""Add an English CC track to an already uploaded episode (transcript rebuilt from the episode + live data).
usage: addcaptions.py mongki/episodes/ep01.json VIDEO_ID"""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import data as D
from upload import token, captions

ep = json.load(open(sys.argv[1])); vid = sys.argv[2]
ctx = D.compute(ep)
lines = [D.fill(s.get("vo", ""), ctx) for s in ep["segments"] if s.get("vo")]
os.makedirs("out", exist_ok=True); tp = f"out/{ep['id']}_transcript.txt"
open(tp, "w").write("\n".join(lines) + "\n")
res = captions(token(), vid, tp)
print("[captions]", res)
os.makedirs("mongki/results", exist_ok=True)
json.dump({"video_id": vid, "captions": res}, open(f"mongki/results/{ep['id']}_captions.json", "w"), indent=1)
