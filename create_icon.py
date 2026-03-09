"""
Generates icon.ico and dark installer wizard images for TXTDrop.
Run before building: python create_icon.py
"""
import os
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_font(size: int, bold: bool = False):
    candidates = [
        ("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
        ("C:/Windows/Fonts/calibrib.ttf"  if bold else "C:/Windows/Fonts/calibri.ttf"),
        ("C:/Windows/Fonts/arial.ttf"),
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default()


def _draw_t_logo(d: ImageDraw.ImageDraw, cx: int, cy: int, r: int,
                 circle_fill=(41, 128, 185), letter_fill="white"):
    """Draw a blue circle with a white T centred at (cx, cy) with radius r."""
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=circle_fill)
    bar_w, bar_h = int(r * 1.1), max(4, int(r * 0.22))
    stem_w       = max(3, int(r * 0.28))
    top_y        = cy - int(r * 0.52)
    # top bar
    d.rectangle([cx - bar_w // 2, top_y, cx + bar_w // 2, top_y + bar_h],
                fill=letter_fill)
    # stem
    d.rectangle([cx - stem_w // 2, top_y, cx + stem_w // 2, cy + int(r * 0.55)],
                fill=letter_fill)


# ── Icon ──────────────────────────────────────────────────────────────────────

def create_icon():
    size = 256
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d    = ImageDraw.Draw(img)

    margin = 10
    try:
        d.rounded_rectangle(
            [margin, margin, size - margin, size - margin],
            radius=40, fill=(41, 128, 185),
        )
    except AttributeError:
        d.rectangle([margin, margin, size - margin, size - margin],
                    fill=(41, 128, 185))

    d.rectangle([60,  55, 196,  85], fill="white")   # top bar
    d.rectangle([112, 55, 144, 200], fill="white")   # stem

    out = os.path.join(BASE_DIR, "icon.ico")
    img.save(out, format="ICO", sizes=[(256, 256), (48, 48), (32, 32), (16, 16)])
    print(f"  icon.ico")


# ── Installer wizard images ───────────────────────────────────────────────────

def create_wizard_images():
    """
    Generate dark-themed Inno Setup wizard images:
      wizard_large.bmp  — 164×314  (side banner on Welcome/Finish pages)
      wizard_small.bmp  —   55×55  (header logo on inner pages)
    """
    _BG      = (17, 17, 17)          # #111111
    _BLUE    = (41, 128, 185)        # #2980b9
    _GOLD    = (255, 214, 0)         # #ffd600
    _DIM     = (88, 88, 88)          # #585858
    _BORDER  = (56, 56, 56)          # #383838

    # ── Large (164 × 314) ─────────────────────────────────────────────────────
    W, H = 164, 314
    large = Image.new("RGB", (W, H), _BG)
    d     = ImageDraw.Draw(large)

    # Right-edge accent stripe
    d.rectangle([W - 3, 0, W - 1, H], fill=_BLUE)

    # Logo centred in upper third
    cx, cy, r = W // 2, 90, 34
    _draw_t_logo(d, cx, cy, r)

    # "TXTDrop" title
    f_title = _load_font(17, bold=True)
    f_sub   = _load_font(10)
    f_tiny  = _load_font(9)

    def _center_text(text, y, font, fill):
        bb = d.textbbox((0, 0), text, font=font)
        tw = bb[2] - bb[0]
        d.text(((W - tw) // 2, y), text, fill=fill, font=font)

    _center_text("TXTDrop",            cy + r + 16, f_title, _GOLD)
    _center_text("AI Clipboard Capture", cy + r + 38, f_sub,   _DIM)

    # Horizontal divider near bottom
    d.rectangle([18, H - 52, W - 18, H - 51], fill=_BORDER)
    _center_text("SVIL", H - 34, f_tiny, _BORDER)

    out_large = os.path.join(BASE_DIR, "wizard_large.bmp")
    large.save(out_large, format="BMP")
    print(f"  wizard_large.bmp")

    # ── Small (55 × 55) ───────────────────────────────────────────────────────
    SW, SH = 55, 55
    small = Image.new("RGB", (SW, SH), _BG)
    d2    = ImageDraw.Draw(small)
    _draw_t_logo(d2, SW // 2, SH // 2, 22)

    out_small = os.path.join(BASE_DIR, "wizard_small.bmp")
    small.save(out_small, format="BMP")
    print(f"  wizard_small.bmp")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Generating assets…")
    create_icon()
    create_wizard_images()
    print("Done.")
