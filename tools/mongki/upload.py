"""Upload a built episode to YouTube as PRIVATE (resumable upload) and try to set the thumbnail.
Needs YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN. usage: upload.py out/ep01"""
import json, os, sys
import requests

def token():
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": os.environ["YT_CLIENT_ID"], "client_secret": os.environ["YT_CLIENT_SECRET"],
        "refresh_token": os.environ["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"}, timeout=30)
    r.raise_for_status(); return r.json()["access_token"]

def main(outdir):
    meta = json.load(open(os.path.join(outdir, "meta.json")))
    tok = token(); hdr = {"Authorization": f"Bearer {tok}"}
    body = {"snippet": {"title": meta["title"][:100], "description": meta["description"][:4900],
                        "tags": meta["tags"], "categoryId": "27", "defaultLanguage": "en", "defaultAudioLanguage": "en"},
            "status": {"privacyStatus": "private", "selfDeclaredMadeForKids": False, "containsSyntheticMedia": False}}
    video = os.path.join(outdir, "video.mp4"); size = os.path.getsize(video)
    r = requests.post("https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
                      headers={**hdr, "Content-Type": "application/json", "X-Upload-Content-Type": "video/mp4",
                               "X-Upload-Content-Length": str(size)}, data=json.dumps(body), timeout=60)
    r.raise_for_status(); loc = r.headers["Location"]
    with open(video, "rb") as f:
        r = requests.put(loc, headers={**hdr, "Content-Type": "video/mp4"}, data=f, timeout=3600)
    r.raise_for_status(); vid = r.json()["id"]; print("[upload] video id", vid)
    res = {"video_id": vid, "url": f"https://youtu.be/{vid}", "privacy": "private"}
    try:
        with open(os.path.join(outdir, "thumb.jpg"), "rb") as f:
            t = requests.post(f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={vid}",
                              headers={**hdr, "Content-Type": "image/jpeg"}, data=f, timeout=120)
        res["thumbnail"] = "set" if t.ok else f"failed {t.status_code}: {t.text[:300]}"
    except Exception as e:
        res["thumbnail"] = f"failed: {e}"
    print("[upload]", res)
    json.dump(res, open(os.path.join(outdir, "upload.json"), "w"), indent=1)

if __name__ == "__main__":
    main(sys.argv[1])
