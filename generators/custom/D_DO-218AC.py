#!/usr/bin/env python3
"""DO-218AC footprint and 3D model (no kicad-library-tools generator covers DO-218).

Usage: ~/.cache/dropout/klt-venv/bin/python generators/custom/D_DO-218AC.py

Source: Vishay XLD8A24CA datasheet (doc 87200, rev. 23-Jan-2026) page 4, "Package outline
dimensions" and "Mounting Pad Layout" (IPC-7351). Lead 1 is the small bent lead; lead 2 is
the metal heatsink under the body. The origin is the centre of the 15.30 mm pad span, within
0.1 mm of the package centre (outline 15.0..16.0 mm).
"""
from fplib import (BODY, CRT_CLR, CRT_W, FAB_W, METAL, SILK_PAD, SILK_W, fab_ref, footprint_text, line,
                   model_ref, rect, smd_pad, text, up, write_footprint, write_model)

LIB = "DropOut_Diode_SMD"
NAME = "D_DO-218AC"
DATASHEET = "https://www.vishay.com/doc?87200"

# Mounting pad layout (mm)
SPAN = 15.30                     # big pad left edge to small pad right edge
BIG = (9.80, 10.70)              # lead 2 / heatsink pad
SMALL = (2.15, 2.60)             # lead 1 pad
GAP = 3.35
assert abs(BIG[0] + GAP + SMALL[0] - SPAN) < 1e-9
PAD2_X = -SPAN / 2 + BIG[0] / 2  # -2.75
PAD1_X = SPAN / 2 - SMALL[0] / 2  # 6.575

# Package outline (nominal of min..max), aligned to the pad span centre
BODY_LEN = 13.5                  # 13.3..13.7
BODY_W = 8.5                     # moulded body 8.3..8.7
OVERALL_W = 10.0                 # with heatsink flanges 9.5..10.5
OVERALL_LEN = 15.5               # body + lead 1, 15.0..16.0
HEIGHT = 4.85                    # 4.7..5.0
SINK_LEN = 10.0                  # heatsink 9.7..10.3
LEAD_W = 2.7                     # lead 1 width 2.4..3.0
LEAD_T = 0.6                     # lead thickness 0.5..0.7
LEAD_H = 3.0                     # lead 1 bend height 2.5..3.5
BODY_X0 = -OVERALL_LEN / 2
BODY_X1 = BODY_X0 + BODY_LEN
LEAD_X1 = OVERALL_LEN / 2


def footprint():
    crt_x = up(max(LEAD_X1, SPAN / 2) + CRT_CLR, 0.05)
    crt_y = up(max(BIG[1] / 2, OVERALL_W / 2) + CRT_CLR, 0.05)
    sy = OVERALL_W / 2 + SILK_W / 2 + 0.05                 # silk just outside the body
    sx0 = PAD2_X + BIG[0] / 2 + SILK_PAD + SILK_W / 2       # clear of the heatsink pad
    sx1 = BODY_X1 + SILK_W / 2 + 0.05
    sy_lead = SMALL[1] / 2 + SILK_PAD + SILK_W / 2           # clear of the lead pad
    body = [
        text("Reference", "REF**", -crt_y - 0.8, "F.SilkS"),
        text("Value", NAME, crt_y + 0.8, "F.Fab"),
        line(sx0, -sy, sx1, -sy, "F.SilkS", SILK_W), line(sx1, -sy, sx1, -sy_lead, "F.SilkS", SILK_W),
        line(sx0, sy, sx1, sy, "F.SilkS", SILK_W), line(sx1, sy, sx1, sy_lead, "F.SilkS", SILK_W),
        rect(-crt_x, -crt_y, crt_x, crt_y, "F.CrtYd", CRT_W),
        rect(BODY_X0, -OVERALL_W / 2, BODY_X1, OVERALL_W / 2, "F.Fab", FAB_W),
        line(BODY_X1, -LEAD_W / 2, LEAD_X1, -LEAD_W / 2, "F.Fab", FAB_W),
        line(LEAD_X1, -LEAD_W / 2, LEAD_X1, LEAD_W / 2, "F.Fab", FAB_W),
        line(LEAD_X1, LEAD_W / 2, BODY_X1, LEAD_W / 2, "F.Fab", FAB_W),
        fab_ref(),
        smd_pad(1, PAD1_X, 0, *SMALL, rratio=0.025), smd_pad(2, PAD2_X, 0, *BIG, rratio=0.025),
        model_ref(LIB, NAME),
    ]
    descr = f"DO-218AC (Vishay XLD8A24CA datasheet doc 87200 p. 4, mounting pad layout per IPC-7351), {DATASHEET}"
    return footprint_text(NAME, descr, "diode TVS DO-218AC DO-218", body)


def model():
    import cadquery as cq
    box = lambda x0, x1, w, z0, z1: cq.Workplane("XY").box(x1 - x0, w, z1 - z0) \
        .translate(((x0 + x1) / 2, 0, (z0 + z1) / 2))
    body = box(BODY_X0, BODY_X1, BODY_W, 0.1, HEIGHT).edges("|Z").fillet(0.3)
    metal = box(BODY_X0, BODY_X0 + SINK_LEN, OVERALL_W, 0.0, 0.5) \
        .union(box(PAD1_X - SMALL[0] / 2, LEAD_X1, LEAD_W, 0.0, LEAD_T)) \
        .union(box(LEAD_X1 - LEAD_T, LEAD_X1, LEAD_W, 0.0, LEAD_H)) \
        .union(box(BODY_X1, LEAD_X1, LEAD_W, LEAD_H - LEAD_T, LEAD_H))
    return [(body, BODY), (metal, METAL)]


if __name__ == "__main__":
    print("footprint ", write_footprint(LIB, NAME, footprint()))
    print("3D model  ", write_model(LIB, NAME, model()))
