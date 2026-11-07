"""Collect public comments from Mongki Money's videos into mongki/ideas/comments.json.
Needs YT_API_KEY (plain API key, YouTube Data API v3). Private videos are skipped by the API.
Each call costs 1 quota unit."""
import datetime as dt, json, os, re, sys
import requests

API = "https://www.googleapis.com/youtube/v3"
CHANNEL = os.environ.get("MONGKI_CHANNEL_ID", "UC6itM-fN4ycJLhiNGkHhpbg")
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "mongki", "ideas", "comments.json")

def get(path, **params):
    params["key"] = os.environ["YT_API_KEY"]
    r = requests.get(f"{API}/{path}", params=params, timeout=30); r.raise_for_status(); return r.json()

def uploads(limit=50):
    pl = "UU" + CHANNEL[2:]; ids = []; tok = None
    while len(ids) < limit:
        j = get("playlistItems", part="contentDetails,snippet", playlistId=pl, maxResults=50, **({"pageToken": tok} if tok else {}))
        ids += [(i["contentDetails"]["videoId"], i["snippet"]["title"]) for i in j.get("items", [])]
        tok = j.get("nextPageToken")
        if not tok: break
    return ids[:limit]

def comments(vid, limit=200):
    out = []; tok = None
    while len(out) < limit:
        try:
            j = get("commentThreads", part="snippet", videoId=vid, maxResults=100, order="relevance", textFormat="plainText",
                    **({"pageToken": tok} if tok else {}))
        except requests.HTTPError as e:
            print(f"[comments] {vid}: {e}"); break
        for it in j.get("items", []):
            s = it["snippet"]["topLevelComment"]["snippet"]
            out.append({"id": it["id"], "video": vid, "author": s.get("authorDisplayName", ""), "text": s.get("textDisplay", "")[:500],
                        "likes": s.get("likeCount", 0), "replies": it["snippet"].get("totalReplyCount", 0), "at": s.get("publishedAt")})
        tok = j.get("nextPageToken")
        if not tok: break
    return out

def performance(vids):
    """Public stats of our uploads (1 quota unit per 50 videos) -> mongki/ideas/performance.json, best first."""
    out = []
    for i in range(0, len(vids), 50):
        j = get("videos", part="statistics,snippet,contentDetails", id=",".join(v for v, _ in vids[i:i + 50]))
        for it in j.get("items", []):
            st = it.get("statistics", {})
            out.append({"id": it["id"], "title": it["snippet"]["title"], "published": it["snippet"].get("publishedAt"),
                        "duration": it["contentDetails"].get("duration"), "views": int(st.get("viewCount", 0)),
                        "likes": int(st.get("likeCount", 0)), "comments": int(st.get("commentCount", 0))})
    out.sort(key=lambda x: -x["views"])
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    path = os.path.join(os.path.dirname(OUT), "performance.json")
    json.dump({"updated": dt.datetime.utcnow().isoformat() + "Z", "videos": out}, open(path, "w"), indent=1, ensure_ascii=False)
    print(f"[comments] performance for {len(out)} videos")

def main():
    if not os.environ.get("YT_API_KEY"):
        print("[comments] YT_API_KEY not set, skipping"); return
    old = {}
    if os.path.exists(OUT):
        for c in json.load(open(OUT)).get("comments", []): old[c["id"]] = c
    ups = uploads()
    try: performance(ups)
    except Exception as e: print("[comments] performance failed:", e)
    for vid, title in ups:
        for c in comments(vid):
            c["video_title"] = title; c["used"] = old.get(c["id"], {}).get("used", False); old[c["id"]] = c
    allc = sorted(old.values(), key=lambda c: (-(c["likes"] + 2 * c["replies"]), c["at"] or ""))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({"updated": dt.datetime.utcnow().isoformat() + "Z", "count": len(allc), "comments": allc}, open(OUT, "w"), indent=1, ensure_ascii=False)
    print(f"[comments] saved {len(allc)} comments")

if __name__ == "__main__":
    main()
