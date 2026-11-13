"""Collect performance data for every Front Porch Stories upload (read-only, changes nothing on YouTube).
1) YouTube Data API: views / likes / comments per video (works with the existing token).
2) YouTube Analytics API: watch time, average view %, retention, traffic sources, audience, per-day views.
   Needs the yt-analytics.readonly scope; if the token lacks it, the error is recorded and part 1 still runs.
Writes fps/results/stats.json (latest) and fps/results/stats/YYYY-MM-DD.json (history)."""
import datetime as dt, json, os, re, sys
import requests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mongki"))
from upload import token

G = "https://www.googleapis.com/youtube/v3"
A = "https://youtubeanalytics.googleapis.com/v2/reports"


def secs(iso):
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    return sum(int(x or 0) * k for x, k in zip(m.groups(), (3600, 60, 1))) if m else 0


def episode_map():
    """video_id -> {ep, kind(long|s1..s4), theme, title}"""
    out, themes = {}, {}
    if os.path.exists("fps/episodes/LOG.md"):
        for line in open("fps/episodes/LOG.md"):
            c = [x.strip() for x in line.split("|")]
            if len(c) > 4 and re.match(r"ep\d+$", c[1]): themes[c[1]] = c[3]
    for f in sorted(os.listdir("fps/results")):
        m = re.match(r"(ep\d+)(?:_(s\d))?_upload\.json$", f)
        if not m: continue
        d = json.load(open(f"fps/results/{f}"))
        if d.get("video_id"):
            out[d["video_id"]] = {"ep": m[1], "kind": m[2] or "long", "theme": themes.get(m[1], "?"),
                                  "publish_at": d.get("publish_at")}
    return out


def analytics(hdr, start, end, **p):
    r = requests.get(A, params={"ids": "channel==MINE", "startDate": start, "endDate": end, **p}, headers=hdr, timeout=60)
    if not r.ok: return {"error": f"{r.status_code}: {r.text[:300]}"}
    j = r.json(); cols = [h["name"] for h in j.get("columnHeaders", [])]
    return {"rows": [dict(zip(cols, row)) for row in j.get("rows", [])]}


def main():
    tok = token(); hdr = {"Authorization": f"Bearer {tok}"}
    scopes = requests.get("https://oauth2.googleapis.com/tokeninfo", params={"access_token": tok}, timeout=30).json().get("scope", "")
    emap = episode_map(); ids = list(emap)
    vids = []
    for k in range(0, len(ids), 50):
        r = requests.get(f"{G}/videos", params={"part": "snippet,statistics,status,contentDetails", "id": ",".join(ids[k:k + 50])},
                         headers=hdr, timeout=30).json()
        vids += r.get("items", [])
    ch = requests.get(f"{G}/channels", params={"part": "statistics", "mine": "true"}, headers=hdr, timeout=30).json()["items"][0]["statistics"]
    rows = []
    for v in vids:
        s = v.get("statistics", {}); e = emap[v["id"]]
        views = int(s.get("viewCount", 0)); likes = int(s.get("likeCount", 0))
        rows.append({"id": v["id"], **e, "title": v["snippet"]["title"], "published": v["snippet"].get("publishedAt"), "privacy": v["status"]["privacyStatus"],
                     "seconds": secs(v["contentDetails"]["duration"]), "views": views, "likes": likes,
                     "comments": int(s.get("commentCount", 0)), "like_rate": round(likes / views, 4) if views else None})
    today = dt.date.today().isoformat(); start = "2026-11-01"
    an = {"scope_ok": "yt-analytics" in scopes}
    if an["scope_ok"]:
        vf = ",".join(ids[:200])
        an["by_video"] = analytics(hdr, start, today, dimensions="video", filters=f"video=={vf}",
                                   metrics="views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,likes,comments,shares,subscribersGained",
                                   sort="-views", maxResults=200)
        an["by_day"] = analytics(hdr, start, today, dimensions="day", metrics="views,estimatedMinutesWatched,subscribersGained")
        an["traffic"] = analytics(hdr, start, today, dimensions="insightTrafficSourceType", metrics="views,estimatedMinutesWatched")
        an["audience"] = analytics(hdr, start, today, dimensions="ageGroup,gender", metrics="viewerPercentage")
        an["country"] = analytics(hdr, start, today, dimensions="country", metrics="views", sort="-views", maxResults=10)
        an["device"] = analytics(hdr, start, today, dimensions="deviceType", metrics="views,estimatedMinutesWatched")
        an["retention"] = {}
        for vid, e in emap.items():
            if e["kind"] == "long":
                an["retention"][e["ep"]] = analytics(hdr, start, today, dimensions="elapsedVideoTimeRatio",
                                                     metrics="audienceWatchRatio,relativeRetentionPerformance",
                                                     filters=f"video=={vid};audienceType==ORGANIC")
    else:
        an["error"] = "token has no yt-analytics.readonly scope (only views/likes/comments collected). Scopes: " + scopes
    out = {"collected": dt.datetime.utcnow().isoformat(timespec="seconds") + "Z", "channel": ch, "videos": rows, "analytics": an}
    os.makedirs("fps/results/stats", exist_ok=True)
    json.dump(out, open("fps/results/stats.json", "w"), indent=1)
    json.dump(out, open(f"fps/results/stats/{today}.json", "w"), indent=1)
    print(json.dumps({"channel": ch, "videos": len(rows), "scope_ok": an["scope_ok"], "views": sum(r["views"] for r in rows)}, indent=1))


if __name__ == "__main__":
    main()
