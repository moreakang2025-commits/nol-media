"""Upload a built episode to YouTube as PRIVATE (resumable upload) and try to set the thumbnail.
Needs YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN. usage: upload.py out/ep01"""
import json, os, sys
import requests

def token():
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": os.environ["YT_CLIENT_ID"], "client_secret": os.environ["YT_CLIENT_SECRET"],
        "refresh_token": os.environ["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"}, timeout=30)
    r.raise_for_status(); return r.json()["access_token"]

def captions(tok, vid, transcript_path, srt_path=None):
    """Add an English CC track. With a plain transcript, YouTube syncs the timing itself (sync=true).
    Needs the youtube.force-ssl scope; with upload-only scope this returns 403."""
    import uuid
    use_sync = os.path.exists(transcript_path)
    path = transcript_path if use_sync else srt_path
    body = open(path, "rb").read()
    meta = json.dumps({"snippet": {"videoId": vid, "language": "en", "name": "English", "isDraft": False}}).encode()
    b = uuid.uuid4().hex
    data = (f"--{b}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n").encode() + meta + \
           (f"\r\n--{b}\r\nContent-Type: {'text/plain' if use_sync else 'application/octet-stream'}\r\n\r\n").encode() + body + \
           f"\r\n--{b}--".encode()
    url = "https://www.googleapis.com/upload/youtube/v3/captions?uploadType=multipart&part=snippet" + ("&sync=true" if use_sync else "")
    r = requests.post(url, headers={"Authorization": f"Bearer {tok}", "Content-Type": f"multipart/related; boundary={b}"}, data=data, timeout=120)
    return "added" if r.ok else f"failed {r.status_code}: {r.text[:300]}"

def main(outdir, publish_at=None):
    """publish_at: RFC3339 UTC time. The video is uploaded private with status.publishAt so YouTube makes it
    public at that time by itself."""
    meta = json.load(open(os.path.join(outdir, "meta.json")))
    held = None
    qa_path = os.path.join(outdir, "audio_qa.json")
    if publish_at and os.path.exists(qa_path):   # never auto-publish audio that failed the defect check
        q = json.load(open(qa_path)); fin = q.get("final_decoded", {})
        ticks = q.get("final_isolated_ticks", fin.get("isolated_ticks", 0)); mins = max(0.5, json.load(open(os.path.join(outdir, "meta.json"))).get("duration", 60) / 60)
        if fin.get("clipped", 0) > 0 or ticks > max(4, 2 * mins):
            held = f"audio defects: clipped={fin.get('clipped')} isolated_ticks={ticks}"; publish_at = None
    tok = token(); hdr = {"Authorization": f"Bearer {tok}"}
    body = {"snippet": {"title": meta["title"][:100], "description": meta["description"][:4900],
                        "tags": meta["tags"], "categoryId": "27", "defaultLanguage": "en", "defaultAudioLanguage": "en"},
            "status": {"privacyStatus": "private", "selfDeclaredMadeForKids": False, "containsSyntheticMedia": False}}
    if publish_at: body["status"]["publishAt"] = publish_at
    video = os.path.join(outdir, "video.mp4"); size = os.path.getsize(video)
    r = requests.post("https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
                      headers={**hdr, "Content-Type": "application/json", "X-Upload-Content-Type": "video/mp4",
                               "X-Upload-Content-Length": str(size)}, data=json.dumps(body), timeout=60)
    if not r.ok:
        res = {"error": f"upload init {r.status_code}: {r.text[:600]}", "publish_at_requested": publish_at}
        json.dump(res, open(os.path.join(outdir, "upload.json"), "w"), indent=1); print("[upload]", res); sys.exit(1)
    loc = r.headers["Location"]
    with open(video, "rb") as f:
        r = requests.put(loc, headers={**hdr, "Content-Type": "video/mp4"}, data=f, timeout=3600)
    r.raise_for_status(); vid = r.json()["id"]; print("[upload] video id", vid)
    res = {"video_id": vid, "url": f"https://youtu.be/{vid}", "privacy": "private", "publish_at_requested": publish_at, "held": held}
    try:
        with open(os.path.join(outdir, "thumb.jpg"), "rb") as f:
            t = requests.post(f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={vid}",
                              headers={**hdr, "Content-Type": "image/jpeg"}, data=f, timeout=120)
        res["thumbnail"] = "set" if t.ok else f"failed {t.status_code}: {t.text[:300]}"
    except Exception as e:
        res["thumbnail"] = f"failed: {e}"
    try:
        res["captions"] = captions(tok, vid, os.path.join(outdir, "transcript.txt"), os.path.join(outdir, "captions.srt"))
    except Exception as e:
        res["captions"] = f"failed: {e}"
    try:  # what YouTube actually kept (an unverified API project may force private and drop publishAt)
        st = requests.get("https://www.googleapis.com/youtube/v3/videos", params={"part": "status", "id": vid},
                          headers=hdr, timeout=30).json()["items"][0]["status"]
        res["status_now"] = {k: st.get(k) for k in ("privacyStatus", "publishAt", "uploadStatus")}
    except Exception as e:
        res["status_now"] = f"check failed: {e}"
    print("[upload]", res)
    json.dump(res, open(os.path.join(outdir, "upload.json"), "w"), indent=1)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else None)
