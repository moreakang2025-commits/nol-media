"""Parse a Front Porch Stories episode file (fps/episodes/epNN.txt).

Format
  KEY: value            header fields (TITLE, VOICE_STYLE, THUMB_TOP, THUMB_BOTTOM, THUMB_PROMPT, TAGS)
  CAST Name | voice=Gacrux | look=... | style=...
  DESCRIPTION: ... END_DESCRIPTION   (multi-line; {chapters} is replaced with timestamps)
  ## Chapter name       starts a chapter
  [SHOT] prompt          a new picture (generated) starts at the next spoken line
  [SHORT] hook title     a vertical Short starts at the next spoken line (up to ~58 s)
  [LIB] id id ...        library pictures (fps/library/img/<id>.jpg), time split evenly between them
  NAME: text             a spoken line (NAME must be in CAST)
  # comment              ignored
"""
import re

def parse(path):
    ep = {"cast": {}, "items": [], "tags": [], "description": ""}
    lines = open(path, encoding="utf-8").read().splitlines()
    i = 0; chapter = None
    while i < len(lines):
        raw = lines[i].rstrip(); i += 1
        s = raw.strip()
        if not s or (s.startswith("#") and not s.startswith("##")):
            continue
        if s.startswith("DESCRIPTION:"):
            buf = [s[len("DESCRIPTION:"):].strip()]
            while i < len(lines) and lines[i].strip() != "END_DESCRIPTION":
                buf.append(lines[i].rstrip()); i += 1
            i += 1; ep["description"] = "\n".join(buf).strip(); continue
        if s.startswith("CAST "):
            parts = [p.strip() for p in s[5:].split("|")]
            c = {"name": parts[0]}
            for p in parts[1:]:
                k, _, v = p.partition("="); c[k.strip()] = v.strip()
            ep["cast"][parts[0].upper()] = c; continue
        if s.startswith("## "):
            chapter = s[3:].strip(); ep["items"].append({"kind": "chapter", "name": chapter}); continue
        if s.startswith("[SHORT]"):
            ep["items"].append({"kind": "short", "title": s[7:].strip()}); continue
        if s.startswith("[LIB]"):
            ep["items"].append({"kind": "shot", "prompt": "", "lib": s[5:].split()}); continue
        if s.startswith("[SHOT]"):
            ep["items"].append({"kind": "shot", "prompt": s[6:].strip()}); continue
        m = re.match(r"^([A-Z][A-Z ]{1,20}):\s*(.+)$", s)
        if m and m.group(1).strip() in ep["cast"]:
            ep["items"].append({"kind": "line", "who": m.group(1).strip(), "text": m.group(2).strip()}); continue
        m = re.match(r"^([A-Z_]+):\s*(.*)$", s)
        if m:
            k, v = m.group(1), m.group(2)
            if k == "TAGS": ep["tags"] = [t.strip() for t in v.split(",") if t.strip()]
            else: ep[k.lower()] = v
            continue
        raise SystemExit(f"[story] cannot parse line {i}: {raw}")
    return ep

def words(text):
    return len(re.findall(r"[A-Za-z0-9']+", text))

def spoken(text):
    """What the voice says: strip stage directions in (parentheses)."""
    return re.sub(r"\s*\([^)]*\)", "", text).strip()

def stats(ep):
    ls = [x for x in ep["items"] if x["kind"] == "line"]
    w = sum(words(spoken(x["text"])) for x in ls)
    shots = sum(1 for x in ep["items"] if x["kind"] == "shot")
    chaps = sum(1 for x in ep["items"] if x["kind"] == "chapter")
    return {"words": w, "lines": len(ls), "shots": shots, "chapters": chaps, "est_minutes_at_150wpm": round(w / 150, 1)}

if __name__ == "__main__":
    import sys, json
    e = parse(sys.argv[1]); print(json.dumps(stats(e), indent=1)); print("title", len(e.get("title", "")), e.get("title"))
