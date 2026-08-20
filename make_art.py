#!/usr/bin/env python3
"""Rigenera art.json: l'avatar in ASCII a colori.

Due scelte non ovvie, entrambe imposte dalla sorgente.

1. Rampa stretta. Con la classica rampa a 70 caratteri la densita' segue la
   luminanza, e siccome la pelle occupa quasi tutto il fotogramma a un tono
   medio uniforme, il risultato e' rumore che copre il disegno. Qui la rampa e'
   di soli cinque glifi di peso simile (+ * # % @): i caratteri fanno texture,
   la forma la porta il colore.

2. Palette costruita a mano. Il mediancut assegna i colori in base a quanti
   pixel li usano: la pelle arancione se li prende tutti e l'azzurro dell'iride
   sparisce. Quindi il pixel piu' azzurro dell'immagine, il bianco e il nero
   sono riservati d'ufficio.

Uso:  python3 make_art.py [colonne] [righe]
Dip.: pillow
"""

import json
import sys
from PIL import Image

RAMP = "+*#%@"
RESERVED = ["#ffffff", "#000000"]
CHARSET = ("0123456789abcdefghijklmnopqrstuvwxyz"
           "ABCDEFGHIJKLMNOPQRSTUVWXYZ")


def bluest(im):
    """Il pixel piu' azzurro: l'iride."""
    best, score = None, -999
    for r, g, b in im.getdata():
        s = b - max(r, g)
        if s > score:
            best, score = (r, g, b), s
    return best


def build_palette(small, ncolors):
    q = small.quantize(colors=ncolors, method=Image.MEDIANCUT,
                       dither=Image.Dither.NONE)
    raw = q.getpalette()[: ncolors * 3]
    pal = [tuple(raw[i:i + 3]) for i in range(0, len(raw), 3)]
    pal.append(bluest(small))
    for h in RESERVED:
        pal.append(tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)))
    seen, out = set(), []
    for c in pal:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def nearest(px, palette):
    r, g, b = px
    best, bd = 0, None
    for i, (pr, pg, pb) in enumerate(palette):
        d = 2 * (r - pr) ** 2 + 4 * (g - pg) ** 2 + 3 * (b - pb) ** 2
        if bd is None or d < bd:
            best, bd = i, d
    return best


def render(path, cols, rows, ncolors=12):
    im = Image.open(path).convert("RGB")
    small = im.resize((cols, rows), Image.LANCZOS)
    palette = build_palette(small, ncolors)
    if len(palette) > len(CHARSET):
        raise SystemExit("palette troppo grande per il charset")
    rgb, lum = small.load(), small.convert("L").load()
    n = len(RAMP)
    text, color = [], []
    for y in range(rows):
        text.append("".join(RAMP[min(n - 1, lum[x, y] * n // 256)]
                            for x in range(cols)))
        color.append("".join(CHARSET[nearest(rgb[x, y], palette)]
                             for x in range(cols)))
    return {
        "cols": cols,
        "rows": rows,
        "palette": ["#%02x%02x%02x" % c for c in palette],
        "text": text,
        "color": color,
    }


if __name__ == "__main__":
    cols = int(sys.argv[1]) if len(sys.argv) > 1 else 80
    rows = int(sys.argv[2]) if len(sys.argv) > 2 else 42
    art = render("avatar.png", cols, rows)
    with open("art.json", "w", encoding="utf-8") as f:
        json.dump(art, f, indent=1)
    print(f"art.json: {cols}x{rows} caratteri, {len(art['palette'])} colori")
