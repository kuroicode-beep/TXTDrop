"""
Generates icon.ico for use with PyInstaller.
Run this before building: python create_icon.py
"""
import os
from PIL import Image, ImageDraw


def create():
    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    margin = 10
    try:
        d.rounded_rectangle(
            [margin, margin, size - margin, size - margin],
            radius=40,
            fill=(41, 128, 185),
        )
    except AttributeError:
        d.rectangle(
            [margin, margin, size - margin, size - margin],
            fill=(41, 128, 185),
        )

    # White "T"
    d.rectangle([60, 55, 196, 85], fill="white")   # top bar
    d.rectangle([112, 55, 144, 200], fill="white")  # stem

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
    img.save(out, format="ICO", sizes=[(256, 256), (48, 48), (32, 32), (16, 16)])
    print(f"Created: {out}")


if __name__ == "__main__":
    create()
