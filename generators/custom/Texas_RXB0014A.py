#!/usr/bin/env python3
"""TI RXB0014A (VQFN-FCRLF / HotRod, 14 pins + thermal pad, 2.6 x 2.6 mm) footprint and 3D model.

Usage: ~/.cache/dropout/klt-venv/bin/python generators/custom/Texas_RXB0014A.py

The corner pins 1, 5, 8, 12 are L-shaped, which no kicad-library-tools generator makes.
Source: TI drawing 4225574/C (02/2021), LMQ664x0-Q1 datasheet SNVSBV1F pages 55-57:
package outline, example board layout (land pattern) and example stencil. Top view, pin 1
top-left, numbered counter-clockwise; the thermal pad is pad 15 (TI's number).
"""
from fplib import (BODY, CRT_CLR, CRT_W, FAB_W, METAL, SILK_PAD, SILK_W, chamfered_rect, custom_pad,
                   fab_ref, footprint_text, model_ref, poly, rect, smd_pad, text, up, write_footprint,
                   write_model)

LIB = "DropOut_Package_DFN_QFN"
NAME = "Texas_RXB0014A_VQFN-14-1EP_2.6x2.6mm_P0.5mm_EP1x1mm"
DATASHEET = "https://www.ti.com/lit/ds/symlink/lmq66430-q1.pdf"

# Land pattern (example board layout)
ROW = 1.15                 # pad centre lines: (2.3) between opposite rows/columns
PAD_L, PAD_W = 0.70, 0.25  # 10X (0.7) x 18X (0.25)
PITCH = 0.5                # 10X (0.5)
CORNER_ROW = 0.5 + 0.525   # 4X (0.525) beyond the last side pad
LEG_H = 0.875              # 4X (0.875) corner leg along x
LEG_V = 0.60               # 4X (0.6) corner leg along y
OUTER = ROW + PAD_L / 2    # 1.5: outer edge of every pad
EP = 1.0                   # (square 1)
EP_PASTE = 0.95            # stencil: 1X (square 0.95)

# Package (outline)
BODY_SIZE = 2.6            # 2.5..2.7
HEIGHT = 1.0               # 0.95..1.05
TERM_LEN = 0.5             # 10X 0.4..0.6
CORNER_TERM = 0.675        # 4X 0.575..0.775


def l_pad(num, sx, sy):
    """Corner L pad for the quadrant (sx, sy) in {-1, 1}^2; anchor = the horizontal leg."""
    hx0, hx1 = sx * OUTER, sx * (OUTER - LEG_H)
    hy0, hy1 = sy * (CORNER_ROW + PAD_W / 2), sy * (CORNER_ROW - PAD_W / 2)
    ax, ay = (hx0 + hx1) / 2, (hy0 + hy1) / 2
    vx0, vx1 = sx * (OUTER - LEG_H), sx * (OUTER - LEG_H + PAD_W)
    vy0, vy1 = sy * OUTER, sy * (OUTER - LEG_V)
    leg = [(vx0 - ax, vy0 - ay), (vx1 - ax, vy0 - ay), (vx1 - ax, vy1 - ay), (vx0 - ax, vy1 - ay)]
    return custom_pad(num, (ax, ay), (LEG_H, PAD_W), [leg])


def pads():
    out = [l_pad(1, -1, -1)]
    out += [smd_pad(n, -ROW, y, PAD_L, PAD_W) for n, y in ((2, -PITCH), (3, 0), (4, PITCH))]
    out += [l_pad(5, -1, 1)]
    out += [smd_pad(n, x, ROW, PAD_W, PAD_L) for n, x in ((6, -PITCH / 2), (7, PITCH / 2))]
    out += [l_pad(8, 1, 1)]
    out += [smd_pad(n, ROW, y, PAD_L, PAD_W) for n, y in ((9, PITCH), (10, 0), (11, -PITCH))]
    out += [l_pad(12, 1, -1)]
    out += [smd_pad(n, x, -ROW, PAD_W, PAD_L) for n, x in ((13, PITCH / 2), (14, -PITCH / 2))]
    out += [smd_pad(15, 0, 0, EP, EP, rratio=0.05,
                    extra=f" (solder_paste_margin {-(EP - EP_PASTE) / 2})")]
    return out


def footprint():
    crt = up(max(OUTER, BODY_SIZE / 2) + CRT_CLR)
    tip = OUTER + SILK_PAD + SILK_W / 2           # pin-1 arrow tip, clear of the corner pad
    arrow = poly([(-tip, -tip), (-tip - 0.24, -tip - 0.33), (-tip + 0.24, -tip - 0.33)], "F.SilkS", SILK_W)
    h = BODY_SIZE / 2
    body = [
        text("Reference", "REF**", -crt - 0.8, "F.SilkS"),
        text("Value", NAME, crt + 0.8, "F.Fab"),
        arrow,
        rect(-crt, -crt, crt, crt, "F.CrtYd", CRT_W),
        chamfered_rect(-h, -h, h, h, 0.65, "F.Fab", FAB_W),
        fab_ref(0.6),
        *pads(),
        model_ref(LIB, NAME),
    ]
    descr = (f"TI RXB0014A VQFN-FCRLF (HotRod), 14 pins + thermal pad 15, 2.6x2.6mm, L-shaped corner pins; "
             f"land pattern per TI drawing 4225574/C (LMQ664x0-Q1 datasheet SNVSBV1F p. 56), {DATASHEET}#page=56")
    return footprint_text(NAME, descr, "VQFN QFN HotRod FCRLF RXB0014A", body)


def model():
    import cadquery as cq
    box = lambda x0, x1, y0, y1, z0, z1: cq.Workplane("XY").box(abs(x1 - x0), abs(y1 - y0), z1 - z0) \
        .translate(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    h, t = BODY_SIZE / 2, 0.2
    body = box(-h, h, -h, h, 0.0, HEIGHT)
    terms = box(-EP / 2, EP / 2, -EP / 2, EP / 2, -0.001, 0.02)
    for y in (-PITCH, 0, PITCH):
        terms = terms.union(box(-h, -h + TERM_LEN, y - PAD_W / 2, y + PAD_W / 2, -0.001, t))
        terms = terms.union(box(h - TERM_LEN, h, y - PAD_W / 2, y + PAD_W / 2, -0.001, t))
    for x in (-PITCH / 2, PITCH / 2):
        terms = terms.union(box(x - PAD_W / 2, x + PAD_W / 2, -h, -h + TERM_LEN, -0.001, t))
        terms = terms.union(box(x - PAD_W / 2, x + PAD_W / 2, h - TERM_LEN, h, -0.001, t))
    for sx in (-1, 1):
        for sy in (-1, 1):
            xo = sx * h
            terms = terms.union(box(xo, xo - sx * CORNER_TERM, sy * (CORNER_ROW - PAD_W / 2),
                                    sy * (CORNER_ROW + PAD_W / 2), -0.001, t))
    body = body.cut(terms)
    return [(body, BODY), (terms, METAL)]


if __name__ == "__main__":
    print("footprint ", write_footprint(LIB, NAME, footprint()))
    print("3D model  ", write_model(LIB, NAME, model()))
