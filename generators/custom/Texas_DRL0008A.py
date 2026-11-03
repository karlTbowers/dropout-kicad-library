#!/usr/bin/env python3
"""TI DRL0008A: SOT-5X3 (SOT-583), 8 flat leads, 0.5 mm pitch, 1.2 x 2.1 mm body, 0.6 mm max height.
Used by the TPS62850x-Q1 bucks (TPS628501QDRLRQ1, TPS628502QDRLRQ1, TPS628503QDRLRQ1).

Usage: ~/.cache/dropout/klt-venv/bin/python generators/custom/Texas_DRL0008A.py

Source: TPS62850x-Q1 data sheet SLUSDM0N (May 2020, revised January 2026), DRL0008A drawing 4224486/G 11/2024:
- Package outline (p. 44): body E1 1.1..1.3 (x) by D 2.0..2.2 (y, note 3: no mould flash), lead span E 1.5..1.7,
  8X b 0.17..0.27, foot L 0.2..0.4 (bottom view), c 0.08..0.18, A 0.6 max, A1 0.00..0.05, body draft 4..15 deg,
  6X pitch 0.5, pins 1-4 down the left with the pin 1 ID area at pin 1, 5-8 up the right (JEDEC MO-293 UDAD).
- Example board layout (p. 45): 8X (0.67) x (0.3) lands, (R0.05) corners, rows (1.48) centre to centre, 6X (0.5)
  pitch; non-solder-mask-defined preferred (mask 0.05 max around the land: the board's default mask margin).
- Example stencil design (p. 46, 0.1 mm stencil): apertures 8X (0.67) x (0.3), the same as the lands, so the paste
  layer follows the pads.
KiCad's stock Package_TO_SOT_SMD:SOT-583-8 has the same lands (0.67 x 0.3 at x +/-0.74, y +/-0.25/0.75); this one is
built from TI's drawing so the body, fab outline and model follow DRL0008A.
3D model dimensions the drawing does not give are marked ESTIMATE.
"""
from fplib import (CRT_CLR, CRT_W, FAB_W, METAL, SILK_PAD, SILK_W, chamfered_rect, fab_ref, footprint_text,
                   line, model_ref, smd_pad, text, up, write_footprint, write_model)

LIB = "DropOut_Package_TO_SOT_SMD"
NAME = "Texas_DRL0008A_SOT-583-8"
PITCH = 0.5
ROW = 1.48                  # land rows, centre to centre
PAD_W, PAD_H = 0.67, 0.3    # land size (x, y)
RRATIO = round(0.05 / PAD_H, 4)   # R0.05 corners
# pitch multiples: 1-4 down the left (x < 0), 5-8 up the right
PIN_Y = {1: -1.5, 2: -0.5, 3: 0.5, 4: 1.5, 5: 1.5, 6: 0.5, 7: -0.5, 8: -1.5}

BX, BY = 1.2, 2.1           # body E1 x D, nominal
H = 0.55                    # ESTIMATE: body top; A is given only as 0.6 max
SPAN = 1.6                  # E nominal
LW, LL, LT = 0.22, 0.3, 0.13   # b, L, c nominal
DRAFT = 9.5                 # ESTIMATE: middle of the drawing's 4..15 deg body draft

DESCR = ("Texas Instruments DRL0008A SOT-5X3 (SOT-583), 8 pin, 1.2x2.1mm body, 0.6mm max height, 0.5mm pitch, "
         "flat leads (TPS62850x-Q1 data sheet SLUSDM0N, drawing 4224486/G, example board layout p. 45), "
         "https://www.ti.com/lit/ds/symlink/tps628502-q1.pdf#page=44")
TAGS = "SOT-583 SOT583 SOT-5X3 DRL0008A MO-293 flat lead"


def pads():
    return [smd_pad(n, (-1 if n <= 4 else 1) * ROW / 2, PIN_Y[n] * PITCH, PAD_W, PAD_H, rratio=RRATIO)
            for n in PIN_Y]


def footprint():
    x_ext, y_ext = ROW / 2 + PAD_W / 2, 1.5 * PITCH + PAD_H / 2
    hx, hy = BX / 2, BY / 2
    crt_x = up(max(x_ext, hx) + CRT_CLR, 0.05)
    crt_y = up(max(y_ext, hy) + CRT_CLR, 0.05)
    sy = max(y_ext + SILK_PAD, hy) + SILK_W / 2           # silk lines above and below the lands
    return [
        text("Reference", "REF**", -crt_y - 0.8, "F.SilkS"),
        text("Value", NAME, crt_y + 0.8, "F.Fab"),
        line(-x_ext, -sy, hx, -sy, "F.SilkS", SILK_W),       # top line runs out over pin 1: pin 1 mark
        line(-hx, sy, hx, sy, "F.SilkS", SILK_W),
        line(-crt_x, -crt_y, crt_x, -crt_y, "F.CrtYd", CRT_W), line(crt_x, -crt_y, crt_x, crt_y, "F.CrtYd", CRT_W),
        line(crt_x, crt_y, -crt_x, crt_y, "F.CrtYd", CRT_W), line(-crt_x, crt_y, -crt_x, -crt_y, "F.CrtYd", CRT_W),
        chamfered_rect(-hx, -hy, hx, hy, 0.3, "F.Fab", FAB_W),
        fab_ref(0.5),
        *pads(),
        model_ref(LIB, NAME),
    ]


def model():
    import cadquery as cq
    gap = 0.02                                   # ESTIMATE: A1 (0.00..0.05) under the moulded body
    body = cq.Workplane("XY").workplane(offset=gap).rect(BX, BY).extrude(H - gap, taper=DRAFT)
    body = body.faces(">Z").edges().chamfer(0.03)  # ESTIMATE: top edge break
    dot = (cq.Workplane("XY").workplane(offset=H - 0.02).center(-BX / 2 + 0.3, -BY / 2 + 0.35)
           .circle(0.1).extrude(0.03))           # ESTIMATE: index dot in the drawing's pin 1 ID area
    body = body.cut(dot)
    metal = None
    for n, k in PIN_Y.items():
        sx = -1 if n <= 4 else 1
        x0, x1 = sx * (SPAN / 2 - LL), sx * SPAN / 2   # foot L from the lead tip, flat on the board
        lead = cq.Workplane("XY").box(abs(x1 - x0), LW, LT).translate(((x0 + x1) / 2, k * PITCH, LT / 2))
        metal = lead if metal is None else metal.union(lead)
    # KiCad's model Y is the footprint's -y: mirror so the index dot stays at pin 1
    return [(body.mirror("XZ"), (0.15, 0.15, 0.15)), (metal.mirror("XZ"), METAL)]


if __name__ == "__main__":
    print("footprint ", write_footprint(LIB, NAME, footprint_text(NAME, DESCR, TAGS, footprint())))
    print("3D model  ", write_model(LIB, NAME, model()))
