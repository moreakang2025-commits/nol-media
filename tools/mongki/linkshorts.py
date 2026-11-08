"""Point Shorts at their long-form video: put '▶ Full video: <url>' at the top of each Short's description.
(The Studio-only 'Related video' button is set separately by browser automation.)
usage: linkshorts.py LONG_ID SHORT_ID [SHORT_ID ...]   (needs YT_CLIENT_ID/SECRET/REFRESH_TOKEN)"""
import json, os, sys
import requests
from upload import token

def link(tok, short_id, long_id):
    hdr = {"Authorization": f"Bearer {tok}"}
    it = requests.get("https://www.googleapis.com/youtube/v3/videos", params={"part": "snippet", "id": short_id},
                      headers=hdr, timeout=30).json()["items"][0]["snippet"]
    line = f"▶ Full video: https://youtu.be/{long_id}"
    desc = it.get("description", "")
    if line in desc: return "already"
    desc = line + "\n\n" + "\n".join(l for l in desc.splitlines() if not l.startswith("▶ Full video:"))
    body = {"id": short_id, "snippet": {"title": it["title"], "categoryId": it.get("categoryId", "27"), "description": desc[:4900],
                                         "tags": it.get("tags", []), "defaultLanguage": it.get("defaultLanguage", "en")}}
    r = requests.put("https://www.googleapis.com/youtube/v3/videos?part=snippet", headers={**hdr, "Content-Type": "application/json"},
                     data=json.dumps(body), timeout=30)
    return "linked" if r.ok else f"failed {r.status_code}: {r.text[:200]}"

if __name__ == "__main__":
    tok = token(); long_id = sys.argv[1]
    out = {s: link(tok, s, long_id) for s in sys.argv[2:]}
    print("[link]", out)
