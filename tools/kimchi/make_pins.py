"""Pinterest pins (1000x1500) + SEO title/description for every recipe.
Usage: python3 make_pins.py OUT_DIR [--ids 1,2]
Writes OUT_DIR/pins/pNNN.png and OUT_DIR/pins.json
"""
import json, glob, os, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
F = lambda n, s: ImageFont.truetype(os.path.join(HERE, "fonts", n), s)
W, H = 1000, 1500
DEEP = (94, 17, 23); GOLD = (176, 136, 75); PAPER = (245, 238, 225); INK = (29, 25, 20)
RED = (163, 35, 43); MUTE = (122, 111, 98); TINT = (237, 226, 207)
STORE = "nolnull.gumroad.com"
FREE = f"https://{STORE}/l/kimchi-free"; FULL = f"https://{STORE}/l/kimchi101"

def recipes():
    out = []
    for f in sorted(glob.glob(os.path.join(HERE, "data", "*.json"))):
        d = json.load(open(f, encoding="utf-8"))
        for r in d["recipes"]: r["_ch"] = d["chapter"]; out.append(r)
    return out

def wrap(d, text, font, maxw):
    words = text.split(); lines = []; cur = ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) > maxw and cur: lines.append(cur); cur = w
        else: cur = t
    lines.append(cur); return lines

def center(d, y, lines, font, fill, lh=1.15):
    for L in lines:
        d.text(((W - d.textlength(L, font=font)) / 2, y), L, font=font, fill=fill); y += int(font.size * lh)
    return y

def chili(d, x, y, s, on):
    col = RED if on else (217, 205, 184)
    d.polygon([(x, y + s * .55), (x + s * .35, y + s * .9), (x + s * .8, y + s * .55), (x + s, y), (x + s * .55, y + s * .3), (x + s * .15, y + s * .3)], fill=col)

def pin(r):
    im = Image.new("RGB", (W, H), PAPER); d = ImageDraw.Draw(im)
    # header block
    d.rectangle([0, 0, W, 560], fill=DEEP)
    d.rectangle([24, 24, W - 24, H - 24], outline=GOLD, width=3)
    center(d, 70, [f"RECIPE {r['id']} OF 101"], F("Playfair-700.ttf", 30), GOLD)
    fk = F("NanumMyeongjo-ExtraBold.ttf", 150)
    while d.textlength(r["ko"], font=fk) > W - 140: fk = F("NanumMyeongjo-ExtraBold.ttf", fk.size - 10)
    center(d, 140, [r["ko"]], fk, GOLD)
    fe = F("Playfair-900.ttf", 70); lines = wrap(d, r["en"], fe, W - 120)
    while len(lines) > 2: fe = F("Playfair-900.ttf", fe.size - 6); lines = wrap(d, r["en"], fe, W - 120)
    y = center(d, 330, lines, fe, PAPER, 1.1)
    if r["rom"].lower() != r["en"].lower():
        center(d, y + 6, [r["rom"]], F("PlayfairItalic-400.ttf", 34), (220, 200, 170))
    # hook
    fh = F("PlayfairItalic-700.ttf", 44); hl = wrap(d, r["hook"], fh, W - 140)[:3]
    y = center(d, 600, hl, fh, INK, 1.25)
    # meta row
    y += 26; fm = F("Playfair-700.ttf", 28)
    meta = f"{r['time'].upper()}   ·   READY {r['ready'].upper()}"
    ml = wrap(d, meta, fm, W - 160)[:2]; y = center(d, y, ml, fm, MUTE)
    cx = W / 2 - 60
    for i in range(3): chili(d, cx + i * 44, y + 10, 34, i < r["heat"])
    y += 70
    # ingredients box
    fi = F("GowunBatang-Regular.ttf", 32); box_top = y
    items = []
    for ing in r["ing"][:7]:
        items += wrap(d, "· " + ing, fi, W - 220)[:1]
    if len(r["ing"]) > 7: items.append(f"+ {len(r['ing']) - 7} more in the book")
    bh = 80 + len(items) * 44
    d.rounded_rectangle([70, box_top, W - 70, box_top + bh], radius=22, fill=TINT)
    d.text((110, box_top + 24), "YOU NEED", font=F("Playfair-900.ttf", 30), fill=RED)
    yy = box_top + 72
    for L in items: d.text((110, yy), L, font=fi, fill=INK); yy += 44
    # footer CTA
    d.rectangle([24, H - 230, W - 24, H - 24], fill=DEEP)
    center(d, H - 205, ["FULL STEP-BY-STEP RECIPE"], F("Playfair-700.ttf", 30), GOLD)
    center(d, H - 160, ["Grandma Lee's 101 Kimchi Recipes"], F("Playfair-900.ttf", 46), PAPER)
    center(d, H - 95, ["5 recipes free  →  link on this pin"], F("PlayfairItalic-400.ttf", 32), (220, 200, 170))
    return im

def seo(r):
    heat = ["no-chili", "mild", "spicy", "extra spicy"][r["heat"]]
    kind = "Easy Korean Kimchi Recipe" if "kimchi" in r["en"].lower() else "Easy Korean Recipe"
    title = f"{r['en']} ({r['ko']}) | {kind}"
    if len(title) > 100: title = f"{r['en']} | Korean Kimchi Recipe"[:100]
    tags = " ".join(f"#{t.replace('-', '').replace(' ', '')}" for t in r.get("tags", [])[:3])
    desc = (f"{r['hook']} {r['en']} ({r['rom']}) is a {heat} Korean recipe, {r['time']}. "
            f"Recipe {r['id']} of Grandma Lee's 101 Kimchi Recipes, from royal palace kimchi to Seoul street food. "
            f"Get 5 recipes free. #kimchi #koreanfood #koreanrecipes #kfood {tags}")
    return title[:100], desc[:500]

def main():
    out = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "pinterest"
    ids = None
    if "--ids" in sys.argv: ids = {int(x) for x in sys.argv[sys.argv.index("--ids") + 1].split(",")}
    os.makedirs(f"{out}/pins", exist_ok=True); rows = []
    for r in recipes():
        if ids and r["id"] not in ids: continue
        p = f"{out}/pins/p{r['id']:03d}.png"; pin(r).save(p, optimize=True)
        t, dsc = seo(r)
        rows.append({"id": r["id"], "image": p, "title": t, "description": dsc,
                     "link": FREE if r["id"] % 3 else FULL, "board": r["_ch"]["en"]})
    json.dump(rows, open(f"{out}/pins.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(len(rows), "pins ->", out)

if __name__ == "__main__":
    main()
