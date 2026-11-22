"""news-image-20261121 v5 — "THE DAY IN PICTURES".

Pure Python stdlib program. Draws a 1024x1024 picture-led front page summing
up Saturday 21 November 2026's world news and writes it to
$MAKEFUN_OUTPUT_DIR/entry.png (default /output/entry.png).

Deterministic: no randomness, no time, no network. Written from scratch in
this session for the make.fun news-image-20261121 bounty.
"""
import binascii
import math
import os
import struct
import zlib

WIDTH = 1024
HEIGHT = 1024

PAPER = (0xF7, 0xF3, 0xEA)   # warm paper
INK = (0x14, 0x14, 0x14)     # near-black ink
RED = (0xC8, 0x10, 0x2E)     # breaking-news red
BLUE = (0x1E, 0x40, 0xAF)    # link blue
GREY = (0x5B, 0x67, 0x70)    # muted grey
WHITE = (0xFF, 0xFF, 0xFF)
BLACK = (0x00, 0x00, 0x00)

# ---------------------------------------------------------------- font
# 5x7 bitmap font. Each glyph: 7 rows of 5 characters ('#' = on, '.' = off).
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "....#", "....#", "....#", "....#", "#...#", ".###."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    "a": (".....", ".....", ".###.", "....#", ".####", "#...#", ".####"),
    "b": ("#....", "#....", "####.", "#...#", "#...#", "#...#", "####."),
    "c": (".....", ".....", ".####", "#....", "#....", "#....", ".####"),
    "d": ("....#", "....#", ".####", "#...#", "#...#", "#...#", ".####"),
    "e": (".....", ".....", ".###.", "#...#", "#####", "#....", ".###."),
    "f": ("..##.", ".#..#", ".#...", "####.", ".#...", ".#...", ".#..."),
    "g": (".....", ".....", ".####", "#...#", "#...#", ".####", "....#", ".###."),
    "h": ("#....", "#....", "####.", "#...#", "#...#", "#...#", "#...#"),
    "i": (".....", "..#..", ".....", ".##..", "..#..", "..#..", ".###."),
    "j": (".....", "...#.", ".....", "..##.", "...#.", "...#.", "...#.", ".##.."),
    "k": ("#....", "#....", "#..#.", "#.#..", "##...", "#.#..", "#..#."),
    "l": (".##..", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "m": (".....", ".....", "##.#.", "#.#.#", "#.#.#", "#.#.#", "#.#.#"),
    "n": (".....", ".....", "####.", "#...#", "#...#", "#...#", "#...#"),
    "o": (".....", ".....", ".###.", "#...#", "#...#", "#...#", ".###."),
    "p": (".....", ".....", "####.", "#...#", "#...#", "####.", "#....", "#...."),
    "q": (".....", ".....", ".####", "#...#", "#...#", ".####", "....#", "....#"),
    "r": (".....", ".....", "#.##.", "##..#", "#....", "#....", "#...."),
    "s": (".....", ".....", ".####", "#....", ".###.", "....#", "####."),
    "t": (".#...", ".#...", "####.", ".#...", ".#...", ".#...", "..##."),
    "u": (".....", ".....", "#...#", "#...#", "#...#", "#..##", ".##.#"),
    "v": (".....", ".....", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "w": (".....", ".....", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."),
    "x": (".....", ".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#"),
    "y": (".....", ".....", "#...#", "#...#", ".####", "....#", ".###."),
    "z": (".....", ".....", "#####", "...#.", "..#..", ".#...", "#####"),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".#.#.", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "(": ("...#.", "..#..", "..#..", "..#..", "..#..", "..#..", "...#."),
    ")": (".#...", "..#..", "..#..", "..#..", "..#..", "..#..", ".#..."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "%": ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.##.", "#..##"),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    "+": (".....", "..#..", "..#..", ".###.", "..#..", "..#..", "....."),
    "=": (".....", ".....", ".###.", ".....", ".###.", ".....", "....."),
    "&": (".##..", "#..#.", "#..#.", ".#...", "#.#.#", "#..#.", ".##.#"),
    "·": (".....", ".....", ".##..", ".##..", ".....", ".....", "....."),
    "#": (".#.#.", ".#.#.", "#####", ".#.#.", "#####", ".#.#.", ".#.#."),
    "@": (".###.", "#...#", "#.###", "#.#.#", "#.###", "#....", ".###."),
    "*": (".....", ".#.#.", "..#..", "#####", "..#..", ".#.#.", "....."),
    "_": (".....", ".....", ".....", ".....", ".....", ".....", "#####"),
    "[": (".###.", ".#...", ".#...", ".#...", ".#...", ".#...", ".###."),
    "]": (".###.", "...#.", "...#.", "...#.", "...#.", "...#.", ".###."),
    "<": ("...#.", "..#..", ".#...", "#....", ".#...", "..#..", "...#."),
    ">": (".#...", "..#..", "...#.", "....#", "...#.", "..#..", ".#..."),
}
# Normalise glyph rows to exactly 7 rows of 5 chars. Descender glyphs (g, j,
# p, q) are stored with 8 rows: drop leading blank rows first so the
# descender survives inside the 7-row grid.
for _ch in list(FONT):
    _rows = list(FONT[_ch])
    while len(_rows) > 7 and _rows[0] == ".....":
        _rows.pop(0)
    _rows = _rows[:7]
    while len(_rows) < 7:
        _rows.append(".....")
    FONT[_ch] = tuple(r[:5].ljust(5, ".") for r in _rows)


def _norm_char(ch):
    if ch == "—":
        return "-"
    if ch == "’":
        return "'"
    return ch


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg=PAPER):
        self.w = w
        self.h = h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def get(self, x, y):
        i = (y * self.w + x) * 3
        return tuple(self.px[i:i + 3])

    def fill_rect(self, x, y, w, h, color):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def rect(self, x, y, w, h, color, t=1):
        self.fill_rect(x, y, w, t, color)
        self.fill_rect(x, y + h - t, w, t, color)
        self.fill_rect(x, y, t, h, color)
        self.fill_rect(x + w - t, y, t, h, color)

    def line(self, x0, y0, x1, y1, color, t=1):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            if t == 1:
                self.set(x0, y0, color)
            else:
                r = t // 2
                self.fill_rect(x0 - r, y0 - r, t, t, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def fill_circle(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            half = int(math.sqrt(max(0, r * r - (yy - cy) ** 2)))
            self.fill_rect(cx - half, yy, 2 * half + 1, 1, color)

    def circle(self, cx, cy, r, color, t=1):
        # outline circle by sampling angles
        steps = max(24, int(2 * math.pi * r))
        for i in range(steps):
            a = 2 * math.pi * i / steps
            self.fill_rect(int(cx + r * math.cos(a)) - t // 2,
                           int(cy + r * math.sin(a)) - t // 2, t, t, color)

    def fill_poly(self, pts, color):
        # even-odd scanline fill
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                self.fill_rect(int(math.ceil(xs[j])), y,
                               max(1, int(math.floor(xs[j + 1])) - int(math.ceil(xs[j])) + 1),
                               1, color)

    def ink_count(self):
        n = 0
        for i in range(0, len(self.px), 3):
            if tuple(self.px[i:i + 3]) != PAPER:
                n += 1
        return n


# ---------------------------------------------------------------- PNG
def encode_png(canvas):
    def chunk(ctype, payload):
        return (struct.pack(">I", len(payload)) + ctype + payload +
                struct.pack(">I", binascii.crc32(ctype + payload) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    raw = bytearray()
    for y in range(canvas.h):
        raw.append(0)
        raw += canvas.px[y * canvas.w * 3:(y + 1) * canvas.w * 3]
    idat = zlib.compress(bytes(raw), 9)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
            chunk(b"IDAT", idat) + chunk(b"IEND", b""))

# ---------------------------------------------------------------- text
def text_width(text, scale):
    return sum((6 if _norm_char(c) != " " else 6) * scale for c in text) - scale \
        if text else 0


def draw_text(img, x, y, text, scale, color, bold=False):
    """Draw text at top-left (x, y). Returns the width drawn."""
    cx = x
    off = 0
    if bold:
        off = 1 if scale <= 3 else scale // 3
    passes = (0, off) if bold else (0,)
    for dx in passes:
        cx = x + dx
        for ch in text:
            glyph = FONT.get(_norm_char(ch))
            if glyph is None:
                cx += 6 * scale
                continue
            for r, row in enumerate(glyph):
                for c, bit in enumerate(row):
                    if bit == "#":
                        img.fill_rect(cx + c * scale, y + r * scale,
                                      scale, scale, color)
            cx += 6 * scale
    return cx - x


def wrap_text(text, scale, max_w):
    """Greedy word wrap; returns lines that each fit max_w."""
    words = text.split(" ")
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if text_width(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_text_centered(img, cx, y, text, scale, color, bold=False):
    w = text_width(text, scale)
    return draw_text(img, cx - w // 2, y, text, scale, color, bold)


# ---------------------------------------------------------------- pictograms
# Each takes (img, x, y, w, h, color): draws centred inside the box.
def pic_padlock(img, x, y, w, h, color):
    cx, cy = x + w // 2, y + h // 2
    s = min(w, h)
    bw, bh = int(s * 0.62), int(s * 0.42)          # body
    bx, by = cx - bw // 2, cy - bh // 2 + int(s * 0.12)
    img.circle(cx, by, int(s * 0.20), color, 3)    # shackle arc (full ring reads fine)
    img.fill_rect(bx, by, bw, bh, color)           # body
    img.fill_circle(cx, by + bh // 2 - 2, int(s * 0.07), PAPER)  # keyhole
    img.fill_rect(cx - 2, by + bh // 2, 5, int(s * 0.10), PAPER)


def pic_scales(img, x, y, w, h, color):
    cx, cy = x + w // 2, y + h // 2
    s = min(w, h)
    img.line(cx, cy - int(s * 0.42), cx, cy + int(s * 0.42), color, 3)
    img.line(cx - int(s * 0.42), cy - int(s * 0.34), cx + int(s * 0.42),
             cy - int(s * 0.34), color, 3)
    img.fill_circle(cx, cy - int(s * 0.42), 4, color)
    for sgn in (-1, 1):
        px = cx + sgn * int(s * 0.42)
        img.line(px, cy - int(s * 0.34), px, cy + int(s * 0.05), color, 2)
        img.line(px - int(s * 0.16), cy + int(s * 0.05),
                 px + int(s * 0.16), cy + int(s * 0.05), color, 2)
        # pan: half-disc
        for dy in range(0, int(s * 0.13)):
            half = int(math.sqrt(max(0, (s * 0.16) ** 2 - (dy - s * 0.05) ** 2)) * 0.9)
            img.fill_rect(px - half, cy + int(s * 0.05) + dy, 2 * half + 1, 1, color)
    img.line(cx - int(s * 0.20), cy + int(s * 0.42), cx + int(s * 0.20),
             cy + int(s * 0.42), color, 3)


def pic_chart(img, x, y, w, h, color):
    cx, cy = x + w // 2, y + h // 2
    s = min(w, h)
    ox, oy = cx - int(s * 0.38), cy + int(s * 0.34)
    img.line(ox, oy - int(s * 0.72), ox, oy, color, 3)      # y axis
    img.line(ox, oy, ox + int(s * 0.80), oy, color, 3)      # x axis
    pts = [(ox + int(s * 0.06), oy - int(s * 0.62)),
           (ox + int(s * 0.24), oy - int(s * 0.52)),
           (ox + int(s * 0.40), oy - int(s * 0.30)),
           (ox + int(s * 0.58), oy - int(s * 0.10)),
           (ox + int(s * 0.74), oy - int(s * 0.02))]
    for a, b in zip(pts, pts[1:]):
        img.line(a[0], a[1], b[0], b[1], RED, 4)
    ex, ey = pts[-1]
    img.fill_poly([(ex, ey), (ex - 12, ey - 3), (ex - 3, ey - 12)], RED)
    img.fill_circle(pts[0][0], pts[0][1], 4, RED)


def pic_burst(img, x, y, w, h, color):
    cx, cy = x + w // 2, y + h // 2
    s = min(w, h)
    for i in range(12):
        a = 2 * math.pi * i / 12
        r = int(s * 0.46) if i % 2 == 0 else int(s * 0.28)
        img.line(cx, cy, int(cx + r * math.cos(a)), int(cy + r * math.sin(a)),
                 color, 4)
    img.fill_circle(cx, cy, int(s * 0.13), RED)


def pic_capsule(img, x, y, w, h, color):
    cx, cy = x + w // 2, y + h // 2
    s = min(w, h)
    r = int(s * 0.16)
    x0, x1 = cx - int(s * 0.42), cx + int(s * 0.42)
    yc = cy
    img.fill_circle(x0 + r, yc, r, color)
    img.fill_circle(x1 - r, yc, r, color)
    img.fill_rect(x0 + r, yc - r, (x1 - r) - (x0 + r), 2 * r, color)
    # red half (right side)
    img.fill_circle(x1 - r, yc, r, RED)
    img.fill_rect(cx, yc - r, (x1 - r) - cx, 2 * r, RED)
    img.fill_rect(cx - 2, yc - r, 4, 2 * r, WHITE)


def pic_badge(img, x, y, w, h, color):
    cx, cy = x + w // 2, y + h // 2
    s = min(w, h)
    img.circle(cx, cy, int(s * 0.44), color, 3)
    img.circle(cx, cy, int(s * 0.36), color, 2)
    # five-point star
    ro, ri = s * 0.30, s * 0.12
    pts = []
    for i in range(10):
        r = ro if i % 2 == 0 else ri
        a = -math.pi / 2 + i * math.pi / 5
        pts.append((int(cx + r * math.cos(a)), int(cy + r * math.sin(a))))
    img.fill_poly(pts, RED)


def pic_robot(img, x, y, w, h, color):
    cx, cy = x + w // 2, y + h // 2
    s = min(w, h)
    hw, hh = int(s * 0.30), int(s * 0.26)
    hx, hy = cx - hw // 2, cy - int(s * 0.34)
    img.line(cx, hy, cx, hy - int(s * 0.14), color, 3)          # antenna
    img.fill_circle(cx, hy - int(s * 0.16), 4, RED)
    img.fill_rect(hx, hy, hw, hh, color)                        # head
    img.fill_rect(hx + int(hw * 0.18), hy + int(hh * 0.32), int(hw * 0.18),
                  int(hh * 0.22), PAPER)                         # eyes
    img.fill_rect(hx + int(hw * 0.64), hy + int(hh * 0.32), int(hw * 0.18),
                  int(hh * 0.22), PAPER)
    bw, bh = int(s * 0.44), int(s * 0.26)
    bx, by = cx - bw // 2, hy + hh + int(s * 0.05)
    img.fill_rect(bx, by, bw, bh, color)                         # body
    img.fill_rect(bx + int(bw * 0.18), by + int(bh * 0.30), int(bw * 0.64), 3, RED)
    img.fill_rect(bx + int(bw * 0.18), by + int(bh * 0.60), int(bw * 0.40), 3, RED)


PICTOGRAMS = {
    "padlock": pic_padlock,
    "scales": pic_scales,
    "chart": pic_chart,
    "burst": pic_burst,
    "capsule": pic_capsule,
    "badge": pic_badge,
    "robot": pic_robot,
}

# ---------------------------------------------------------------- content
# (text, scale, max_width) registry: every drawn string, for the overflow test.
TEXT_BOXES = []
ALL_TEXT = []


def register(text, scale, max_w):
    TEXT_BOXES.append((text, scale, max_w))
    ALL_TEXT.append(text)
    return wrap_text(text, scale, max_w)


MASTHEAD_TITLE = "THE WORLD TODAY"
MASTHEAD_DATE = ["SATURDAY", "21 NOVEMBER 2026"]
KICKER_LEFT = "ONE DAY IN THE WORLD - IN SEVEN PICTURES"
KICKER_RIGHT = "LATE EDITION"

LEAD_KICKER = "CYBERATTACK · WASHINGTON"
LEAD_HEADLINE = "FBI DATABASE HACKED"
LEAD_STANDFIRST = "FBI probes a suspected breach of its crime database."
LEAD_CHIP = "2ND BREACH IN MONTHS · USDA ALSO HIT"
LEAD_TINT = (0xFB, 0xE9, 0xE7)

TEAL = (0x0E, 0x7A, 0x5B)      # health green
ORANGE = (0xC2, 0x57, 0x0B)    # crime orange

# (pictogram, picture-field tint, headline, big stat or None, stat colour, fact)
CARDS = [
    ("scales", (0xE4, 0xEB, 0xF7), "MYANMAR GUILTY OF GENOCIDE",
     None, None, "A first for any court · Myanmar calls it unfair"),
    ("chart", (0xFB, 0xF0, 0xD3), "MARKETS IN MELTDOWN",
     "-5.28%", RED, "S&P -3.7% · Dow -950"),
    ("burst", (0xFB, 0xE3, 0xD8), "KYIV UNDER FIRE",
     "400+", RED, "drones, 110+ missiles"),
    ("capsule", (0xE2, 0xF2, 0xE4), "CANCER BREAKTHROUGH",
     "1 IN 12", TEAL, "90.2% stopped growing"),
    ("badge", (0xEA, 0xE6, 0xF2), "EL CHAPO ISIDRO CAUGHT",
     "$5M REWARD", ORANGE, None),
    ("robot", (0xDD, 0xF0, 0xEE), "128 NATIONS AGREE ROBOT RULES",
     None, None, "Draft rules by 2028 · No binding treaty yet"),
]

TICKER_LINES = [
    "ALSO TODAY: Shenzhen peace deal · COP31 deadlocked · Bayer $7.25bn deal",
    "Houthi missiles intercepted · Gen Z protests, 25 nations · Peru 6.9 quake",
]
FOOTER = "Sources: Reuters · AP · CNN · BBC · UN News · ICJ · AFP"
SIGNOFF = "One day, seven stories, seven pictures."


# Register every drawn string at import time so the tests can verify
# font coverage and overflow without rendering.
register(MASTHEAD_TITLE, 7, 664)
for _l in MASTHEAD_DATE:
    register(_l, 3, 288)
register(KICKER_LEFT, 2, 700)
register(KICKER_RIGHT, 2, 200)
register(LEAD_KICKER, 3, 660)
register(LEAD_HEADLINE, 8, 660)
register(LEAD_STANDFIRST, 3, 660)
register(LEAD_CHIP, 2, 474)
for _pic, _tint, _h, _stat, _sc, _f in CARDS:
    register(_h, 4, 290)
    if _stat:
        register(_stat, 4, 290)
    if _f:
        register(_f, 2, 290)
for _l in TICKER_LINES:
    register(_l, 2, 944)
register(FOOTER, 2, 976)
register(SIGNOFF, 2, 976)


# ---------------------------------------------------------------- layout
def draw_page(img):
    # Masthead: black band, white title left, date right.
    img.fill_rect(0, 0, WIDTH, 100, BLACK)
    draw_text(img, 28, 25, MASTHEAD_TITLE, 7, WHITE, bold=True)
    for i, line in enumerate(MASTHEAD_DATE):
        draw_text(img, 996 - text_width(line, 3), 20 + i * 30, line, 3,
                  WHITE, bold=True)
    # Breaking red rule under the masthead.
    img.fill_rect(0, 100, WIDTH, 6, RED)
    # Kicker strip.
    draw_text(img, 28, 118, KICKER_LEFT, 2, INK, bold=True)
    draw_text(img, 996 - text_width(KICKER_RIGHT, 2), 118, KICKER_RIGHT, 2,
              GREY, bold=True)

    # Lead band: FBI database hacked.
    img.fill_rect(24, 152, 976, 244, WHITE)
    img.rect(24, 152, 976, 244, INK, 2)
    img.fill_rect(24, 152, 8, 244, RED)
    img.fill_rect(40, 168, 252, 212, LEAD_TINT)
    PICTOGRAMS["padlock"](img, 91, 199, 150, 150, INK)
    draw_text(img, 316, 168, LEAD_KICKER, 3, RED, bold=True)
    lead_lines = wrap_text(LEAD_HEADLINE, 8, 660)
    ly = 196
    for line in lead_lines:
        draw_text(img, 316, ly, line, 8, INK, bold=True)
        ly += 64
    stand_lines = wrap_text(LEAD_STANDFIRST, 3, 660)
    sy = 318
    for line in stand_lines:
        draw_text(img, 316, sy, line, 3, INK)
        sy += 26
    # Red chip: second breach + USDA hit.
    img.fill_rect(316, 370, 474, 22, RED)
    draw_text(img, 326, 375, LEAD_CHIP, 2, WHITE, bold=True)

    # Grid: six picture-led cards, 3 x 2.
    for idx, (pic, tint, headline, stat, stat_color, fact) in enumerate(CARDS):
        cx0 = 24 + (idx % 3) * 330
        cy0 = 412 + (idx // 3) * 244
        img.fill_rect(cx0, cy0, 314, 228, WHITE)
        img.rect(cx0, cy0, 314, 228, INK, 2)
        img.fill_rect(cx0 + 2, cy0 + 2, 310, 96, tint)
        PICTOGRAMS[pic](img, cx0 + 97, cy0 + 5, 120, 90, INK)
        head_lines = wrap_text(headline, 4, 290)
        hy = cy0 + 104
        for line in head_lines:
            draw_text_centered(img, cx0 + 157, hy, line, 4, INK, bold=True)
            hy += 29
        if stat:
            draw_text_centered(img, cx0 + 157, hy + 2, stat, 4, stat_color,
                               bold=True)
            hy += 34
        if fact:
            fact_lines = wrap_text(fact, 2, 290)
            fy = hy + 2
            for line in fact_lines:
                draw_text_centered(img, cx0 + 157, fy, line, 2, GREY)
                fy += 16

    # Ticker strip.
    img.fill_rect(24, 900, 976, 46, RED)
    for i, line in enumerate(TICKER_LINES):
        draw_text(img, 40, 908 + i * 18, line, 2, WHITE, bold=True)

    # Footer.
    draw_text_centered(img, 512, 962, FOOTER, 2, GREY)
    draw_text_centered(img, 512, 986, SIGNOFF, 2, GREY)


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    img = Canvas(WIDTH, HEIGHT)
    draw_page(img)
    data = encode_png(img)
    with open(os.path.join(outdir, "entry.png"), "wb") as f:
        f.write(data)
    print(f"wrote {os.path.join(outdir, 'entry.png')} ({len(data)} bytes)")


if __name__ == "__main__":
    main()
