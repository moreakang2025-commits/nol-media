"""Check an episode script before building.  usage: python3 tools/fps/lint.py fps/episodes/epNN.txt
Exit 1 with reasons if it would fail or break channel rules."""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import story as ST
VOICES = {"Zephyr","Puck","Charon","Kore","Fenrir","Leda","Orus","Aoede","Callirrhoe","Autonoe","Enceladus","Iapetus","Umbriel",
          "Algieba","Despina","Erinome","Algenib","Rasalgethi","Laomedeia","Achernar","Alnilam","Schedar","Gacrux","Pulcherrima",
          "Achird","Zubenelgenubi","Vindemiatrix","Sadachbia","Sadaltager","Sulafat"}

def lint(path):
    e = ST.parse(path); errs, warn = [], []
    lib = {l.split()[1] for l in open("fps/library/library.txt") if l.startswith("IMG ")}
    roles = {l.split()[1] for l in open("fps/library/library.txt") if l.startswith("ROLE ")}
    solo = e.get("kind") == "short"     # standalone Short (fps/shorts/shNNN.txt)
    t = e.get("title", "")
    if not t or len(t) > 100: errs.append(f"title missing or over 100 chars ({len(t)})")
    for k in (("description",) if solo else ("thumb_top", "thumb_bottom", "thumb_prompt", "description")):
        if not e.get(k): errs.append(f"missing {k.upper()}")
    if not solo and "{chapters}" not in e.get("description", ""): errs.append("DESCRIPTION needs {chapters}")
    if "fiction" not in e.get("description", "").lower(): errs.append("DESCRIPTION needs the fiction disclaimer")
    if "AI" not in e.get("description", ""): errs.append("DESCRIPTION needs the AI tools note")
    for k, c in e["cast"].items():
        if c.get("voice") not in VOICES: errs.append(f"cast {c['name']}: unknown voice {c.get('voice')}")
        lk = c.get("look", "")
        if lk.startswith("lib:") and lk[4:] not in roles: errs.append(f"cast {c['name']}: unknown library face {lk}")
        elif lk.startswith("lib:") and not os.path.exists(f"fps/library/ref/{lk[4:]}.jpg"): warn.append(f"cast {c['name']}: face {lk} will be made at build (~$0.04)")
    st = ST.stats(e)
    shorts = [x for x in e["items"] if x["kind"] == "short"]
    if solo:
        if not 95 <= st["words"] <= 140: errs.append(f"{st['words']} spoken words (standalone Short: 95-140, about 45-58 s)")
        if len(shorts) != 1: errs.append(f"{len(shorts)} [SHORT] markers (standalone Short: exactly 1, before the first line)")
        if len(t) > 90: errs.append("standalone Short title over 90 chars (#Shorts is added)")
    else:
        if not 1550 <= st["words"] <= 2300: errs.append(f"{st['words']} words (aim 1,700-2,100 for 12-15 min)")
        if len(shorts) != 4: errs.append(f"{len(shorts)} [SHORT] markers (need exactly 4)")
    gen = 0; pics = 0; newpics = set()
    for x in e["items"]:
        if x["kind"] == "shot":
            if x.get("lib"):
                for i in x["lib"]:
                    pics += 1
                    if i not in lib: errs.append(f"unknown library picture {i}")
                    elif not os.path.exists(f"fps/library/img/{i}.jpg"): newpics.add(i)
            else: gen += 1; pics += 1
    if newpics: warn.append(f"{len(newpics)} new library pictures will be made at build (~${0.04*len(newpics):.2f}): {' '.join(sorted(newpics))}")
    if len(newpics) > 25: errs.append(f"{len(newpics)} new library pictures in one episode (max 25)")
    if gen > 2: errs.append(f"{gen} generated [SHOT]s (max 2, each costs money; use [LIB])")
    secs = st["words"] / 2.3
    if solo and pics < 4: warn.append(f"only {pics} pictures; a standalone Short wants 5-8 (one every 6-10 s)")
    if not solo and pics and secs / pics > 24: warn.append(f"one picture every {secs/pics:.0f}s; add pictures to [LIB] lines (aim <= 20s)")
    first = next((x for x in e["items"] if x["kind"] == "line"), None)
    if first and first["who"] == list(e["cast"])[0] and len(first["text"].split()) > 40: warn.append("first line is long; open with the insult itself")
    if re.search(r"\b(kill|murder|rape|suicide)\b", open(path).read(), re.I): errs.append("violent/sexual/suicide wording found")
    return st, errs, warn

if __name__ == "__main__":
    st, errs, warn = lint(sys.argv[1]); print(st)
    for w in warn: print("WARN", w)
    for x in errs: print("ERROR", x)
    sys.exit(1 if errs else 0)
