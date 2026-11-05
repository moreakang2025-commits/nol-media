"""Shared paths, fonts, colors and small helpers for the Mongki Money pipeline."""
import os, functools
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ASSETS = os.path.join(ROOT, "mongki", "assets")
OFFLINE = os.environ.get("MONGKI_OFFLINE") == "1"

W, H, FPS = 1920, 1080, 30
BG = (11, 15, 26); PANEL = (22, 29, 46); GRID = (28, 36, 54)
FG = (240, 242, 246); DIM = (138, 147, 166)
YEL = (250, 204, 21); RED = (255, 46, 59); GREEN = (34, 197, 94); BLUE = (37, 99, 235)

def _first(paths):
    for p in paths:
        if os.path.exists(p):
            return p
    return None

FONT_HEAVY = _first([os.path.join(ASSETS, "fonts", "Anton-Regular.ttf"),
                     "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf",
                     "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf",
                     "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"])
FONT_BOLD = _first(["/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf",
                    os.path.join(ASSETS, "fonts", "Inter-Bold.ttf"),
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"])
FONT_REG = _first(["/usr/share/fonts/opentype/inter/Inter-Regular.otf",
                   os.path.join(ASSETS, "fonts", "Inter-Regular.ttf"),
                   "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"])

@functools.lru_cache(maxsize=256)
def font(kind, size):
    path = {"heavy": FONT_HEAVY, "bold": FONT_BOLD, "reg": FONT_REG}[kind]
    return ImageFont.truetype(path, size)

@functools.lru_cache(maxsize=512)
def text_img(text, kind, size, color, stroke=0, stroke_color=(0, 0, 0)):
    """Render text once to a transparent RGBA image (cached)."""
    f = font(kind, size)
    box = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textbbox((0, 0), text, font=f, stroke_width=stroke)
    w, h = box[2] - box[0] + 4, box[3] - box[1] + 4
    im = Image.new("RGBA", (max(w, 1), max(h, 1)), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((-box[0] + 2, -box[1] + 2), text, font=f, fill=color,
                            stroke_width=stroke, stroke_fill=stroke_color)
    return im

def fit_text(text, kind, size, max_w, color, stroke=0):
    while size > 20:
        im = text_img(text, kind, size, color, stroke)
        if im.width <= max_w:
            return im
        size = int(size * 0.92)
    return text_img(text, kind, size, color, stroke)

def paste_center(base, im, cx, cy, scale=1.0, alpha=1.0):
    if scale <= 0.01 or alpha <= 0.01:
        return
    if abs(scale - 1) > 0.01:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BICUBIC)
    if alpha < 0.99:
        im = im.copy(); im.putalpha(im.getchannel("A").point(lambda a: int(a * alpha)))
    base.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

def paste_left(base, im, x, cy, alpha=1.0):
    if alpha < 0.99:
        im = im.copy(); im.putalpha(im.getchannel("A").point(lambda a: int(a * alpha)))
    base.alpha_composite(im, (int(x), int(cy - im.height / 2)))

@functools.lru_cache(maxsize=8)
def mascot(name, width):
    """Mascot as RGBA at the given width, from the pre-rendered 1200px PNG (SVG kept as the source)."""
    im = Image.open(os.path.join(ASSETS, f"mongki_{name}.png")).convert("RGBA")
    return im.resize((width, int(im.height * width / im.width)), Image.LANCZOS)

def ease_out(t):
    t = max(0.0, min(1.0, t)); return 1 - (1 - t) ** 3

def ease_back(t):
    t = max(0.0, min(1.0, t)); c = 1.70158
    return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2

def pct_words(x):
    if x is None:
        return "still moving"
    return f"{'up' if x >= 0 else 'down'} {abs(x):.1f} percent"

def money(x):
    return f"${x:,.0f}"
