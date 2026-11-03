#!/usr/bin/env python3
"""TI RYT0009A: VQFN-HR (HotRod), 9 pins, 2 x 2.2 mm, 0.5 mm pitch, 0.9 mm max height.
Used by the TPS6290x-Q1 bucks (e.g. TPS62903QRYTRQ1).

Usage: ~/.cache/dropout/klt-venv/bin/python generators/custom/Texas_RYT0009A.py

Corner pins 3, 4, 7, 9 have a leg toward the package end, which no kicad-library-tools generator makes.
Source: TPS62903-Q1 data sheet SLVSG65A (May 2022, revised March 2023), RYT0009A drawing 4226765/B 05/2024
(pp. 49-51). Land pattern example (p. 50), top view:
- 13X (0.25) wide lands at 8X (0.5) pitch; four rows per side at y = -0.75, -0.25, +0.25, +0.75;
- pins 1, 2, 5, 6 and the horizontal legs of 3 and 4: 6X (0.875) long, row centres (1.525) apart (x +/-0.7625);
- pins 9 and 7: horizontal leg 2X (0.825), with a 4X (0.4) leg up to the package end at the inner end;
- pins 3 and 4: a leg 4X (0.4) down to the package end, centred 2X (1) apart (x +/-0.5);
- pin 8: 0.25 x (0.65) on the centre line; lands span 2X (2.55) in y; R0.05 corners; NSMD, mask 0.07 max.
Stencil example (p. 51, 0.125 mm): the same apertures as the lands, so the paste follows the pads.
Package (p. 49): body 1.9..2.1 (x) by 2.1..2.3 (y), 0.8..0.9 high, A1 0.00..0.05, 13X terminals 0.2..0.3 wide.
Pin numbers as the land pattern example (top view): 9, 1, 2, 3 down the left, 8 top centre, 7, 6, 5, 4 down the
right (Figure 6-1 shows the same order, turned 180 degrees). No exposed pad.
3D model dimensions the drawing does not give are marked ESTIMATE.
"""
from fplib import (BODY, CRT_CLR, CRT_W, FAB_W, METAL, SILK_PAD, SILK_W, chamfered_rect, custom_pad, fab_ref,
                   footprint_text, line, model_ref, poly, rect, smd_pad, text, up, write_footprint, write_model)

LIB = "DropOut_Package_DFN_QFN"
NAME = "Texas_RYT0009A_VQFN-HR-9_2x2.2mm_P0.5mm"
DATASHEET = "https://www.ti.com/lit/ds/symlink/tps62903-q1.pdf"

W = 0.25                      # 13X (0.25) land width
BAR_L = 0.875                 # 6X (0.875)
BAR_C = 1.525 / 2             # bar centre x
XO = BAR_C + BAR_L / 2        # 1.2: outer x edge
L_H = 0.825                   # 2X (0.825): horizontal leg of pins 7 and 9
LEG = 0.4                     # 4X (0.4): legs beyond the horizontal leg
YO = 2.55 / 2                 # 1.275: outer y edge
LEG_X = 0.5                   # 2X (1): legs of pins 3 and 4
SMALL_H = 0.65                # pin 8 (0.65)
RR = round(0.05 / W, 4)       # R0.05 corners

BX, BY, HEIGHT = 2.0, 2.2, 0.85   # body nominal; A 0.8..0.9


def leg_pad(num, sx, sy, h_len, leg_cx):
    """Horizontal leg at |y| = 0.75 from the outer edge, h_len long; a leg W wide centred at |x| = leg_cx out to
    the package end (sy side)."""
    hy = sy * 0.75
    ax, ay = sx * (XO - h_len / 2), hy
    lx0, lx1 = sx * (leg_cx - W / 2), sx * (leg_cx + W / 2)
    ly0, ly1 = hy + sy * W / 2, sy * YO
    leg = [(lx0 - ax, ly0 - ay), (lx1 - ax, ly0 - ay), (lx1 - ax, ly1 - ay), (lx0 - ax, ly1 - ay)]
    return custom_pad(num, (ax, ay), (h_len, W), [leg])


def pads():
    inner_end = XO - L_H                       # 0.375: the inner end of the 0.825 legs
    return [
        leg_pad(9, -1, -1, L_H, inner_end + W / 2),
        smd_pad(1, -BAR_C, -0.25, BAR_L, W, rratio=RR),
        smd_pad(2, -BAR_C, 0.25, BAR_L, W, rratio=RR),
        leg_pad(3, -1, 1, BAR_L, LEG_X),
        leg_pad(4, 1, 1, BAR_L, LEG_X),
        smd_pad(5, BAR_C, 0.25, BAR_L, W, rratio=RR),
        smd_pad(6, BAR_C, -0.25, BAR_L, W, rratio=RR),
        leg_pad(7, 1, -1, L_H, inner_end + W / 2),
        smd_pad(8, 0, -(YO - SMALL_H / 2), W, SMALL_H, rratio=RR),
    ]


def footprint():
    hx, hy = BX / 2, BY / 2
    crt_x = up(max(XO, hx) + CRT_CLR, 0.05)
    crt_y = up(max(YO, hy) + CRT_CLR, 0.05)
    sy = YO + SILK_PAD + SILK_W / 2
    sx = XO + SILK_PAD + SILK_W / 2
    # pin 1 arrow left of pin 1 (second row; the index corner, top left, is pin 9's)
    arrow = poly([(-sx, -0.25), (-sx - 0.33, -0.25 - 0.24), (-sx - 0.33, -0.25 + 0.24)], "F.SilkS", SILK_W)
    marks = [line(hx - 0.3, sy, sx, sy, "F.SilkS", SILK_W), line(sx, sy, sx, sy - 0.3, "F.SilkS", SILK_W),
             line(hx - 0.3, -sy, sx, -sy, "F.SilkS", SILK_W), line(sx, -sy, sx, -sy + 0.3, "F.SilkS", SILK_W),
             line(-hx + 0.3, sy, -sx, sy, "F.SilkS", SILK_W), line(-sx, sy, -sx, sy - 0.3, "F.SilkS", SILK_W)]
    descr = (f"TI RYT0009A VQFN-HR (HotRod), 9 pins, 2x2.2mm, 0.5mm pitch, corner pins with legs to the package "
             f"end (TPS62903-Q1 data sheet SLVSG65A, drawing 4226765/B, example board layout p. 50), "
             f"{DATASHEET}#page=49")
    body = [
        text("Reference", "REF**", -crt_y - 0.8, "F.SilkS"),
        text("Value", NAME, crt_y + 0.8, "F.Fab"),
        arrow, *marks,
        rect(-crt_x, -crt_y, crt_x, crt_y, "F.CrtYd", CRT_W),
        chamfered_rect(-hx, -hy, hx, hy, 0.5, "F.Fab", FAB_W),
        fab_ref(0.5),
        *pads(),
        model_ref(LIB, NAME),
    ]
    return footprint_text(NAME, descr, "VQFN QFN VQFN-HR HotRod RYT0009A", body)


def model():
    import cadquery as cq

    def box(x0, x1, y0, y1, z0, z1):
        return (cq.Workplane("XY").box(abs(x1 - x0), abs(y1 - y0), z1 - z0)
                .translate(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)))

    hx, hy, t = BX / 2, BY / 2, 0.2           # ESTIMATE: terminal (lead frame) thickness
    tl = 0.675                                # 6X 0.575..0.775 terminal length from the body edge
    body = box(-hx, hx, -hy, hy, 0.0, HEIGHT)
    terms = None

    def add(b):
        nonlocal terms
        terms = b if terms is None else terms.union(b)

    # Terminals follow the lands inside the body outline (ESTIMATE: the drawing gives widths and the 0.675
    # terminal length, not every leg); 0.25 wide
    for y in (-0.25, 0.25):
        for sx in (-1, 1):
            add(box(sx * hx, sx * (hx - tl), y - 0.125, y + 0.125, -0.001, t))
    for sx in (-1, 1):
        add(box(sx * hx, sx * (XO - L_H), -0.875, -0.625, -0.001, t))                     # 9 / 7 horizontal
        add(box(sx * (XO - L_H), sx * (XO - L_H + W), -hy, -0.875, -0.001, t))           # 9 / 7 leg
        add(box(sx * hx, sx * (XO - BAR_L), 0.625, 0.875, -0.001, t))                    # 3 / 4 horizontal
        add(box(sx * (LEG_X - W / 2), sx * (LEG_X + W / 2), 0.875, hy, -0.001, t))       # 3 / 4 leg
    add(box(-0.125, 0.125, -hy, -hy + 0.475, -0.001, t))                                  # 8 (0.375..0.575)
    body = body.cut(terms)
    dot = (cq.Workplane("XY").workplane(offset=HEIGHT - 0.02).center(-hx + 0.4, -hy + 0.4)
           .circle(0.12).extrude(0.03))       # ESTIMATE: index dot in the drawing's pin 1 index area
    body = body.cut(dot)
    # KiCad's model Y is the footprint's -y: mirror so the index stays top left
    return [(body.mirror("XZ"), BODY), (terms.mirror("XZ"), METAL)]


if __name__ == "__main__":
    print("footprint ", write_footprint(LIB, NAME, footprint()))
    print("3D model  ", write_model(LIB, NAME, model()))
