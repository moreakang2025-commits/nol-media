"""Generate the reusable picture library (only what is missing) and write fps/library/catalog.md.
usage: python3 tools/fps/library.py [--limit N]"""
import os, re, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import images as IM

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
LIB = os.path.join(ROOT, "fps", "library")
REF, IMG = os.path.join(LIB, "ref"), os.path.join(LIB, "img")

def parse():
    roles, imgs = {}, []
    for raw in open(os.path.join(LIB, "library.txt"), encoding="utf-8"):
        s = raw.strip()
        if not s or s.startswith("#"): continue
        kind, _, rest = s.partition(" "); key, _, val = rest.partition("|")
        if kind == "ROLE": roles[key.strip()] = val.strip()
        elif kind == "IMG": imgs.append((key.strip(), val.strip()))
    return roles, imgs

LABEL = {"grandma": "the grandmother", "grandpa": "the grandfather", "son": "the son", "dil": "the daughter-in-law",
         "daughter": "the daughter", "sil": "the son-in-law", "grandson": "the grandson", "granddaughter": "the granddaughter",
         "lawyer": "the lawyer", "realtor": "the real estate agent", "nurse": "the nurse", "friend": "the old friend", "banker": "the banker",
         "dog": "the old dog", "youngman": "the young man", "neighbor": "the old neighbor", "kidboy": "the little boy",
         "kidgirl": "the little girl", "mom": "the young mother", "widow": "the widow"}

def ref_image(key):
    p = os.path.join(REF, f"{key}.jpg")
    return Image.open(p).convert("RGB") if os.path.exists(p) else None

def main():
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else 10 ** 6
    os.makedirs(REF, exist_ok=True); os.makedirs(IMG, exist_ok=True)
    roles, imgs = parse(); made = 0
    for key, look in roles.items():
        p = os.path.join(REF, f"{key}.jpg")
        if os.path.exists(p): continue
        im = IM.generate(f"Head-and-shoulders portrait photo of {look}. Neutral expression, plain softly lit background, "
                         "looking slightly off camera.", ratio="3:4", tag=f"libref_{key}")
        if im: im.thumbnail((900, 1200)); im.save(p, quality=88); made += 1
    for iid, prompt in imgs:
        p = os.path.join(IMG, f"{iid}.jpg")
        if os.path.exists(p) or made >= limit: continue
        keys = re.findall(r"\{(\w+)\}", prompt)
        text = re.sub(r"\{(\w+)\}", lambda m: LABEL.get(m.group(1), m.group(1)), prompt)
        refs = [(LABEL[k], ref_image(k)) for k in dict.fromkeys(keys) if k in LABEL and ref_image(k) is not None][:3]
        im = IM.generate(text, refs, tag=f"lib_{iid}")
        if im:
            im = im.resize((1600, int(1600 * im.height / im.width)), Image.LANCZOS); im.save(p, quality=85); made += 1
    with open(os.path.join(LIB, "catalog.md"), "w") as f:
        f.write("# Picture library catalog (use in episodes as `[LIB] id id ...`)\n\n")
        f.write("Recurring faces: " + ", ".join(f"{k} ({LABEL[k]})" for k in roles) + "\n\n")
        for iid, prompt in imgs:
            ok = "" if os.path.exists(os.path.join(IMG, f"{iid}.jpg")) else " (MISSING)"
            f.write(f"- `{iid}`{ok}: {prompt}\n")
    have = sum(os.path.exists(os.path.join(IMG, f"{i}.jpg")) for i, _ in imgs)
    print(f"[library] made {made} now; {have}/{len(imgs)} scene pictures, {len(os.listdir(REF))}/{len(roles)} faces")

if __name__ == "__main__":
    main()
