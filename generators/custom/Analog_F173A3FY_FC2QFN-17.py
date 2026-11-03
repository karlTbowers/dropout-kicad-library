#!/usr/bin/env python3
"""Analog Devices (Maxim) F173A3FY+7: FC2QFN, 17 pins + exposed pad, 3.5 x 3.75 x 0.7 mm, 0.5 mm pitch.
Used by MAX20004E / MAX20006E / MAX20008E (e.g. MAX20004EAFOA/VY+).

Usage: ~/.cache/dropout/klt-venv/bin/python generators/custom/Analog_F173A3FY_FC2QFN-17.py

Corner pins are L- and T-shaped, the switch pin is a long bar, which no kicad-library-tools generator makes.
Sources (MAX20004E datasheet 19-100562 Rev 6, "Package Information": outline 21-100383, land pattern 90-100124):
- Land pattern 90-100124 rev. A (top view), tolerance +/-0.02, R0.05 corners:
  overall 4.100 (x) by 4.350 (y); pad details A (corner L, 0.950 x 0.875, vertical leg 0.500, horizontal leg 0.450),
  B 0.875 x 0.300, C 0.825 x 0.325, D 1.425 x 0.250, E (T, 1.425 x 0.950, bar 0.250, stem 0.450 wide 0.500 from the
  outer edge), F 0.300 x 1.075, G 0.950 x 0.550 (exposed pad), H 0.350 x 1.925.
  Positions: A vertical legs 2.700 apart; F at 1.500 outer pitch (0.5 pitch); B centre 1.225 below the top edge, C 0.513
  below B; first D centre 2.225 below the top edge, then 0.650 to the next D and to E's bar; E stems 2.650 apart; G's top
  edge 1.500 below the top edge; H to the bottom edge on the centre line.
- Outline 21-100383 rev. B: D 3.5 bsc (x), E 3.75 bsc (y), A 0.650..0.750, A1 0.000..0.050, A3 0.152 ref; pin 1 laser
  mark top left; pins 1-5 down the left, 6 bottom centre, 7-11 up the right, 12-17 along the top right to left.
- Pin configuration (datasheet p. 8): 17 OUT (A, top left), 16 FB, 15 SSEN, 14 GND, 13 BIAS (F), 12 SYNC (A, top
  right); 1 RESET (B), 2 BST (C), 3 SUPSW (D), 4 PGND (D), 5 PGND (E) down the left; 11 EN (B), 10 SUP (C), 9 SUPSW
  (D), 8 PGND (D), 7 PGND (E) down the right; 6 LX (H); EP (G) = SUPSW, numbered 18 here (N+1, the datasheet gives
  it no number).
No stencil is given: paste follows the pads.
3D model dimensions the drawings do not give are marked ESTIMATE.
"""
from fplib import (BODY, CRT_CLR, CRT_W, FAB_W, METAL, SILK_PAD, SILK_W, chamfered_rect, custom_pad, fab_ref,
                   footprint_text, line, model_ref, poly, rect, smd_pad, text, up, write_footprint, write_model)

LIB = "DropOut_Package_DFN_QFN"
NAME = "Analog_F173A3FY_FC2QFN-17-1EP_3.5x3.75mm_P0.5mm"
DATASHEET = "https://www.analog.com/media/en/technical-documentation/data-sheets/max20004e-max20008e.pdf"
LAND = "https://mds.analog.com/api/public/content/90-100124.pdf"

XO, YO = 4.100 / 2, 4.350 / 2    # outer land edges
RR = 0.05                        # corner radius
BX, BY, HEIGHT = 3.5, 3.75, 0.7

TOP = -YO
Y_B = TOP + 1.225
Y_C = Y_B + 0.513
Y_D1 = TOP + 2.225
Y_D2 = Y_D1 + 0.650
Y_E = Y_D2 + 0.650


def rects_for(sx):
    """Pad rectangles (x0, x1, y0, y1) per pin on one side (sx = -1 left, +1 right), footprint coordinates."""
    def r(xa, xb, ya, yb):
        return (min(sx * xa, sx * xb), max(sx * xa, sx * xb), ya, yb)
    a_v = r(2.700 / 2 - 0.25, 2.700 / 2 + 0.25, TOP, TOP + 0.875)          # A vertical leg (0.500 wide)
    a_h = r(XO, XO - 0.950, TOP + 0.875 - 0.450, TOP + 0.875)              # A horizontal leg (0.450 high)
    b = r(XO, XO - 0.875, Y_B - 0.150, Y_B + 0.150)
    c = r(XO, XO - 0.825, Y_C - 0.1625, Y_C + 0.1625)
    d1 = r(XO, XO - 1.425, Y_D1 - 0.125, Y_D1 + 0.125)
    d2 = r(XO, XO - 1.425, Y_D2 - 0.125, Y_D2 + 0.125)
    e_bar = r(XO, XO - 1.425, Y_E - 0.125, Y_E + 0.125)
    e_stem = r(XO - 0.500, XO - 0.950, Y_E + 0.125, YO)                    # stem 0.450 wide, to the bottom edge
    return a_h, a_v, b, c, d1, d2, e_bar, e_stem


def pad_rects():
    lh, lv, lb, lc, ld1, ld2, le, les = rects_for(-1)
    rh, rv, rb, rc, rd1, rd2, re_, res = rects_for(1)
    f = {16: -0.75, 15: -0.25, 14: 0.25, 13: 0.75}
    out = {1: [lb], 2: [lc], 3: [ld1], 4: [ld2], 5: [le, les],
           7: [re_, res], 8: [rd2], 9: [rd1], 10: [rc], 11: [rb], 12: [rh, rv], 17: [lh, lv],
           6: [(-0.175, 0.175, YO - 1.925, YO)],
           18: [(-0.475, 0.475, TOP + 1.500, TOP + 1.500 + 0.550)]}
    for n, x in f.items():
        out[n] = [(x - 0.150, x + 0.150, TOP, TOP + 1.075)]
    return out


def make_pad(num, rects):
    x0, x1, y0, y1 = rects[0]
    w, h = x1 - x0, y1 - y0
    if len(rects) == 1:
        return smd_pad(num, (x0 + x1) / 2, (y0 + y1) / 2, w, h, rratio=round(RR / min(w, h), 4))
    ax, ay = (x0 + x1) / 2, (y0 + y1) / 2
    polys = [[(a - ax, c - ay), (b - ax, c - ay), (b - ax, d - ay), (a - ax, d - ay)] for a, b, c, d in rects[1:]]
    return custom_pad(num, (ax, ay), (w, h), polys)


def footprint():
    hx, hy = BX / 2, BY / 2
    crt_x = up(max(XO, hx) + CRT_CLR, 0.05)
    crt_y = up(max(YO, hy) + CRT_CLR, 0.05)
    sx, sy = XO + SILK_PAD + SILK_W / 2, YO + SILK_PAD + SILK_W / 2
    arrow = poly([(-sx, -sy), (-sx - 0.24, -sy - 0.33), (-sx + 0.24, -sy - 0.33)], "F.SilkS", SILK_W)
    marks = [line(hx - 0.3, sy, sx, sy, "F.SilkS", SILK_W), line(sx, sy, sx, sy - 0.3, "F.SilkS", SILK_W),
             line(hx - 0.3, -sy, sx, -sy, "F.SilkS", SILK_W), line(sx, -sy, sx, -sy + 0.3, "F.SilkS", SILK_W),
             line(-hx + 0.3, sy, -sx, sy, "F.SilkS", SILK_W), line(-sx, sy, -sx, sy - 0.3, "F.SilkS", SILK_W)]
    descr = (f"Analog Devices (Maxim) F173A3FY+7 FC2QFN, 17 pins + exposed pad 18, 3.5x3.75x0.7mm, 0.5mm pitch, "
             f"L-, T- and bar-shaped pins (outline 21-100383 rev. B, land pattern 90-100124 rev. A), {LAND}")
    body = [
        text("Reference", "REF**", -crt_y - 0.8, "F.SilkS"),
        text("Value", NAME, crt_y + 0.8, "F.Fab"),
        arrow, *marks,
        rect(-crt_x, -crt_y, crt_x, crt_y, "F.CrtYd", CRT_W),
        chamfered_rect(-hx, -hy, hx, hy, 0.6, "F.Fab", FAB_W),
        fab_ref(0.7),
        *[make_pad(n, rs) for n, rs in sorted(pad_rects().items())],
        model_ref(LIB, NAME),
    ]
    return footprint_text(NAME, descr, "FC2QFN QFN F173A3FY 21-100383 90-100124 MAX20004E MAX20006E MAX20008E", body)


def model():
    import cadquery as cq
    hx, hy, t = BX / 2, BY / 2, 0.152           # A3 0.152 ref: terminal thickness

    def box(x0, x1, y0, y1, z0, z1):
        return (cq.Workplane("XY").box(abs(x1 - x0), abs(y1 - y0), z1 - z0)
                .translate(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)))

    body = box(-hx, hx, -hy, hy, 0.0, HEIGHT)
    terms = None
    # ESTIMATE: terminals drawn as the lands clipped to the body outline (the lands reach 0.3 beyond it; the
    # outline's own terminal sizes L1..L6, b1..b5 agree with that within their tolerances)
    for rs in pad_rects().values():
        for x0, x1, y0, y1 in rs:
            x0, x1, y0, y1 = max(x0, -hx), min(x1, hx), max(y0, -hy), min(y1, hy)
            if x1 - x0 < 1e-6 or y1 - y0 < 1e-6:
                continue
            b = box(x0, x1, y0, y1, -0.001, t)
            terms = b if terms is None else terms.union(b)
    body = body.cut(terms)
    dot = (cq.Workplane("XY").workplane(offset=HEIGHT - 0.02).center(-hx + 0.4, -hy + 0.4)
           .circle(0.15).extrude(0.03))         # ESTIMATE: laser mark for pin 1 (outline: "in this area")
    body = body.cut(dot)
    # KiCad's model Y is the footprint's -y: mirror so pin 1 stays top left
    return [(body.mirror("XZ"), BODY), (terms.mirror("XZ"), METAL)]


if __name__ == "__main__":
    print("footprint ", write_footprint(LIB, NAME, footprint()))
    print("3D model  ", write_model(LIB, NAME, model()))
