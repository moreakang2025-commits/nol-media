"""Scene drawing. Every scene is draw(t, dur, spec, ctx) -> RGBA 1920x1080 image."""
import math, random, functools
from PIL import Image, ImageDraw
from common import (W, H, BG, PANEL, GRID, FG, DIM, YEL, RED, GREEN, BLUE, text_img, fit_text,
                    paste_center, paste_left, mascot, ease_out, ease_back, font)

@functools.lru_cache(maxsize=1)
def _bg():
    im = Image.new("RGBA", (W, H), BG + (255,)); d = ImageDraw.Draw(im)
    for y in range(120, H, 120): d.line([(0, y), (W, y)], fill=GRID, width=2)
    return im

def base():
    return _bg().copy()

def _src(im, text):
    if text: paste_left(im, text_img("Source: " + text, "reg", 26, DIM), 60, 40)

def _appear(t, i, n, dur, lead=0.3, span=0.6):
    """Item i of n appears spread over the first `span` of the scene."""
    start = lead + i * (max(0.4, dur * span) / max(1, n)); return ease_out((t - start) / 0.35)

def _shake(t, t0, amp=18):
    k = t - t0
    if k < 0 or k > 0.45: return 0, 0
    a = amp * (1 - k / 0.45)
    return int(a * math.sin(k * 90)), int(a * math.cos(k * 70))

def logo(t, dur, spec, ctx):
    im = base(); m = mascot("baby", 560)
    paste_center(im, m, W / 2, H / 2 - 60, scale=0.6 + 0.4 * ease_back(t / 0.6))
    paste_center(im, text_img("MONGKI MONEY", "heavy", 120, YEL, 6), W / 2, H - 170, alpha=ease_out((t - 0.4) / 0.4))
    return im

def smash(t, dur, spec, ctx):
    im = base(); d = ImageDraw.Draw(im)
    hit = 0.45
    if 0 <= t - hit < 0.12: d.rectangle([0, 0, W, H], fill=(120, 10, 20))
    rnd = random.Random(7)
    for k in range(14):
        x0, sp = rnd.uniform(0, W), rnd.uniform(200, 520); ang = rnd.uniform(-1, 1)
        y = (rnd.uniform(-300, H) + t * sp) % (H + 300) - 150
        bill = Image.new("RGBA", (130, 62), (0, 0, 0, 0)); bd = ImageDraw.Draw(bill)
        bd.rounded_rectangle([2, 2, 128, 60], 6, fill=GREEN, outline=(11, 107, 58), width=4); bd.ellipse([48, 14, 82, 48], fill=(11, 107, 58))
        im.alpha_composite(bill.rotate(ang * 40 + t * 60 * ang, expand=True), (int(x0), int(y)))
    dx, dy = _shake(t, hit)
    m = mascot("muscle", 860)
    rise = ease_out(t / hit); my = H + 300 - (H - 40) * rise
    im.alpha_composite(m, (int(W - m.width - 40 + dx), int(my - m.height + 520 + dy)))
    big = fit_text(spec["big"], "heavy", 230, 1180, YEL, 10)
    paste_center(im, big, 680 + dx, 420 + dy, scale=ease_back((t - hit) / 0.35))
    if spec.get("sub"):
        paste_center(im, fit_text(spec["sub"], "heavy", 120, 1180, FG, 8), 680 + dx, 640 + dy, alpha=ease_out((t - hit - 0.25) / 0.3))
    return im

def statcard(t, dur, spec, ctx):
    im = base()
    if spec.get("kicker"): paste_center(im, text_img(spec["kicker"].upper(), "bold", 48, DIM), W / 2, 220, alpha=ease_out(t / 0.3))
    paste_center(im, fit_text(spec["big"], "heavy", 260, 1700, YEL, 10), W / 2, 450, scale=ease_back((t - 0.15) / 0.4))
    lines = spec.get("lines", [])
    for i, ln in enumerate(lines):
        paste_center(im, fit_text(ln, "bold", 70, 1600, FG), W / 2, 680 + i * 95, alpha=_appear(t, i, len(lines), dur, lead=0.8))
    _src(im, spec.get("source")); return im

def tickers(t, dur, spec, ctx):
    im = base(); d = ImageDraw.Draw(im)
    paste_center(im, text_img(spec["title"].upper(), "heavy", 90, FG), W / 2, 120)
    items = spec["items"]; live = ctx.get("_event_moves") or {}
    for i, it in enumerate(items):
        chg = live.get(it["sym"]) if live.get(it["sym"]) is not None else it["chg"]
        a = _appear(t, i, len(items), dur, lead=0.3, span=0.75)
        if a <= 0: continue
        y = 300 + i * 175; col = GREEN if chg >= 0 else RED
        d.rounded_rectangle([260, y - 70, 1660, y + 70], 18, fill=PANEL)
        paste_left(im, fit_text(it.get("label", it["sym"]), "heavy", 110, 440, FG), 310, y, alpha=a)
        bw = int(min(abs(chg), 15) / 15 * 620 * a)
        d.rounded_rectangle([760, y - 34, 760 + max(bw, 8), y + 34], 10, fill=col)
        paste_left(im, text_img(f"{'+' if chg >= 0 else '−'}{abs(chg):.1f}%", "heavy", 100, col), 1420, y, alpha=a)
        if chg < 0 and a > 0.99:
            pulse = 0.5 + 0.5 * math.sin(t * 8)
            d.rounded_rectangle([250, y - 80, 1670, y + 80], 22, outline=RED, width=int(4 + 4 * pulse))
    _src(im, spec.get("source")); return im

def question(t, dur, spec, ctx):
    im = base(); lines = spec["lines"]
    for i, ln in enumerate(lines):
        a = _appear(t, i, len(lines), dur, lead=0.1, span=0.7)
        paste_center(im, fit_text(ln, "heavy", 150, 1700, YEL if i == len(lines) - 1 else FG, 6), W / 2, 300 + i * 220, scale=0.85 + 0.15 * a, alpha=a)
    return im

def title(t, dur, spec, ctx):
    im = base()
    paste_center(im, fit_text(spec["big"], "heavy", 210, 1750, YEL, 10), W / 2, 440, scale=ease_back(t / 0.45))
    if spec.get("sub"): paste_center(im, fit_text(spec["sub"], "bold", 80, 1600, FG), W / 2, 680, alpha=ease_out((t - 0.5) / 0.4))
    return im

def tiles(t, dur, spec, ctx):
    im = base(); d = ImageDraw.Draw(im); items = spec["items"]; n = len(items)
    tw, gap = 320, 30; x0 = (W - (n * tw + (n - 1) * gap)) / 2
    for i, it in enumerate(items):
        a = _appear(t, i, n, dur, lead=0.4, span=0.7)
        if a <= 0: continue
        x = x0 + i * (tw + gap); col = BLUE if it["color"] == "blue" else RED
        y = 330 + (1 - a) * 80
        d.rounded_rectangle([x, y, x + tw, y + 420], 24, fill=col)
        paste_center(im, text_img(it["value"], "heavy", 130, FG), x + tw / 2, y + 160, alpha=a)
        paste_center(im, fit_text(it["label"], "bold", 44, tw - 30, FG), x + tw / 2, y + 330, alpha=a)
    _src(im, spec.get("source")); return im

def timeline(t, dur, spec, ctx):
    im = base(); d = ImageDraw.Draw(im); items = spec["items"]; n = len(items)
    y = 520; x0, x1 = 200, 1720
    d.line([(x0, y), (x0 + (x1 - x0) * ease_out(t / (dur * 0.8)), y)], fill=YEL, width=10)
    for i, it in enumerate(items):
        a = _appear(t, i, n, dur, lead=0.3, span=0.75)
        if a <= 0: continue
        x = x0 + (x1 - x0) * (i + 0.5) / n; r = 26 * a
        d.ellipse([x - r, y - r, x + r, y + r], fill=YEL)
        paste_center(im, text_img(it["when"], "heavy", 80, YEL), x, y - 130, alpha=a)
        paste_center(im, fit_text(it["what"], "bold", 48, 360, FG), x, y + 120, alpha=a)
    return im

def twocol(t, dur, spec, ctx):
    im = base(); d = ImageDraw.Draw(im)
    for side, (x, col, key) in enumerate([(120, RED, "left"), (1000, GREEN, "right")]):
        a = ease_out((t - 0.2 - side * dur * 0.35) / 0.4)
        if a <= 0: continue
        d.rounded_rectangle([x, 160, x + 800, 900], 28, fill=PANEL, outline=col, width=6)
        paste_center(im, fit_text(spec[key + "_title"].upper(), "heavy", 90, 740, col), x + 400, 250, alpha=a)
        for i, ln in enumerate(spec[key]):
            b = ease_out((t - 0.5 - side * dur * 0.35 - i * 0.35) / 0.3)
            paste_left(im, fit_text("• " + ln, "bold", 64, 720, FG), x + 50, 410 + i * 120, alpha=b)
        paste_center(im, fit_text(spec[key + "_note"], "bold", 40, 740, DIM), x + 400, 840, alpha=a)
    return im

def election_bars(t, dur, spec, ctx):
    im = base(); d = ImageDraw.Draw(im); els = ctx.get("_elections", [])
    paste_center(im, text_img("TESLA AFTER BIG ELECTIONS", "heavy", 90, FG), W / 2, 110)
    paste_center(im, text_img("left bar: next day   ·   right bar: one month later", "reg", 32, DIM), W / 2, 190)
    zero = 520; scale = 9.0; n = max(1, len(els)); cw = 1600 / n
    d.line([(160, zero), (1760, zero)], fill=DIM, width=3)
    for i, e in enumerate(els):
        a = _appear(t, i, n, dur, lead=0.3, span=0.8); cx = 160 + cw * (i + 0.5)
        for j, k in enumerate(["d1", "d30"]):
            v = e.get(k); x = cx - 120 + j * 140
            if v is None:
                paste_center(im, text_img("TBD", "bold", 40, DIM), x + 50, zero - 40, alpha=a); continue
            h = max(-260, min(260, v * scale)) * a; col = GREEN if v >= 0 else RED
            d.rounded_rectangle([x, min(zero, zero - h), x + 100, max(zero, zero - h)], 8, fill=col)
            ty = zero - h - 40 if v >= 0 else zero - h + 40
            paste_center(im, text_img(f"{v:+.1f}%", "heavy", 50, col), x + 50, ty, alpha=a)
        paste_center(im, fit_text(e["label"], "bold", 46, cw - 20, FG), cx, 870, alpha=a)
    return im

def eventbars(t, dur, spec, ctx):
    """Bars for a list of past events: spec {data: ctx key, title, legend, keys: [..], max: 8, scale}."""
    im = base(); d = ImageDraw.Draw(im); ev = list(ctx.get(spec["data"], []))[-spec.get("max", 8):]
    keys = spec.get("keys", ["m1", "y1"])
    paste_center(im, fit_text(spec.get("title", "").upper(), "heavy", 90, 1700, FG), W / 2, 110)
    if spec.get("legend"): paste_center(im, text_img(spec["legend"], "reg", 32, DIM), W / 2, 190)
    vals = [abs(e[k]) for e in ev for k in keys if e.get(k) is not None] or [10]
    scale = spec.get("scale") or 250 / max(vals)
    zero = 540; n = max(1, len(ev)); cw = 1600 / n; bw = min(100, cw / (len(keys) + 1))
    d.line([(160, zero), (1760, zero)], fill=DIM, width=3)
    for i, e in enumerate(ev):
        a = _appear(t, i, n, dur, lead=0.3, span=0.8); cx = 160 + cw * (i + 0.5)
        for j, k in enumerate(keys):
            v = e.get(k); x = cx - (len(keys) * (bw + 10)) / 2 + j * (bw + 10)
            if v is None:
                paste_center(im, text_img("TBD", "bold", 34, DIM), x + bw / 2, zero - 40, alpha=a); continue
            h = max(-280, min(280, v * scale)) * a; col = GREEN if v >= 0 else RED
            d.rounded_rectangle([x, min(zero, zero - h), x + bw, max(zero, zero - h)], 8, fill=col)
            ty = zero - h - 36 if v >= 0 else zero - h + 36
            paste_center(im, fit_text(f"{v:+.0f}%", "heavy", 40, cw / len(keys) + 10, col), x + bw / 2, ty, alpha=a)
        import datetime as _dt
        lab = _dt.date.fromisoformat(e["date"]).strftime("%b %Y") if "date" in e else e.get("label", "")
        paste_center(im, fit_text(lab, "bold", 40, cw - 16, FG), cx, 880, alpha=a)
    _src(im, spec.get("source")); return im

def backtest(t, dur, spec, ctx):
    im = base(); d = ImageDraw.Draw(im)
    bt, cmp_, bspec = ctx.get("_bt"), ctx.get("_cmp"), ctx.get("_bt_spec", {})
    if not bt:
        return title(t, dur, {"big": "BACKTEST", "sub": "data missing"}, ctx)
    if spec.get("which") == "compare":
        paste_center(im, text_img("SAME $10 A DAY", "heavy", 90, FG), W / 2, 110)
        paste_center(im, text_img(f"Invested: ${bt['invested']:,.0f} each", "bold", 40, DIM), W / 2, 200)
        vals = [(bspec.get("ticker", "TSLA"), bt), (bspec.get("compare", "SPY"), cmp_)]
        top = max(v["value"] for _, v in vals)
        for i, (sym, v) in enumerate(vals):
            a = ease_out((t - 0.3 - i * 0.8) / 0.8); x = 560 + i * 520; hh = 480 * v["value"] / top * a
            col = YEL if i == 0 else BLUE
            d.rounded_rectangle([x, 820 - hh, x + 300, 820], 16, fill=col)
            paste_center(im, text_img(f"${v['value'] * a:,.0f}", "heavy", 76, FG), x + 150, 820 - hh - 55)
            paste_center(im, text_img(sym, "heavy", 64, col), x + 150, 870)
        return im
    curve = bt["curve"]; k = max(2, int(len(curve) * ease_out(t / (dur * 0.7))))
    pts = curve[:k]; vmax = max(c[2] for c in curve + [(0, bt["invested"], bt["invested"])]) * 1.05
    x0, x1, y0, y1 = 140, 1180, 950, 250
    X = lambda i: x0 + (x1 - x0) * i / (len(curve) - 1); Y = lambda v: y0 - (y0 - y1) * v / vmax
    d.line([(X(i), Y(c[1])) for i, c in enumerate(pts)], fill=DIM, width=5)
    d.line([(X(i), Y(c[2])) for i, c in enumerate(pts)], fill=YEL, width=8)
    paste_left(im, text_img("invested", "reg", 30, DIM), x0, y1 - 60); paste_left(im, text_img("worth", "bold", 30, YEL), x0 + 180, y1 - 60)
    cur = pts[-1]
    paste_center(im, text_img(f"$10 a day in {bspec.get('ticker','')}", "bold", 46, FG), 1540, 260)
    paste_center(im, text_img("PUT IN", "bold", 36, DIM), 1540, 380); paste_center(im, text_img(f"${cur[1]:,.0f}", "heavy", 96, FG), 1540, 460)
    paste_center(im, text_img("WORTH", "bold", 36, DIM), 1540, 590); paste_center(im, text_img(f"${cur[2]:,.0f}", "heavy", 120, YEL), 1540, 680)
    paste_center(im, text_img(f"since {bspec.get('start','')}", "reg", 32, DIM), 1540, 820)
    paste_left(im, text_img(f"Prices as of {bt['asof']} · adjusted closes · Yahoo Finance", "reg", 26, DIM), 60, 40)
    return im

def multibars(t, dur, spec, ctx):
    """Final value of the same $10/day in several tickers."""
    im = base(); d = ImageDraw.Draw(im)
    bt = ctx.get("_bt"); more = ctx.get("_dca_more", {}); bspec = ctx.get("_bt_spec", {})
    if not bt: return title(t, dur, {"big": "BACKTEST", "sub": "data missing"}, ctx)
    vals = [(bspec.get("ticker", "TSLA"), bt)] + list(more.items())
    paste_center(im, text_img(spec.get("title", "SAME $10 A DAY"), "heavy", 90, FG), W / 2, 110)
    paste_center(im, text_img(f"Invested: ${bt['invested']:,.0f} each", "bold", 40, DIM), W / 2, 200)
    top = max(v["value"] for _, v in vals) or 1; n = len(vals); bw = 260; gap = (1600 - n * bw) / max(1, n - 1)
    cols = [YEL, RED, BLUE, GREEN]
    for i, (sym, v) in enumerate(vals):
        a = ease_out((t - 0.3 - i * 0.6) / 0.7); x = 160 + i * (bw + gap); hh = 480 * v["value"] / top * a
        d.rounded_rectangle([x, 820 - hh, x + bw, 820], 16, fill=cols[i % 4])
        paste_center(im, text_img(f"${v['value'] * a:,.0f}", "heavy", 64, FG), x + bw / 2, 820 - hh - 50)
        paste_center(im, text_img(sym, "heavy", 60, cols[i % 4]), x + bw / 2, 870)
    return im

def lump(t, dur, spec, ctx):
    """What a lump sum would be worth now."""
    im = base(); L = ctx.get("_" + spec["key"])
    if not L: return title(t, dur, {"big": spec.get("kicker", ""), "sub": "data missing"}, ctx)
    paste_center(im, text_img(spec.get("kicker", "").upper(), "bold", 48, DIM), W / 2, 200)
    def fm(x): return f"${x / 1e6:,.1f}M" if x >= 1e6 else f"${x:,.0f}"
    paste_center(im, fit_text(f"{fm(L['cost'])} in {spec.get('label', L['ticker'])}", "heavy", 140, 1700, FG), W / 2, 360, scale=ease_back(t / 0.4))
    v = L["value"] * ease_out((t - 0.8) / 1.6)
    col = GREEN if L["value"] >= L["cost"] else RED
    paste_center(im, text_img("WORTH TODAY", "bold", 44, DIM), W / 2, 540)
    paste_center(im, fit_text(fm(v), "heavy", 220, 1700, col), W / 2, 690)
    paste_left(im, text_img(f"Prices as of {L['asof']} · Yahoo Finance", "reg", 26, DIM), 60, 40)
    return im

def cards(t, dur, spec, ctx):
    im = base(); d = ImageDraw.Draw(im); items = spec["items"]; n = len(items)
    cw, gap = 520, 50; x0 = (W - (n * cw + (n - 1) * gap)) / 2
    cols = [GREEN, YEL, RED]
    for i, it in enumerate(items):
        a = _appear(t, i, n, dur, lead=0.3, span=0.8)
        if a <= 0: continue
        x = x0 + i * (cw + gap); y = 220 + (1 - a) * 100
        d.rounded_rectangle([x, y, x + cw, y + 640], 28, fill=PANEL, outline=cols[i % 3], width=6)
        paste_center(im, text_img(it["n"], "heavy", 160, cols[i % 3]), x + cw / 2, y + 140, alpha=a)
        paste_center(im, fit_text(it["title"], "heavy", 90, cw - 40, FG), x + cw / 2, y + 320, alpha=a)
        words = it["text"].split(); mid = (len(words) + 1) // 2
        for j, ln in enumerate([" ".join(words[:mid]), " ".join(words[mid:])]):
            paste_center(im, fit_text(ln, "bold", 44, cw - 50, DIM), x + cw / 2, y + 450 + j * 60, alpha=a)
    return im

def end(t, dur, spec, ctx):
    im = base(); d = ImageDraw.Draw(im)
    m = mascot("baby", 460)
    im.alpha_composite(m, (90, int(360 + 12 * math.sin(t * 3))))
    a = ease_back(t / 0.5)
    d.rounded_rectangle([640, 170, 1180, 310], 70, fill=RED)
    paste_center(im, text_img("SUBSCRIBE", "heavy", 84, FG), 910, 240, scale=a)
    if spec.get("cta"):
        b = ease_out((t - 0.8) / 0.5)
        d.rounded_rectangle([600, 370, 1220, 700], 26, fill=PANEL, outline=YEL, width=6)
        paste_center(im, fit_text(spec["cta"], "heavy", 96, 560, YEL), 910, 470, alpha=b, scale=0.9 + 0.1 * b)
        words = spec.get("cta_sub", "").split(); mid = (len(words) + 1) // 2
        for j, ln in enumerate([" ".join(words[:mid]), " ".join(words[mid:])]):
            paste_center(im, fit_text(ln, "bold", 40, 560, FG), 910, 590 + j * 52, alpha=b)
    d.rounded_rectangle([1290, 300, 1850, 640], 18, outline=YEL, width=6)
    paste_center(im, text_img("NEXT VIDEO", "heavy", 52, YEL), 1570, 360)
    paste_center(im, fit_text(spec.get("next", ""), "bold", 38, 520, FG), 1570, 470)
    paste_center(im, text_img("Not financial advice. For education only.", "bold", 36, DIM), W / 2, 870)
    return im

SCENES = {f.__name__: f for f in [logo, smash, statcard, tickers, question, title, tiles, timeline, twocol,
                                  election_bars, backtest, cards, end, multibars, lump, eventbars]}

def caption_overlay(im, text):
    if not text: return
    d = ImageDraw.Draw(im); f = font("heavy", 64)
    w = d.textlength(text, font=f)
    while w > 1700 and f.size > 36:
        f = font("heavy", f.size - 4); w = d.textlength(text, font=f)
    x, y = (W - w) / 2, H - 120
    d.text((x, y), text, font=f, fill=FG, stroke_width=6, stroke_fill=(0, 0, 0))


def punch(im, k):
    """Jump-cut feel: alternate caption chunks get a slight zoom (pattern interrupt)."""
    if k % 2 == 0: return im
    s = 1.045; cw, ch = int(W / s), int(H / s); x, y = (W - cw) // 2, (H - ch) // 2
    return im.crop((x, y, x + cw, y + ch)).resize((W, H), Image.BILINEAR)

def progress(im, frac):
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 8], fill=(30, 36, 52)); d.rectangle([0, 0, int(W * max(0, min(1, frac))), 8], fill=YEL)
