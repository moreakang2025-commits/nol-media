"""List every upload on the channel with its privacy. With --privatize-mongki, any non-private video that
is not a Front Porch Stories upload (i.e. an old Mongki Money video) is set to private. Nothing is deleted.
Writes fps/results/channel_check.json."""
import json, os, sys
import requests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mongki"))
from upload import token

def main():
    fix = "--privatize-mongki" in sys.argv
    hdr = {"Authorization": f"Bearer {token()}"}; G = "https://www.googleapis.com/youtube/v3"
    ch = requests.get(f"{G}/channels", params={"part": "snippet,contentDetails,statistics,brandingSettings", "mine": "true"}, headers=hdr, timeout=30).json()
    if "items" not in ch: print(ch); raise SystemExit("channel lookup failed")
    c = ch["items"][0]; up = c["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, tok = [], None
    while True:
        p = {"part": "contentDetails", "playlistId": up, "maxResults": 50}
        if tok: p["pageToken"] = tok
        r = requests.get(f"{G}/playlistItems", params=p, headers=hdr, timeout=30).json()
        ids += [i["contentDetails"]["videoId"] for i in r.get("items", [])]; tok = r.get("nextPageToken")
        if not tok: break
    vids = []
    for k in range(0, len(ids), 50):
        r = requests.get(f"{G}/videos", params={"part": "snippet,status,contentDetails", "id": ",".join(ids[k:k + 50])}, headers=hdr, timeout=30).json()
        vids += r.get("items", [])
    fps_ids = set(json.load(open("fps/results/fps_ids.json"))) if os.path.exists("fps/results/fps_ids.json") else set()
    rows, changed = [], []
    for v in vids:
        st = v["status"]; row = {"id": v["id"], "title": v["snippet"]["title"], "privacy": st["privacyStatus"],
                                 "publishAt": st.get("publishAt"), "published": v["snippet"]["publishedAt"], "duration": v["contentDetails"]["duration"]}
        if fix and v["id"] not in fps_ids and (st["privacyStatus"] != "private" or st.get("publishAt")):
            u = requests.put(f"{G}/videos?part=status", headers={**hdr, "Content-Type": "application/json"},
                             data=json.dumps({"id": v["id"], "status": {"privacyStatus": "private", "selfDeclaredMadeForKids": False}}), timeout=30)
            row["action"] = "set private" if u.ok else f"failed {u.status_code}: {u.text[:200]}"; changed.append(row["id"])
        rows.append(row)
    out = {"channel": {"id": c["id"], "title": c["snippet"]["title"], "handle": c["snippet"].get("customUrl"),
                       "country": c["snippet"].get("country"), "subscribers": c["statistics"].get("subscriberCount"),
                       "keywords": c.get("brandingSettings", {}).get("channel", {}).get("keywords")},
           "total": len(rows), "by_privacy": {p: sum(1 for r in rows if r["privacy"] == p) for p in {r["privacy"] for r in rows}},
           "changed": changed, "videos": rows}
    os.makedirs("fps/results", exist_ok=True); json.dump(out, open("fps/results/channel_check.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "videos"}, indent=1))

if __name__ == "__main__":
    main()
