"""Turn fps/results/stats.json (+ daily history in fps/results/stats/) into fps/results/insights.md.
Compares fairly by using views at ~48 h after publish when history allows, else views per day of age.
Groups: long vs Shorts, Short role (s1 insult, s2 plan, s3 hidden card, s4 payoff), publish time (ET), theme lane,
weekday. Small samples are flagged; nothing here changes YouTube."""
import glob, json, os
from collections import defaultdict
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

ROLE = {"long": "long-form", "s1": "s1 insult", "s2": "s2 plan", "s3": "s3 hidden card", "s4": "s4 payoff"}
ET = ZoneInfo("America/New_York")


def views_at_48h(vid, pub, hist):
    """first snapshot at least 40 h after publish -> its views (None if none yet)"""
    for t, views in hist.get(vid, []):
        if (t - pub).total_seconds() >= 40 * 3600: return views
    return None


def main():
    cur = json.load(open("fps/results/stats.json"))
    now = datetime.fromisoformat(cur["collected"].replace("Z", "+00:00"))
    hist = defaultdict(list)
    for f in sorted(glob.glob("fps/results/stats/*.json")):
        d = json.load(open(f)); t = datetime.fromisoformat(d["collected"].replace("Z", "+00:00"))
        for v in d["videos"]: hist[v["id"]].append((t, v["views"]))
    rows = []
    for v in cur["videos"]:
        when = v.get("publish_at") or v.get("published")
        if v["privacy"] != "public" or not when: continue
        pub = datetime.fromisoformat(when.replace("Z", "+00:00")); age_d = max((now - pub).total_seconds() / 86400, 0.25)
        v48 = views_at_48h(v["id"], pub, hist)
        rows.append({**v, "age_d": age_d, "v48": v48, "vpd": v["views"] / age_d,
                     "slot": pub.astimezone(ET).strftime("%H:%M ET"), "weekday": pub.astimezone(ET).strftime("%a")})

    def table(key, label, only=None):
        g = defaultdict(list)
        for r in rows:
            if only and not only(r): continue
            g[key(r)].append(r)
        out = [f"\n### {label}", "| group | n | views | views/day | views@48h avg | likes | like rate |", "|---|---|---|---|---|---|---|"]
        for k, rs in sorted(g.items(), key=lambda kv: -sum(r["vpd"] for r in kv[1]) / len(kv[1])):
            v = sum(r["views"] for r in rs); l = sum(r["likes"] for r in rs)
            v48 = [r["v48"] for r in rs if r["v48"] is not None]
            out.append(f"| {k} | {len(rs)} | {v} | {sum(r['vpd'] for r in rs) / len(rs):.1f} | "
                       f"{(sum(v48) / len(v48)) if v48 else float('nan'):.1f} | {l} | {(l / v * 100) if v else 0:.1f}% |")
        return out

    shorts = lambda r: r["kind"] != "long"
    md = [f"# Front Porch Stories — insights ({now:%Y-%m-%d %H:%M} UTC)",
          f"Channel: {cur['channel'].get('subscriberCount')} subscribers, {cur['channel'].get('viewCount')} total views. "
          f"Public FPS videos analysed: {len(rows)}.",
          "Analytics API (watch time, retention, audience, traffic): " + ("ON" if cur["analytics"].get("scope_ok") else "OFF — owner must re-authorize with yt-analytics.readonly")]
    if len(rows) < 30: md.append(f"**Small sample ({len(rows)} videos): treat every pattern as a hint, not a rule.**")
    md += table(lambda r: "Shorts" if shorts(r) else "long-form", "Long-form vs Shorts")
    md += table(lambda r: ROLE[r["kind"]], "Short role (which part of the story)", shorts)
    md += table(lambda r: r["slot"], "Shorts publish time (ET)", shorts)
    md += table(lambda r: r["theme"], "Theme lane (long-form)", lambda r: not shorts(r))
    md += table(lambda r: r["theme"], "Theme lane (Shorts)", shorts)
    md += table(lambda r: r["weekday"], "Weekday (all)")
    md += ["\n### Top 5 videos by views/day", "| ep | kind | slot | views | views/day | likes | title |", "|---|---|---|---|---|---|---|"]
    for r in sorted(rows, key=lambda r: -r["vpd"])[:5]:
        md.append(f"| {r['ep']} | {r['kind']} | {r['slot']} | {r['views']} | {r['vpd']:.1f} | {r['likes']} | {r['title'][:70]} |")
    an = cur["analytics"]
    if an.get("scope_ok") and "rows" in an.get("by_video", {}):
        md += ["\n### Watch time (Analytics API)", "| video | views | avg view % | avg seconds | subs gained |", "|---|---|---|---|---|"]
        for r in an["by_video"]["rows"][:15]:
            md.append(f"| {r['video']} | {r['views']} | {r['averageViewPercentage']:.0f}% | {r['averageViewDuration']} | {r['subscribersGained']} |")
        for k in ("traffic", "audience", "device", "country"):
            if "rows" in an.get(k, {}): md += [f"\n### {k}", "```", json.dumps(an[k]["rows"][:12], indent=0), "```"]
    open("fps/results/insights.md", "w").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
