"""Pinterest sales layer for Grandma Lee's 101 Kimchi Recipes.

python3 tools/kimchi/make_sales.py footers   -> repaints the footer of every recipe pin in kimchi/pins/
                                               (paid link for 2 of 3 pins, free sampler for the rest)
python3 tools/kimchi/make_sales.py sales     -> writes kimchi/sales/sNN.png (product pins, 1000x1500)
python3 tools/kimchi/make_sales.py queue     -> rebuilds kimchi/pins.json from next_index on:
                                               recipe, recipe, product, recipe, recipe, product, ...
All facts come from the Gumroad listing (101 recipes, 9 chapters, 117 pages, $19, instant PDF).
"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = "https://raw.githubusercontent.com/moreakang2025-commits/nol-media/main/"
FULL = "https://nolnull.gumroad.com/l/kimchi101"
FREE = "https://nolnull.gumroad.com/l/kimchi-free"
PRICE = "$19"
W, H = 1000, 1500
DEEP = (94, 17, 23); DEEP2 = (74, 12, 18); GOLD = (176, 136, 75); GOLD2 = (214, 178, 118)
PAPER = (245, 238, 225); INK = (29, 25, 20); RED = (163, 35, 43); MUTE = (122, 111, 98); TINT = (237, 226, 207)
SERIF = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"
SERIFB = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Black.ttc"
SERIFR = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc"
INTER = "/usr/share/fonts/truetype/inter/Inter-SemiBold.ttf"
INTERB = "/usr/share/fonts/truetype/inter/Inter-Bold.ttf"
INTERR = "/usr/share/fonts/truetype/inter/Inter-Regular.ttf"


def F(p, s):
    for cand in (p, p.replace("truetype/inter", "opentype/inter").replace(".ttf", ".otf")):
        if os.path.exists(cand):
            return ImageFont.truetype(cand, int(s), index=1 if cand.endswith(".ttc") else 0)
    import glob
    hit = glob.glob(f"/usr/share/fonts/**/{os.path.basename(p).split('.')[0]}*", recursive=True)
    return ImageFont.truetype(hit[0], int(s))


def tw(d, t, f): return d.textlength(t, font=f)


def wrap(d, text, f, maxw):
    out = []
    for para in text.split("\n"):
        cur = ""
        for w in para.split():
            t = (cur + " " + w).strip()
            if tw(d, t, f) > maxw and cur: out.append(cur); cur = w
            else: cur = t
        out.append(cur)
    return out


def ctext(d, y, lines, f, fill, lh=1.2, cx=W / 2, track=0):
    for L in lines:
        if track:
            total = sum(tw(d, ch, f) for ch in L) + track * (len(L) - 1); x = cx - total / 2
            for ch in L: d.text((x, y), ch, font=f, fill=fill); x += tw(d, ch, f) + track
        else:
            d.text((cx - tw(d, L, f) / 2, y), L, font=f, fill=fill)
        y += int(f.size * lh)
    return y


# ---------- book cover + mockup ----------
def jar(d, cx, top, s, fill, rim):
    """simple onggi (kimchi crock) silhouette"""
    w = s; h = s * 1.05
    d.ellipse([cx - w * .5, top + h * .12, cx + w * .5, top + h * .98], fill=fill)
    d.rectangle([cx - w * .28, top + h * .02, cx + w * .28, top + h * .2], fill=fill)
    d.rounded_rectangle([cx - w * .33, top - h * .02, cx + w * .33, top + h * .08], radius=int(s * .04), fill=rim)
    d.ellipse([cx - w * .1, top + h * .45, cx + w * .1, top + h * .6], fill=RED)


def cover(cw=600, ch=857):
    im = Image.new("RGB", (cw, ch), DEEP); d = ImageDraw.Draw(im); k = cw / 600
    d.rectangle([14 * k, 14 * k, cw - 14 * k, ch - 14 * k], outline=GOLD, width=max(2, int(2 * k)))
    y = ctext(d, 60 * k, ["KOREAN ROYAL"], F(INTER, 20 * k), GOLD2, cx=cw / 2, track=4 * k)
    y = ctext(d, y + 4 * k, ["GRANDMA LEE'S"], F(SERIF, 44 * k), PAPER, cx=cw / 2)
    y = ctext(d, y - 6 * k, ["101"], F(SERIFB, 170 * k), GOLD2, lh=1.08, cx=cw / 2)
    y = ctext(d, y + 4 * k, ["KIMCHI RECIPES"], F(SERIF, 46 * k), PAPER, cx=cw / 2)
    y = ctext(d, y + 10 * k, ["From the King's Table", "to Seoul's Hottest Kitchens"], F(SERIFR, 22 * k), GOLD2, cx=cw / 2)
    jar(d, cw / 2, y + 40 * k, 150 * k, DEEP2, GOLD)
    ctext(d, ch - 70 * k, ["117 PAGES  ·  INSTANT PDF"], F(INTER, 17 * k), GOLD2, cx=cw / 2, track=3 * k)
    return im


def book(cw=520):
    c = cover(cw, int(cw * 1.4286))
    pad = 40; bw, bh = c.width + 26 + pad * 2, c.height + pad * 2 + 20
    canvas = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    sh = Image.new("RGBA", (bw, bh), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    sd.rounded_rectangle([pad + 18, pad + 22, pad + c.width + 30, pad + c.height + 18], radius=10, fill=(40, 20, 10, 150))
    sh = sh.filter(ImageFilter.GaussianBlur(16)); canvas.alpha_composite(sh)
    d = ImageDraw.Draw(canvas)
    for i in range(10):  # page block
        d.rectangle([pad + c.width - 4 + i * 2, pad + 6 + i, pad + c.width + i * 2, pad + c.height - 2 - i], fill=(250 - i * 3, 246 - i * 3, 236 - i * 3, 255))
    canvas.paste(c, (pad, pad))
    sp = Image.new("RGBA", (16, c.height), (0, 0, 0, 0)); spd = ImageDraw.Draw(sp)
    for x in range(16): spd.line([(x, 0), (x, c.height)], fill=(0, 0, 0, int(70 * (1 - x / 16))))
    canvas.alpha_composite(sp, (pad, pad))
    return canvas


# ---------- shared pieces ----------
def frame(bg=PAPER):
    im = Image.new("RGB", (W, H), bg); d = ImageDraw.Draw(im)
    d.rectangle([24, 24, W - 24, H - 24], outline=GOLD, width=3)
    return im, d


def buy_band(im, d, line2="All 101 recipes  ·  instant PDF", y0=H - 250):
    d.rectangle([24, y0, W - 24, H - 24], fill=DEEP)
    ctext(d, y0 + 30, ["GRANDMA LEE'S 101 KIMCHI RECIPES"], F(INTER, 26), GOLD2, track=3)
    pf = F(SERIFB, 92); label = PRICE; lw = tw(d, label, pf)
    ctext(d, y0 + 62, [label], pf, PAPER, lh=1.0)
    ctext(d, y0 + 170, [line2], F(SERIFR, 32), (226, 206, 176))


def headline(d, y, text, size, fill=INK, maxw=W - 140, font=SERIFB, lh=1.12, maxlines=4):
    f = F(font, size); L = wrap(d, text, f, maxw)
    while len(L) > maxlines and size > 40:
        size -= 4; f = F(font, size); L = wrap(d, text, f, maxw)
    return ctext(d, y, L, f, fill, lh=lh)


def kicker(d, y, text, fill=RED): return ctext(d, y, [text.upper()], F(INTERB, 26), fill, track=4)


def paste_book(im, x, y, cw):
    b = book(cw); im.paste(b, (int(x - b.width / 2), int(y)), b); return y + b.height


def thumb(pid, w):
    p = Image.open(os.path.join(ROOT, f"kimchi/pins/p{pid:03d}.png")).convert("RGB")
    p = p.resize((w, int(w * 1.5)), Image.LANCZOS)
    m = Image.new("L", p.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, p.width - 1, p.height - 1], radius=14, fill=255)
    out = Image.new("RGBA", p.size); out.paste(p, (0, 0), m); return out


def bullets(d, x, y, items, f, fill=INK, dot=RED, gap=1.45):
    for t in items:
        d.ellipse([x, y + f.size * .38, x + 14, y + f.size * .38 + 14], fill=dot)
        for i, L in enumerate(wrap(d, t, f, W - x - 110)):
            d.text((x + 34, y), L, font=f, fill=fill); y += int(f.size * 1.2)
        y += int(f.size * (gap - 1.2))
    return y


# ---------- product pins ----------
def s_hero():
    im, d = frame(); kicker(d, 80, "The kimchi cookbook")
    y = headline(d, 130, "101 Kimchi Recipes, From the King's Table to Seoul Today", 74)
    y = paste_book(im, W / 2, y + 10, 400)
    ctext(d, y - 10, ["11 royal  ·  every classic  ·  vegan  ·  no-chili  ·  30-minute"], F(INTER, 27), MUTE)
    buy_band(im, d); return im


def s_beginner():
    im, d = frame(); kicker(d, 80, "Never made kimchi?")
    y = headline(d, 130, "Start Here. Real Kimchi, Even Your First Time.", 72)
    f = F(SERIF, 38); y += 30
    steps = [("1", "30-minute jar kimchi", "supermarket vegetables, ready tonight"),
             ("2", "No napa cabbage?", "recipe 23 uses green cabbage"),
             ("3", "Scared of spice?", "a whole chapter with zero chili")]
    for n, a, b in steps:
        d.ellipse([110, y, 180, y + 70], fill=RED); ctext(d, y + 6, [n], F(SERIFB, 44), PAPER, cx=145)
        d.text((210, y - 4), a, font=f, fill=INK); d.text((210, y + 46), b, font=F(INTERR, 28), fill=MUTE); y += 140
    paste_book(im, W / 2 + 230, y - 60, 230)
    buy_band(im, d, "Step-by-step  ·  instant PDF"); return im


def s_inside():
    im, d = frame(); kicker(d, 80, "What's inside")
    y = headline(d, 130, "9 Chapters of Kimchi", 76)
    ch = ["The Palace Table: 11 royal court kimchi", "Grandma Lee's Classics", "The Eight Provinces",
          "Water & White: zero-chili kimchi", "30-Minute Kimchi", "Plant-Based & New Wave",
          "Cook With It: stew, fried rice, pancakes", "Seoul Right Now", "Grandma Lee's Pantry + fermentation guide"]
    f = F(SERIF, 33); y += 24
    for i, t in enumerate(ch, 1):
        d.text((90, y), f"{i:02d}", font=F(INTERB, 30), fill=RED); d.text((160, y - 4), t, font=f, fill=INK)
        y += 64
        d.line([(160, y - 14), (W - 90, y - 14)], fill=TINT, width=2)
    buy_band(im, d, "117 pages  ·  instant PDF"); return im


def s_collage(ids, head, kick):
    im, d = frame(DEEP); kicker(d, 74, kick, GOLD2)
    y = headline(d, 120, head, 66, PAPER)
    tw_ = 400; gap = 30; x0 = (W - 2 * tw_ - gap) // 2; y += 16
    for i, pid in enumerate(ids[:4]):
        t = thumb(pid, tw_); x = x0 + (i % 2) * (tw_ + gap); yy = y + (i // 2) * (int(tw_ * 1.5 * .55) + gap)
        crop = t.crop((0, 0, tw_, int(tw_ * 1.5 * .55)))
        im.paste(crop, (x, yy), crop)
    d.rectangle([24, H - 250, W - 24, H - 24], fill=PAPER)
    ctext(d, H - 228, ["101 RECIPES LIKE THESE"], F(INTER, 26), RED, track=3)
    ctext(d, H - 192, [PRICE], F(SERIFB, 92), INK, lh=1.0)
    ctext(d, H - 82, ["Grandma Lee's 101 Kimchi Recipes  ·  instant PDF"], F(SERIFR, 30), MUTE)
    return im


def s_topic(kick, head, items, line2, cw=300):
    im, d = frame(); kicker(d, 80, kick)
    y = headline(d, 130, head, 74)
    y = bullets(d, 100, y + 40, items, F(SERIF, 42))
    room = (H - 250) - y - 10
    cw = int(min(430, (room - 100) / 1.4286))
    paste_book(im, W / 2, y - 10, cw)
    buy_band(im, d, line2); return im


def s_gift():
    im, d = frame(DEEP); kicker(d, 80, "Gift idea for foodies", GOLD2)
    y = headline(d, 130, "The Kimchi Cookbook They'll Actually Use", 74, PAPER)
    y = paste_book(im, W / 2, y + 10, 400)
    ctext(d, y - 6, ["Instant PDF  ·  no shipping  ·  print it or read on a phone"], F(INTER, 27), GOLD2)
    d.rectangle([24, H - 250, W - 24, H - 24], fill=PAPER)
    ctext(d, H - 228, ["GRANDMA LEE'S 101 KIMCHI RECIPES"], F(INTER, 26), RED, track=3)
    ctext(d, H - 192, [PRICE], F(SERIFB, 92), INK, lh=1.0)
    ctext(d, H - 82, ["Send it as a gift at checkout"], F(SERIFR, 30), MUTE)
    return im


SALES = [
    ("s01", s_hero, "101 Kimchi Recipes Cookbook (PDF) | From the King's Table to Seoul Today",
     "The complete kimchi cookbook: 101 recipes in one 117-page PDF. 11 royal court kimchi, every classic (napa, kkakdugi, stuffed cucumber), all eight provinces, vegan kimchi, no-chili water kimchi and 30-minute kimchi. Instant download, $19. #kimchi #kimchirecipe #koreancookbook #koreanfood #fermentation"),
    ("s02", s_beginner, "How to Make Kimchi for Beginners | Easy Kimchi Cookbook PDF",
     "Never made kimchi? Start with a 30-minute jar kimchi from supermarket vegetables, green-cabbage kimchi when there's no napa, and a whole no-chili chapter. Grandma Lee's 101 Kimchi Recipes, instant PDF, $19. #kimchiforbeginners #easykimchi #howtomakekimchi #koreanrecipes"),
    ("s03", s_inside, "Kimchi Cookbook: 9 Chapters, 101 Recipes | What's Inside",
     "Palace kimchi, Grandma Lee's classics, the eight provinces, water & white kimchi, 30-minute kimchi, plant-based & new wave, cooking with kimchi, Seoul right now, and a pantry + fermentation guide. 117-page PDF, $19. #kimchi #koreancookbook #fermentedfoods #koreanfood"),
    ("s04", lambda: s_collage([12, 3, 61, 70], "Classic to Brand-New: 101 Kimchi Recipes", "One book"),
     "101 Kimchi Recipes: Napa Kimchi, Dongchimi, Basil Kimchi, Kimchi Stew",
     "From whole napa kimchi and ice-cold dongchimi to basil kimchi and kimchi stew. All 101 recipes in Grandma Lee's 101 Kimchi Recipes, instant PDF, $19. #kimchi #koreanfood #kimchistew #dongchimi #koreanrecipes"),
    ("s05", lambda: s_topic("No chili? Still kimchi.", "Zero-Chili Kimchi Recipes for Spice-Shy Eaters",
                            ["White kimchi and water kimchi", "Ice-cold dongchimi broth", "Kid-friendly, still fermented"], "Whole no-chili chapter  ·  instant PDF"),
     "Non-Spicy Kimchi Recipes: White Kimchi & Water Kimchi | Cookbook PDF",
     "Can't handle spice? A whole chapter of zero-chili kimchi: white kimchi, water kimchi and ice-cold dongchimi. Part of Grandma Lee's 101 Kimchi Recipes, instant PDF, $19. #whitekimchi #waterkimchi #nonspicy #kimchi #koreanfood"),
    ("s06", lambda: s_topic("Plant-based", "Vegan Kimchi That Tastes Like the Real Thing",
                            ["No fish sauce, no shrimp", "Shiitake-kelp umami base", "Basil and tangerine kimchi too"], "Whole vegan chapter  ·  instant PDF"),
     "Vegan Kimchi Recipes (No Fish Sauce) | Plant-Based Kimchi Cookbook",
     "A whole plant-based chapter: vegan kimchi with a shiitake-kelp umami base, plus new-wave basil and tangerine kimchi. Grandma Lee's 101 Kimchi Recipes, instant PDF, $19. #vegankimchi #plantbased #veganrecipes #kimchi #koreanfood"),
    ("s07", lambda: s_collage([86, 87, 72, 48], "Seoul Right Now: Kimchi Grilled Cheese, Carbonara & More", "Cook with kimchi"),
     "Kimchi Grilled Cheese, Kimchi Carbonara, Kimchi Pancake | 101 Recipes",
     "What Seoul is eating right now: kimchi grilled cheese, kimchi carbonara, crispy kimchi pancakes and 30-minute jar kimchi. All in Grandma Lee's 101 Kimchi Recipes, instant PDF, $19. #kimchirecipes #fusionfood #kimchipancake #koreanfood"),
    ("s08", s_gift, "Kimchi Cookbook Gift for Foodies | Instant PDF, No Shipping",
     "A gift for the friend who ferments, loves K-dramas or loves Korean food: Grandma Lee's 101 Kimchi Recipes. 117-page PDF, instant delivery, send it as a gift at checkout. $19. #foodiegift #giftideas #koreancookbook #kimchi #christmasgift"),
    ("s09", lambda: s_topic("Kimchi tonight", "30-Minute Kimchi With Supermarket Vegetables",
                            ["Real kimchi flavor by dinner", "No Korean market needed", "Swaps for every ingredient"], "Whole 30-minute chapter  ·  instant PDF"),
     "Quick Kimchi Recipes (30 Minutes) | Easy Kimchi Cookbook PDF",
     "Kimchi tonight: a whole chapter of 30-minute kimchi with supermarket vegetables and swaps for every ingredient. Grandma Lee's 101 Kimchi Recipes, instant PDF, $19. #quickrecipes #easykimchi #kimchi #koreanrecipes"),
    ("s10", lambda: s_topic("From the royal court", "11 Kimchi From Korea's Royal Palace Table",
                            ["Built on documented Joseon court cuisine", "3 served at the king's table", "Adapted for home kitchens"], "Palace chapter  ·  instant PDF"),
     "Royal Korean Court Kimchi Recipes | Joseon Palace Food Cookbook",
     "Chapter 1 is built on kimchi recorded at the Joseon royal court, adapted for home kitchens: 11 palace kimchi including the 3 served at the king's table. Grandma Lee's 101 Kimchi Recipes, $19. #koreanroyalcuisine #kimchi #koreanhistory #koreanfood"),
    ("s11", lambda: s_topic("Cook what you watch", "The Kimchi on Every K-Drama Dinner Table",
                            ["Kimchi stew from the late-night scenes", "Whole napa kimchi, the classic", "Kimchi fried rice and pancakes"], "Make it at home  ·  instant PDF"),
     "K-Drama Food at Home: Kimchi Recipes You See On Screen",
     "You've seen it on every K-drama dinner table. Make kimchi stew, whole napa kimchi, kimchi fried rice and pancakes at home. Grandma Lee's 101 Kimchi Recipes, instant PDF, $19. #kdramafood #kdrama #koreanfood #kimchi"),
    ("s12", lambda: s_topic("Fermentation guide", "When Is Kimchi Ready? When Is It Too Sour?",
                            ["A full fermentation guide", "Salting and rice paste basics", "Grandma Lee's master seasoning"], "Pantry chapter  ·  instant PDF"),
     "Kimchi Fermentation Guide: How Long, How Sour, How to Store",
     "When is kimchi ready, when is it too sour, and how to store it. Grandma Lee's pantry chapter covers salting, rice paste, master seasoning and fermentation. In the 101 Kimchi Recipes PDF, $19. #fermentation #kimchi #fermentedfoods #guthealth"),
]


def make_sales():
    os.makedirs(os.path.join(ROOT, "kimchi/sales"), exist_ok=True); rows = []
    for sid, fn, title, desc in SALES:
        p = f"kimchi/sales/{sid}.png"; fn().save(os.path.join(ROOT, p), optimize=True)
        rows.append(dict(id=sid, image=p, image_url=RAW + p, title=title[:100], description=desc[:500], link=FULL,
                         alt=f"Pin for Grandma Lee's 101 Kimchi Recipes cookbook PDF: {title.split('|')[0].strip()}"))
        print(sid, title)
    json.dump(rows, open(os.path.join(ROOT, "kimchi/sales.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


# ---------- recipe pin footer ----------
def is_free(pid): return pid % 3 == 2


def footer(pid):
    path = os.path.join(ROOT, f"kimchi/pins/p{pid:03d}.png")
    im = Image.open(path).convert("RGB"); d = ImageDraw.Draw(im)
    d.rectangle([24, H - 230, W - 24, H - 24], fill=DEEP)
    if is_free(pid):
        ctext(d, H - 208, ["FREE PDF  ·  5 RECIPES"], F(INTER, 26), GOLD2, track=3)
        ctext(d, H - 166, ["Grandma Lee's 101 Kimchi Recipes"], F(SERIFB, 46), PAPER)
        ctext(d, H - 96, ["Tap the pin to get 5 recipes free"], F(SERIFR, 32), (226, 206, 176))
    else:
        ctext(d, H - 210, ["THE FULL RECIPE IS IN THE BOOK"], F(INTER, 26), GOLD2, track=3)
        ctext(d, H - 172, ["Grandma Lee's 101 Kimchi Recipes"], F(SERIFB, 46), PAPER)
        chip_f = F(SERIFB, 40); txt = f"{PRICE}  ·  instant PDF  ·  tap to get it"
        w_ = tw(d, txt, chip_f) + 60
        d.rounded_rectangle([W / 2 - w_ / 2, H - 108, W / 2 + w_ / 2, H - 46], radius=31, fill=GOLD)
        ctext(d, H - 103, [txt], chip_f, DEEP2)
    im.save(path, optimize=True)


def make_footers():
    pins = json.load(open(os.path.join(ROOT, "kimchi/pins.json"), encoding="utf-8"))
    ids = sorted({p["id"] for p in pins if isinstance(p["id"], int)})
    for i in ids: footer(i)
    print(len(ids), "footers")


# ---------- queue ----------
def seo_desc(desc, free):
    desc = desc.replace("Get 5 kimchi recipes free at the link.", "").replace("Get all 101 recipes at the link.", "").strip()
    desc = " ".join(desc.split())
    tail = "Get 5 recipes free at the link." if free else f"Full recipe in the cookbook: all 101 recipes, instant PDF, {PRICE}."
    base, tags = desc.split(" #", 1) if " #" in desc else (desc, "kimchi #koreanfood")
    return f"{base} {tail} #{tags} #koreancookbook"[:500]


def make_queue():
    pj = os.path.join(ROOT, "kimchi/pins.json"); st = json.load(open(os.path.join(ROOT, "kimchi/state.json")))
    pins = json.load(open(pj, encoding="utf-8")); sales = json.load(open(os.path.join(ROOT, "kimchi/sales.json"), encoding="utf-8"))
    head = pins[:st["next_index"]]
    recipes = [p for p in pins[st["next_index"]:] if isinstance(p["id"], int)]
    for p in [q for q in pins if isinstance(q["id"], int)]:
        free = is_free(p["id"]); p["link"] = FREE if free else FULL
        p["description"] = seo_desc(p["description"], free)
        p["alt"] = p["alt"].split(", ingredients")[0].split(" with ingredients")[0] + (", ingredients, and a free 5-recipe sampler" if free else f", ingredients, and the 101-recipe cookbook PDF ({PRICE})")
    out, si = [], 0
    for i, p in enumerate(recipes):
        out.append(p)
        if i % 2 == 1 and si < len(sales): out.append(sales[si]); si += 1
    out += sales[si:]
    json.dump(head + out, open(pj, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("queue", len(head), "+", len(out), "| sales placed", len(sales))


if __name__ == "__main__":
    {"footers": make_footers, "sales": make_sales, "queue": make_queue}[sys.argv[1]]()
