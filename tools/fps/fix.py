"""One-off fixes on already uploaded videos. Reads commands from fps/fix.txt (one per line):
  schedule <video_id> <US date YYYY-MM-DD> <long|s1|s2|s3|s4>   set a publish time (stays private until then)
  rethumb <epNN>                                                  make a new thumbnail for the episode and set it
Writes fps/results/fix_log.json."""
import json, os, sys
import requests
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "mongki"))
from upload import token
import when
G = "https://www.googleapis.com/youtube/v3"

def schedule(hdr, vid, date, slot):
    t = when.at(date, slot)
    r = requests.put(f"{G}/videos?part=status", headers={**hdr, "Content-Type": "application/json"},
                     data=json.dumps({"id": vid, "status": {"privacyStatus": "private", "publishAt": t,
                                                            "selfDeclaredMadeForKids": False, "containsSyntheticMedia": True}}), timeout=30)
    return {"cmd": "schedule", "id": vid, "publishAt": t, "ok": r.ok, "detail": "" if r.ok else r.text[:300]}

def rethumb(hdr, ep):
    import build, story, images as IM
    e = story.parse(f"fps/episodes/{ep}.txt"); refs = IM.portraits(e["cast"]); out = f"fps/results/{ep}_thumb.jpg"
    build.thumbnail(e, refs, out)
    vid = json.load(open(f"fps/results/{ep}_upload.json"))["video_id"]
    with open(out, "rb") as f:
        r = requests.post(f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={vid}",
                          headers={**hdr, "Content-Type": "image/jpeg"}, data=f, timeout=120)
    return {"cmd": "rethumb", "ep": ep, "id": vid, "ok": r.ok, "detail": "" if r.ok else r.text[:300]}

def main():
    hdr = {"Authorization": f"Bearer {token()}"}; log = []
    for line in open("fps/fix.txt"):
        p = line.split()
        if not p or p[0].startswith("#"): continue
        try:
            if p[0] == "schedule": log.append(schedule(hdr, p[1], p[2], p[3]))
            elif p[0] == "rethumb": log.append(rethumb(hdr, p[1]))
        except Exception as e:
            log.append({"cmd": line.strip(), "ok": False, "detail": str(e)[:300]})
        print(log[-1], flush=True)
    os.makedirs("fps/results", exist_ok=True); json.dump(log, open("fps/results/fix_log.json", "w"), indent=1)

if __name__ == "__main__":
    main()
