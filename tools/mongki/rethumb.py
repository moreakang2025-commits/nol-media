"""Remake the thumbnail for an episode and set it on an already uploaded video.
usage: rethumb.py mongki/episodes/ep01.json VIDEO_ID"""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import requests, thumb
from upload import token

ep = json.load(open(sys.argv[1])); vid = sys.argv[2]
os.makedirs("out", exist_ok=True); out = f"out/{ep['id']}_thumb.jpg"
thumb.make(ep, out)
with open(out, "rb") as f:
    r = requests.post(f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={vid}",
                      headers={"Authorization": f"Bearer {token()}", "Content-Type": "image/jpeg"}, data=f, timeout=120)
print("[rethumb]", r.status_code, r.text[:300])
os.makedirs("mongki/results", exist_ok=True)
os.replace(out, f"mongki/results/{ep['id']}_thumb.jpg")
rep = f"out/{ep['id']}_thumb_report.json"
if os.path.exists(rep): os.replace(rep, f"mongki/results/{ep['id']}_thumb_report.json")
json.dump({"video_id": vid, "status": r.status_code, "body": r.text[:300]}, open(f"mongki/results/{ep['id']}_rethumb.json", "w"), indent=1)
