#!/usr/bin/env python3
"""THE DAILY WORLD - 24 November 2026, in one image.
Pure Python standard library only: hand-rolled PNG encoder + bitmap font.
Deterministic: no network, no randomness, no time.
"""
import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- palette
PAPER = (0xF5, 0xEF, 0xE0)
INK = (0x16, 0x15, 0x13)
RED = (0xB3, 0x20, 0x2A)
BLUE = (0x1D, 0x4E, 0x89)
GREEN = (0x1E, 0x7A, 0x46)
NAVY = (0x14, 0x21, 0x3D)
GREY = (0x5A, 0x55, 0x4C)
WHITE = (0xFF, 0xFF, 0xFF)
BLACK = (0x00, 0x00, 0x00)
ORANGE = (0xE8, 0x6B, 0x1E)
LGREY = (0xB8, 0xB2, 0xA4)
SKIN = (0x8F, 0xC8, 0xE8)

buf = bytearray(W * H * 3)


def set_px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        buf[i] = c[0]
        buf[i + 1] = c[1]
        buf[i + 2] = c[2]


def fill_all(c):
    row = bytes(c) * W
    for y in range(H):
        buf[y * W * 3:(y + 1) * W * 3] = row


def fill_rect(x, y, w, h, c):
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(W, x + w)
    y1 = min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    row = bytes(c) * (x1 - x0)
    for yy in range(y0, y1):
        i = (yy * W + x0) * 3
        buf[i:i + (x1 - x0) * 3] = row


def outline_rect(x, y, w, h, t, c):
    fill_rect(x, y, w, t, c)
    fill_rect(x, y + h - t, w, t, c)
    fill_rect(x, y, t, h, c)
    fill_rect(x + w - t, y, t, h, c)


def fill_circle(cx, cy, r, c):
    for yy in range(cy - r, cy + r + 1):
        dy = yy - cy
        rem = r * r - dy * dy
        if rem < 0:
            continue
        dx = int(rem ** 0.5)
        fill_rect(cx - dx, yy, dx * 2 + 1, 1, c)


def fill_ellipse(cx, cy, rx, ry, c):
    if rx <= 0 or ry <= 0:
        return
    for yy in range(cy - ry, cy + ry + 1):
        dy = (yy - cy) / ry
        rem = 1.0 - dy * dy
        if rem < 0:
            continue
        dx = int(rx * (rem ** 0.5))
        fill_rect(cx - dx, yy, dx * 2 + 1, 1, c)


def fill_poly(points, c):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    x0, x1 = max(0, min(xs)), min(W - 1, max(xs))
    y0, y1 = max(0, min(ys)), min(H - 1, max(ys))
    n = len(points)
    for yy in range(y0, y1 + 1):
        for xx in range(x0, x1 + 1):
            inside = False
            j = n - 1
            for i in range(n):
                xi, yi = points[i]
                xj, yj = points[j]
                if ((yi > yy) != (yj > yy)) and (
                        xx < (xj - xi) * (yy - yi) / (yj - yi) + xi):
                    inside = not inside
                j = i
            if inside:
                set_px(xx, yy, c)


def thick_line(x0, y0, x1, y1, t, c):
    steps = max(abs(x1 - x0), abs(y1 - y0), 1)
    r = max(1, t // 2)
    for s in range(steps + 1):
        x = x0 + (x1 - x0) * s // steps
        y = y0 + (y1 - y0) * s // steps
        fill_circle(x, y, r, c)


def arc(cx, cy, rx, ry, a0, a1, t, c):
    # angles in degrees, 0 = east, positive = clockwise (screen coords)
    import math
    steps = max(8, int(abs(a1 - a0) * max(rx, ry) / 40) + 8)
    r = max(1, t // 2)
    for s in range(steps + 1):
        a = math.radians(a0 + (a1 - a0) * s / steps)
        x = int(cx + rx * math.cos(a))
        y = int(cy + ry * math.sin(a))
        fill_circle(x, y, r, c)


def ellipse_outline(cx, cy, rx, ry, t, c):
    arc(cx, cy, rx, ry, 0, 360, t, c)


# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows of 5 columns, '#' = ink.
FONT = {
    'A': (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'B': ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    'C': (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    'D': ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    'E': ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    'F': ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    'G': (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    'H': ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'I': (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    'J': ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    'K': ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    'L': ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    'M': ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    'N': ("#...#", "#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#"),
    'O': (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'P': ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    'Q': (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    'R': ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    'S': (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    'T': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    'U': ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'V': ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    'W': ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."),
    'X': ("#...#", ".#.#.", "..#..", "..#..", "..#..", ".#.#.", "#...#"),
    'Y': ("#...#", ".#.#.", "..#..", "..#..", "..#..", "..#..", "..#.."),
    'Z': ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    '0': (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    '1': ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    '2': (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    '3': (".###.", "#...#", "....#", "..##.", "....#", "#...#", ".###."),
    '4': ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    '5': ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    '6': (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    '7': ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    '8': (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    '9': (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    ' ': (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    '.': (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ',': (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    "'": (".##..", ".##..", ".#...", ".....", ".....", ".....", "....."),
    ':': (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    '!': ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    '?': (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    '-': (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    '\u2022': (".....", ".....", ".###.", ".###.", ".###.", ".....", "....."),
    '$': ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    '%': ("##..#", "##.#.", "....#", "...#.", "..#..", ".#...", "#..##"),
    '/': ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    '(': ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ')': ("##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."),
    '+': (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
}


def text_width(s, sx, spacing, bold=False):
    if not s:
        return 0
    return len(s) * (5 * sx + spacing) - spacing + (sx if bold else 0)


def draw_text(x, y, s, sx, sy, c, spacing=1, bold=False):
    """Draw text at (x, y); glyph cell is 5*sx wide, 7*sy tall."""
    cx = x
    for ch in s.upper():
        glyph = FONT.get(ch, FONT[' '])
        passes = (0, sx) if bold else (0,)
        for off in passes:
            for row in range(7):
                line = glyph[row]
                for col in range(5):
                    if line[col] == '#':
                        fill_rect(cx + off + col * sx, y + row * sy, sx, sy, c)
        cx += 5 * sx + spacing
    return cx - spacing


def draw_text_center(cx_center, y, s, sx, sy, c, spacing=1, bold=False):
    w = text_width(s, sx, spacing, bold)
    return draw_text(cx_center - w // 2, y, s, sx, sy, c, spacing, bold)


def draw_text_right(x_right, y, s, sx, sy, c, spacing=1, bold=False):
    w = text_width(s, sx, spacing, bold)
    return draw_text(x_right - w, y, s, sx, sy, c, spacing, bold)


# ---------------------------------------------------------------- icons
def icon_dove(cx, cy, r):
    """White dove on a deep-blue disc, holding a green olive branch."""
    fill_circle(cx, cy, r, BLUE)
    ellipse_outline(cx, cy, r - 4, r - 4, 2, SKIN)
    # tail (swept, lower left)
    fill_poly([(cx - 18, cy + 16), (cx - 62, cy + 34), (cx - 58, cy + 12),
               (cx - 66, cy - 2), (cx - 30, cy + 2)], WHITE)
    # body
    fill_ellipse(cx - 2, cy + 12, 40, 24, WHITE)
    # swept wing (angled back toward the tail, not a vertical fin)
    fill_poly([(cx - 22, cy + 6), (cx - 30, cy - 34), (cx - 16, cy - 46),
               (cx + 14, cy - 8), (cx + 12, cy + 8), (cx - 6, cy + 16)], WHITE)
    fill_poly([(cx - 14, cy + 4), (cx - 18, cy - 28), (cx - 10, cy - 34),
               (cx + 6, cy - 4), (cx + 4, cy + 6)], SKIN)
    # head + beak
    fill_circle(cx + 34, cy - 12, 15, WHITE)
    fill_poly([(cx + 47, cy - 14), (cx + 64, cy - 8), (cx + 47, cy - 4)], ORANGE)
    fill_circle(cx + 38, cy - 15, 3, INK)
    # olive branch from the beak
    thick_line(cx + 58, cy - 2, cx + 44, cy + 26, 4, GREEN)
    for (lx, ly, a, b) in [(53, 5, 8, 4), (48, 12, 7, 4), (55, 14, 7, 4),
                           (46, 21, 6, 3)]:
        fill_ellipse(cx + lx, cy + ly, a, b, GREEN)
    fill_circle(cx + 44, cy + 28, 4, GREEN)


def icon_carrier(cx, cy):
    # compact: fits y in [cy-30, cy+31]
    # hull + deck
    fill_poly([(cx - 80, cy - 1), (cx + 82, cy - 1), (cx + 64, cy + 17),
               (cx - 58, cy + 17)], NAVY)
    fill_rect(cx - 86, cy - 8, 172, 8, INK)
    # island tower
    fill_rect(cx + 34, cy - 24, 18, 17, INK)
    fill_rect(cx + 41, cy - 31, 4, 8, INK)
    fill_rect(cx + 31, cy - 26, 24, 3, INK)
    # tiny jet on deck
    fill_poly([(cx - 54, cy - 9), (cx - 34, cy - 16), (cx - 16, cy - 9)], GREY)
    fill_poly([(cx - 36, cy - 16), (cx - 30, cy - 22), (cx - 24, cy - 16)], GREY)
    # waves (upper arcs only, so they stay above cy+31)
    for wy, off in [(cy + 25, 0), (cy + 32, 24)]:
        for k in range(4):
            arc(cx - 76 + off + k * 44, wy, 19, 6, 180, 350, 4, BLUE)


def icon_globe(cx, cy):
    # compact: fits y in [cy-27, cy+27]
    fill_circle(cx - 16, cy - 1, 25, BLUE)
    # continent blobs
    fill_ellipse(cx - 27, cy - 11, 9, 6, GREEN)
    fill_ellipse(cx - 10, cy - 16, 7, 5, GREEN)
    fill_ellipse(cx - 22, cy + 7, 8, 7, GREEN)
    fill_ellipse(cx - 2, cy + 12, 6, 4, GREEN)
    fill_ellipse(cx - 4, cy - 3, 5, 6, GREEN)
    ellipse_outline(cx - 16, cy - 1, 25, 25, 3, NAVY)
    # thermometer
    fill_rect(cx + 32, cy - 26, 10, 42, WHITE)
    outline_rect(cx + 32, cy - 26, 10, 42, 3, RED)
    fill_circle(cx + 37, cy + 21, 9, RED)
    fill_rect(cx + 35, cy - 6, 5, 24, RED)
    for k in range(3):
        fill_rect(cx + 44, cy - 19 + k * 11, 6, 3, RED)


def icon_mercury(cx, cy):
    # compact: fits y in [cy-30, cy+24]
    # stars
    for (sx_, sy_, sr) in [(-84, -26, 3), (-56, -30, 2), (78, -28, 2),
                           (-88, 14, 2), (84, 20, 3), (-44, 24, 2)]:
        fill_circle(cx + sx_, cy + sy_, sr, INK)
    # orbit ring
    ellipse_outline(cx, cy, 74, 21, 3, GREY)
    # planet
    fill_circle(cx - 16, cy, 21, ORANGE)
    for (px, py, pr) in [(-24, -7, 4), (-8, 5, 5), (-22, 9, 3), (-6, -12, 3)]:
        fill_circle(cx + px, cy + py, pr, (0xB8, 0x4A, 0x12))
    # satellite on the ring (upper right)
    scx, scy = cx + 54, cy - 17
    fill_rect(scx - 19, scy - 6, 11, 12, BLUE)
    fill_rect(scx + 9, scy - 6, 11, 12, BLUE)
    fill_rect(scx - 7, scy - 8, 15, 16, LGREY)
    outline_rect(scx - 7, scy - 8, 15, 16, 2, INK)
    fill_circle(scx, scy - 13, 3, RED)


def icon_sport(cx, cy):
    # compact: fits y in [cy-28, cy+30]
    # checkered flag on a pole (left)
    fill_rect(cx - 88, cy - 28, 5, 56, INK)
    sq = 8
    for row in range(4):
        for col in range(5):
            wave = 2 if col in (2, 3) else (1 if col == 4 else 0)
            if (row + col) % 2 == 0:
                fill_rect(cx - 82 + col * sq, cy - 28 + row * sq + wave, sq, sq, INK)
            else:
                fill_rect(cx - 82 + col * sq, cy - 28 + row * sq + wave, sq, sq, WHITE)
    outline_rect(cx - 82, cy - 28, 5 * sq, 4 * sq, 2, INK)
    # low race car (right / lower)
    bx, by = cx + 8, cy + 12
    fill_poly([(bx - 32, by + 8), (bx - 25, by - 4), (bx + 0, by - 7),
               (bx + 12, by - 17), (bx + 30, by - 15), (bx + 40, by - 4),
               (bx + 54, by + 0), (bx + 58, by + 8)], RED)
    fill_poly([(bx + 14, by - 14), (bx + 21, by - 6), (bx + 5, by - 5)], SKIN)
    fill_rect(bx - 42, by - 12, 15, 5, INK)          # rear wing
    fill_rect(bx - 31, by - 7, 4, 9, INK)
    fill_rect(bx - 34, by + 15, 96, 4, INK)          # ground line
    for wx in (bx - 13, bx + 34):
        fill_circle(wx, by + 9, 8, INK)
        fill_circle(wx, by + 9, 4, LGREY)


# ---------------------------------------------------------------- layout
CX0, CX1 = 30, 994          # content edges (inside the frame)
MID = (CX0 + CX1) // 2


def panel(x, y, w, h, strip_c, label, headline, body, icon):
    outline_rect(x, y, w, h, 2, INK)
    fill_rect(x, y, w, 36, strip_c)
    draw_text(x + 12, y + 8, label, 3, 3, WHITE, spacing=2, bold=True)
    # headline: sy=5 (~35px), shrink sx until it fits
    sx = 3
    while sx > 1 and text_width(headline, sx, 1, True) > w - 20:
        sx -= 1
    draw_text(x + 10, y + 44, headline, sx, 5, INK, spacing=1, bold=True)
    icon(x + w // 2, y + 109)
    draw_text_center(x + w // 2, y + h - 52, body[0], 2, 3, INK, spacing=1)
    draw_text_center(x + w // 2, y + h - 27, body[1], 2, 3, INK, spacing=1)


def build():
    fill_all(PAPER)
    # outer double-rule frame
    outline_rect(10, 10, W - 20, H - 20, 6, INK)
    outline_rect(22, 22, W - 44, H - 44, 2, INK)

    # masthead
    fill_rect(CX0, 36, CX1 - CX0, 2, INK)
    draw_text_center(MID, 46, "THE DAILY WORLD", 9, 10, INK, spacing=5, bold=True)
    fill_rect(CX0, 122, CX1 - CX0, 2, INK)
    draw_text(CX0 + 2, 132, "TUESDAY, 24 NOVEMBER 2026", 3, 3, INK, spacing=2)
    fill_rect(549, 138, 10, 10, RED)
    draw_text_right(CX1 - 2, 132, "THE DAY IN ONE IMAGE", 3, 3, INK, spacing=2)
    fill_rect(CX0, 162, CX1 - CX0, 3, INK)

    # kicker strip
    fill_rect(CX0, 174, 252, 38, RED)
    draw_text_center(CX0 + 126, 180, "TOP STORY", 4, 4, WHITE, spacing=3, bold=True)
    draw_text(CX0 + 268, 183, "EUROPE LEADERS GATHER FOR TALKS", 3, 3, GREY, spacing=2)

    # hero headline (left) + dove (right)
    draw_text(CX0 + 2, 226, "PEACE TALKS", 10, 13, INK, spacing=6, bold=True)
    draw_text(CX0 + 2, 322, "FOR UKRAINE", 10, 13, INK, spacing=6, bold=True)
    icon_dove(856, 306, 88)

    # sub-headline, full width
    draw_text(CX0 + 2, 428, "TRUMP'S 28-POINT PLAN TESTED AS ZELENSKYY", 3, 4, INK, spacing=3)
    draw_text(CX0 + 2, 464, "SEEKS A DIGNIFIED PEACE IN EUROPE TALKS", 3, 4, INK, spacing=3)

    # thick divider
    fill_rect(CX0, 502, CX1 - CX0, 6, INK)

    # 2x2 panels
    pw, ph, gap = 476, 196, 12
    py1, py2 = 518, 726
    panel(CX0, py1, pw, ph, BLUE, "VENEZUELA", "US TURNS UP THE HEAT",
          ("CARRIER IN THE CARIBBEAN AS CARTEL",
           "DE LOS SOLES LISTED AS TERROR GROUP"), icon_carrier)
    panel(CX0 + pw + gap, py1, pw, ph, GREEN, "CLIMATE COP31",
          "SUMMIT SPLIT ON FOSSIL FUELS",
          ("LEADERS IN ANTALYA DIVIDED OVER",
           "PHASE-OUT PLEDGES AND FINANCE"), icon_globe)
    panel(CX0, py2, pw, ph, NAVY, "SPACE", "PROBE REACHES MERCURY",
          ("BEPICOLOMBO ENTERS ORBIT AROUND",
           "THE SUN'S NEAREST PLANET"), icon_mercury)
    panel(CX0 + pw + gap, py2, pw, ph, RED, "SPORT", "VERSTAPPEN WINS IN VEGAS",
          ("RED BULL STAR TAKES THE LAS VEGAS",
           "GRAND PRIX UNDER THE LIGHTS"), icon_sport)

    # bottom ticker
    fill_rect(CX0, 934, CX1 - CX0, 64, INK)
    draw_text_center(MID, 948, "ALSO TODAY: BOLSONARO BACK IN JAIL \u2022 INDIA-NEPAL EXPRESS LAUNCHED",
                     2, 3, WHITE, spacing=1, bold=True)
    draw_text_center(MID, 972, "\u2022 LISBON MARCHES ON LIVING COSTS \u2022",
                     2, 3, WHITE, spacing=1, bold=True)


# ---------------------------------------------------------------- PNG out
def write_png(path):
    raw = bytearray()
    stride = W * 3
    for y in range(H):
        raw.append(0)
        raw += buf[y * stride:(y + 1) * stride]

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    build()
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    size = write_png(path)
    print("wrote %s (%d bytes)" % (path, size))


if __name__ == "__main__":
    main()
