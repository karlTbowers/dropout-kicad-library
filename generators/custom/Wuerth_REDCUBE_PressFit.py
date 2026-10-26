#!/usr/bin/env python3
"""Würth Elektronik REDCUBE PRESS-FIT power terminal footprints and 3D models (no generator covers
press-fit pin arrays).

Usage: ~/.cache/dropout/klt-venv/bin/python generators/custom/Wuerth_REDCUBE_PressFit.py

Sources (archived in dropout-vendor-docs, Wuerth/REDCUBE/):
- 7461068 WP-RAFU, right angled, M8 (data sheet rev. 001.004, 2025-12-22, p. 1): 5 x 5 press-fit
  pins at 2.54 (10.16 grid), 13.0 square pin plate, body 20.0 above the board, pins 3.5 below,
  PCB 1.6 to 3.2 thick, 250 A.
- 786202106 WP-PFIFUA, M6 blind thread, 10 mm (data sheet rev. 001.003, 2024-09-26, p. 1): 4 x 4
  press-fit pins at 2.54 (7.62 grid), 10.0 square body 10.5 above the board, pins 3.0 below, PCB
  1.6 to 2.7 thick, 180 A. "Recommended hole pattern": no components within 4 mm of the REDCUBE, and
  not within 3 mm of the PCB edge; the courtyard is drawn at the 4 mm keep-out.
- Holes (both): drill Ø1.60 -0.03 before plating, 25 to 60 µm copper, finished Ø1.475 ±0.05 for
  chemical surfaces (Ø1.45 ±0.05 for HAL). The footprint drill is the finished Ø1.475.
- Press-fit pins: one electrical terminal, so every pad is numbered "1" and the symbol has one pin
  (as KiCad's stock REDCUBE footprints; user's decision 2026-10-26). Press in one movement, no
  rework or soldering afterwards, 0.1 mm min. gap under the part (Würth notes).
- 3D models are envelopes built here (Würth's STEP downloads are not redistributed).

Origin at the centre of the pin grid.
"""
from fplib import (CRT_CLR, CRT_W, FAB_W, METAL, SILK_W, footprint_text, line, model_ref, r, rect,
                   text, up, write_footprint, write_model)

LIB = "DropOut_TerminalBlock_Wuerth"
PITCH = 2.54
FINISHED = 1.475                 # Ø1.475 ±0.05 finished hole (chemical Sn / ENIG)
PAD = 2.1                        # 0.31 mm annular ring, 0.44 mm between pads of the same terminal
BRASS = (0.80, 0.62, 0.30)

PARTS = {
    "Wuerth_REDCUBE-PRESS-FIT_WP-RAFU_7461068_PressFit": dict(
        n=5, body=13.0, height=20.0, tail=3.5, keepout=None, thread=("x", 8.0, 12.0),
        descr="Würth REDCUBE PRESS-FIT WP-RAFU, right angled, M8, 25 press-fit pins 2.54 mm, 250 A "
              "(data sheet 7461068 rev. 001.004 p. 1), https://www.we-online.com/components/products/datasheet/7461068.pdf",
        tags="REDCUBE press-fit power terminal M8 right angle WP-RAFU 7461068"),
    "Wuerth_REDCUBE-PRESS-FIT_WP-PFIFUA_786202106_PressFit": dict(
        n=4, body=10.0, height=10.5, tail=3.0, keepout=4.0, thread=("z", 6.0, 6.0),
        descr="Würth REDCUBE PRESS-FIT WP-PFIFUA, M6 blind thread, 16 press-fit pins 2.54 mm, 180 A, "
              "4 mm component keep-out (data sheet 786202106 rev. 001.003 p. 1), "
              "https://www.we-online.com/components/products/datasheet/786202106.pdf",
        tags="REDCUBE press-fit power terminal M6 WP-PFIFUA 786202106 automotive"),
}


def pins(n):
    o = (n - 1) * PITCH / 2
    return [(-o + i * PITCH, -o + j * PITCH) for j in range(n) for i in range(n)]


def tht_pad(x, y):
    return (f'\t(pad "1" thru_hole circle (at {r(x)} {r(y)}) (size {PAD} {PAD}) (drill {FINISHED})\n'
            f'\t\t(layers "*.Cu" "*.Mask"))')


def footprint(name, p):
    h = p["body"] / 2
    crt = up(h + (p["keepout"] if p["keepout"] else CRT_CLR), 0.05)
    s = h + FAB_W / 2 + SILK_W / 2 + 0.04
    notes = ["Drill Ø1.60 -0.03 before plating, Cu 25-60 µm; finished Ø1.475 (chem.) / Ø1.45 (HAL)",
             "Press-fit in one movement; no rework or soldering after insertion"]
    if p["keepout"]:
        notes.append("Courtyard = Würth 4 mm component keep-out; keep 3 mm from the PCB edge")
    body = [
        text("Reference", "REF**", -crt - 1.0, "F.SilkS"),
        text("Value", name, crt + 1.0, "F.Fab"),
        rect(-s, -s, s, s, "F.SilkS", SILK_W),
        rect(-h, -h, h, h, "F.Fab", FAB_W),
        rect(-crt, -crt, crt, crt, "F.CrtYd", CRT_W),
        *[f'\t(fp_text user "{t}" (at 0 {r(crt + 2.4 + 1.2 * i)} 0) (layer "Cmts.User")\n'
          f'\t\t(effects (font (size 0.8 0.8) (thickness 0.12))))' for i, t in enumerate(notes)],
        f'\t(fp_text user "${{REFERENCE}}" (at 0 0 0) (layer "F.Fab")\n\t\t(effects (font (size 1 1) (thickness 0.15))))',
        *[tht_pad(x, y) for x, y in pins(p["n"])],
        model_ref(LIB, name),
    ]
    return footprint_text(name, p["descr"], p["tags"], body, attr="through_hole")


def model(p):
    import cadquery as cq
    h, top = p["body"] / 2, p["height"]
    block = cq.Workplane("XY").box(2 * h, 2 * h, top - 0.1).translate((0, 0, 0.1 + (top - 0.1) / 2))
    axis, d, zc = p["thread"]
    if axis == "z":                                   # blind thread from the top
        block = block.cut(cq.Workplane("XY").circle(d / 2).extrude(top).translate((0, 0, top - 6.0)))
    else:                                             # through thread, axis along x
        block = block.cut(cq.Workplane("YZ").circle(d / 2).extrude(2 * h + 2).translate((-h - 1, 0, zc)))
    tails = None
    for x, y in pins(p["n"]):
        t = cq.Workplane("XY").box(0.8, 0.8, p["tail"] + 0.1).translate((x, y, -(p["tail"] + 0.1) / 2 + 0.1))
        tails = t if tails is None else tails.union(t)
    # KiCad's model Y is the footprint's -y; these models are symmetric, so no mirror is needed
    return [(block, BRASS), (tails, METAL)]


if __name__ == "__main__":
    for name, p in PARTS.items():
        print("footprint ", write_footprint(LIB, name, footprint(name, p)))
        print("3D model  ", write_model(LIB, name, model(p)))
