"""Front Porch Stories: upload PRIVATE (no publish time unless given), Entertainment category,
synthetic-media label ON (photoreal AI people), thumbnail + English CC track.
usage: upload.py out/fps_ep01 [RFC3339 publishAt]"""
import json, os, sys
import requests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mongki"))
from upload import token, captions

def main(outdir, publish_at=None):
    meta = json.load(open(os.path.join(outdir, "meta.json")))
    tok = token(); hdr = {"Authorization": f"Bearer {tok}"}
    body = {"snippet": {"title": meta["title"][:100], "description": meta["description"][:4900], "tags": meta["tags"],
                        "categoryId": "24", "defaultLanguage": "en", "defaultAudioLanguage": "en"},
            "status": {"privacyStatus": "private", "selfDeclaredMadeForKids": False, "containsSyntheticMedia": True}}
    if publish_at: body["status"]["publishAt"] = publish_at
    video = os.path.join(outdir, "video.mp4"); size = os.path.getsize(video)
    r = requests.post("https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
                      headers={**hdr, "Content-Type": "application/json", "X-Upload-Content-Type": "video/mp4",
                               "X-Upload-Content-Length": str(size)}, data=json.dumps(body), timeout=60)
    if not r.ok:
        res = {"error": f"upload init {r.status_code}: {r.text[:600]}"}
        json.dump(res, open(os.path.join(outdir, "upload.json"), "w"), indent=1); print(res); sys.exit(1)
    with open(video, "rb") as f:
        r = requests.put(r.headers["Location"], headers={**hdr, "Content-Type": "video/mp4"}, data=f, timeout=3600)
    r.raise_for_status(); vid = r.json()["id"]
    res = {"video_id": vid, "url": f"https://youtu.be/{vid}", "privacy": "private", "publish_at": publish_at}
    try:
        with open(os.path.join(outdir, "thumb.jpg"), "rb") as f:
            t = requests.post(f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={vid}",
                              headers={**hdr, "Content-Type": "image/jpeg"}, data=f, timeout=120)
        res["thumbnail"] = "set" if t.ok else f"failed {t.status_code}: {t.text[:300]}"
    except Exception as e:
        res["thumbnail"] = f"failed: {e}"
    try: res["captions"] = captions(tok, vid, os.path.join(outdir, "transcript.txt"))
    except Exception as e: res["captions"] = f"failed: {e}"
    try:
        st = requests.get("https://www.googleapis.com/youtube/v3/videos", params={"part": "status", "id": vid}, headers=hdr, timeout=30).json()["items"][0]["status"]
        res["status_now"] = {k: st.get(k) for k in ("privacyStatus", "publishAt", "uploadStatus", "containsSyntheticMedia")}
    except Exception as e: res["status_now"] = f"check failed: {e}"
    print("[upload]", res); json.dump(res, open(os.path.join(outdir, "upload.json"), "w"), indent=1)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else None)
