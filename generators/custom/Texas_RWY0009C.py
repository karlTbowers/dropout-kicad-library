#!/usr/bin/env python3
"""TI RWY0009C: VQFN-HR (HotRod), 9 pins, 2 x 3 mm, 0.5 mm pitch, 1.0 mm max height, wettable flanks.
Used by the TPS6281x-Q1 bucks (e.g. TPS628122GQWRWYRQ1).

Usage: ~/.cache/dropout/klt-venv/bin/python generators/custom/Texas_RWY0009C.py

The corner pins 1, 5, 7, 8 are L-shaped and pins 2-4 are bars across the package, which no kicad-library-tools
generator makes.
Source: TPS6281x-Q1 data sheet SLVSDU1K (August 2018, revised July 2025), RWY0009C drawing 4226803/A 05/2021
(pp. 51-53; the wettable-flank version, "Package with wettable flanks", p. 1). RWY0009A (4224015/B, pp. 48-50) has
the same land pattern and stencil. Land pattern example (p. 52), top view:
- pins 2, 3, 4: 3X (2.3) x (0.25) bars at (0.5) pitch, pin 3 on the centre line;
- pins 1, 5, 7, 8: L pads (0.775) x (0.775), legs (0.35) wide along y and (0.25) along x, the horizontal leg's
  centre line (0.5) from pin 2's / pin 4's, the vertical leg's centre (0.55) from the centre line;
- pins 9, 6: 0.25 x (0.65), centres (2.65) apart; R0.05 corners on every pad; non-solder-mask-defined.
Stencil example (p. 53, 0.1 mm): bars split into 6X (1.05) x (0.25); L pads 90 % coverage, inner legs (0.31) and
(0.21) wide; pins 6 and 9 the land size.
Package (p. 51): body 1.9..2.1 x 2.9..3.1, 0.8..1.0 high, A1 0.00..0.05, terminals 0.2 +/-0.05 (bars),
0.2..0.3 (9X), 0.3..0.4 (4X); wettable-flank step 0.1 min deep.
Pad 1 top left; 1, 2, 3, 4, 5 down the left (bars across), 6 bottom centre, 7 bottom right, 8 top right, 9 top
centre (Figure 5-1 and the land pattern). No exposed pad.
3D model dimensions the drawing does not give are marked ESTIMATE.
"""
from fplib import (BODY, CRT_CLR, CRT_W, FAB_W, METAL, SILK_PAD, SILK_W, chamfered_rect, custom_pad, fab_ref,
                   footprint_text, line, model_ref, poly, r, rect, smd_pad, text, up, write_footprint, write_model)

LIB = "DropOut_Package_DFN_QFN"
NAME = "Texas_RWY0009C_VQFN-HR-9_2x3mm_P0.5mm"
DATASHEET = "https://www.ti.com/lit/ds/symlink/tps62813-q1.pdf"

PITCH = 0.5
BAR_L, BAR_W = 2.3, 0.25          # pins 2-4
XO = BAR_L / 2                    # 1.15: outer x edge of bars and L pads
L_SIZE = 0.775                    # L pad overall, x and y
V_W, H_W = 0.35, 0.25             # vertical leg width (x), horizontal leg height (y)
SMALL_W, SMALL_H = 0.25, 0.65     # pins 6 and 9
SMALL_C = 2.65 / 2                # centre of pins 6 and 9
YO = SMALL_C + SMALL_H / 2        # 1.65: outer y edge of pins 6, 9 and the L pads
RR = round(0.05 / 0.25, 4)        # R0.05 corners
PASTE_V, PASTE_H = 0.31, 0.21     # stencil: L legs on the inner side
PASTE_BAR = 1.05                  # stencil: 6X (1.05) bar halves

BX, BY, HEIGHT = 2.0, 3.0, 0.9    # body nominal; A 0.8..1.0


def l_pad(num, sx, sy):
    """L pad in the quadrant (sx, sy); horizontal leg at |y| = 1.0, vertical leg out to the package end."""
    hy = sy * (2 * PITCH)                                   # horizontal leg centre line
    ax, ay = sx * (XO - L_SIZE / 2), hy                     # anchor: the horizontal leg
    vx0, vx1 = sx * (XO - L_SIZE), sx * (XO - L_SIZE + V_W)
    vy0, vy1 = sy * YO, hy + sy * H_W / 2
    leg = [(vx0 - ax, vy0 - ay), (vx1 - ax, vy0 - ay), (vx1 - ax, vy1 - ay), (vx0 - ax, vy1 - ay)]
    return custom_pad(num, (ax, ay), (L_SIZE, H_W), [leg])


def paste_rect(x0, x1, y0, y1):
    """Unnumbered paste-only aperture (as kicad-library-tools' QFN generator writes split paste)."""
    return (f'\t(pad "" smd roundrect (at {r((x0 + x1) / 2)} {r((y0 + y1) / 2)}) (size {r(abs(x1 - x0))} '
            f'{r(abs(y1 - y0))})\n\t\t(layers "F.Paste") (roundrect_rratio {RR}))')


def l_paste(sx, sy):
    """Paste L for one corner: the inner (concave) edges pulled back to the stencil's 0.31 / 0.21 legs."""
    hy = sy * (2 * PITCH)
    x_out, x_in = sx * XO, sx * (XO - L_SIZE)
    h_out, h_in = hy + sy * H_W / 2, hy + sy * H_W / 2 - sy * PASTE_H     # horizontal leg (outer edge kept)
    v_in = x_in + sx * (V_W - PASTE_V)                                      # vertical leg's concave edge
    ax, ay = (x_out + x_in) / 2, (h_out + h_in) / 2                         # anchor: the horizontal leg
    leg = [(v_in - ax, h_in - ay), (x_in - ax, h_in - ay), (x_in - ax, sy * YO - ay), (v_in - ax, sy * YO - ay)]
    return custom_pad("", (ax, ay), (L_SIZE, PASTE_H), [leg]).replace(
        '(layers "F.Cu" "F.Mask" "F.Paste")', '(layers "F.Paste")')


def pads():
    out = []
    for n, sx, sy in ((1, -1, -1), (5, -1, 1), (7, 1, 1), (8, 1, -1)):
        out.append(l_pad(n, sx, sy).replace('(layers "F.Cu" "F.Mask" "F.Paste")', '(layers "F.Cu" "F.Mask")'))
    for n, y in ((2, -PITCH), (3, 0), (4, PITCH)):
        out.append(smd_pad(n, 0, y, BAR_L, BAR_W, rratio=RR).replace(
            '(layers "F.Cu" "F.Mask" "F.Paste")', '(layers "F.Cu" "F.Mask")'))
    out.append(smd_pad(6, 0, SMALL_C, SMALL_W, SMALL_H, rratio=RR))
    out.append(smd_pad(9, 0, -SMALL_C, SMALL_W, SMALL_H, rratio=RR))
    return out


def paste():
    out = [l_paste(sx, sy) for sx in (-1, 1) for sy in (-1, 1)]
    for y in (-PITCH, 0, PITCH):
        for sx in (-1, 1):
            x0, x1 = sx * XO, sx * (XO - PASTE_BAR)
            out.append(paste_rect(x0, x1, y - BAR_W / 2, y + BAR_W / 2))
    return out


def footprint():
    hx, hy = BX / 2, BY / 2
    crt_x = up(max(XO, hx) + CRT_CLR, 0.05)
    crt_y = up(max(YO, hy) + CRT_CLR, 0.05)
    sy = YO + SILK_PAD + SILK_W / 2
    sx = XO + SILK_PAD + SILK_W / 2
    # silk: corner marks clear of the pads, plus a pin 1 arrow at the top left
    tip_x, tip_y = -sx, -sy
    arrow = poly([(tip_x, tip_y), (tip_x - 0.24, tip_y - 0.33), (tip_x + 0.24, tip_y - 0.33)], "F.SilkS", SILK_W)
    marks = [line(hx - 0.3, sy, sx, sy, "F.SilkS", SILK_W), line(sx, sy, sx, sy - 0.3, "F.SilkS", SILK_W),
             line(hx - 0.3, -sy, sx, -sy, "F.SilkS", SILK_W), line(sx, -sy, sx, -sy + 0.3, "F.SilkS", SILK_W),
             line(-hx + 0.3, sy, -sx, sy, "F.SilkS", SILK_W), line(-sx, sy, -sx, sy - 0.3, "F.SilkS", SILK_W)]
    descr = (f"TI RWY0009C VQFN-HR (HotRod), 9 pins, 2x3mm, 0.5mm pitch, wettable flanks, L-shaped corner pins and "
             f"bar pins (TPS6281x-Q1 data sheet SLVSDU1K, drawing 4226803/A, example board layout p. 52; RWY0009A "
             f"has the same lands), {DATASHEET}#page=51")
    body = [
        text("Reference", "REF**", -crt_y - 0.8, "F.SilkS"),
        text("Value", NAME, crt_y + 0.8, "F.Fab"),
        arrow, *marks,
        rect(-crt_x, -crt_y, crt_x, crt_y, "F.CrtYd", CRT_W),
        chamfered_rect(-hx, -hy, hx, hy, 0.5, "F.Fab", FAB_W),
        fab_ref(0.5),
        *paste(),
        *pads(),
        model_ref(LIB, NAME),
    ]
    return footprint_text(NAME, descr, "VQFN QFN VQFN-HR HotRod RWY0009C RWY0009A wettable flank", body)


def model():
    import cadquery as cq

    def box(x0, x1, y0, y1, z0, z1):
        return (cq.Workplane("XY").box(abs(x1 - x0), abs(y1 - y0), z1 - z0)
                .translate(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)))

    hx, hy, t = BX / 2, BY / 2, 0.2              # ESTIMATE: terminal (lead frame) thickness
    body = box(-hx, hx, -hy, hy, 0.0, HEIGHT)
    # Terminals: the land shapes clipped to the body outline (ESTIMATE: the drawing dimensions only the
    # terminal widths; the lands follow the terminals with a toe beyond the body)
    terms = None
    for y in (-PITCH, 0, PITCH):                 # bars 2-4, 0.2 wide
        b = box(-hx, hx, y - 0.1, y + 0.1, -0.001, t)
        terms = b if terms is None else terms.union(b)
    for sx in (-1, 1):
        for sy in (-1, 1):
            hyc = sy * 2 * PITCH                 # L: horizontal leg 0.25, vertical leg 0.3 wide (ESTIMATE in between)
            terms = terms.union(box(sx * hx, sx * (XO - L_SIZE), hyc - 0.125, hyc + 0.125, -0.001, t))
            terms = terms.union(box(sx * (XO - L_SIZE), sx * (XO - L_SIZE + 0.3), sy * hy, hyc, -0.001, t))
    for sy in (-1, 1):                           # pins 6 and 9, 0.25 wide
        terms = terms.union(box(-0.125, 0.125, sy * hy, sy * (SMALL_C - SMALL_H / 2 + 0.175), -0.001, t))
    body = body.cut(terms)
    dot = (cq.Workplane("XY").workplane(offset=HEIGHT - 0.02).center(-hx + 0.35, -hy + 0.45)
           .circle(0.12).extrude(0.03))          # ESTIMATE: index dot in the drawing's pin 1 index area
    body = body.cut(dot)
    # KiCad's model Y is the footprint's -y: mirror so pin 1 stays top left
    return [(body.mirror("XZ"), BODY), (terms.mirror("XZ"), METAL)]


if __name__ == "__main__":
    print("footprint ", write_footprint(LIB, NAME, footprint()))
    print("3D model  ", write_model(LIB, NAME, model()))
