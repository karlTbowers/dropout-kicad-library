#!/usr/bin/env python3
"""Amphenol SINE BoardLock ATM13-2P-BMxx right-angle PCB receptacle footprint and 3D model (no
generator covers it). One footprint serves all four versions (BM01 gold/unpotted, BM02 gold/potted,
BM03 tin/unpotted, BM04 tin/potted): they share drawing ATM13-2P-BMXX.

Usage: ~/.cache/dropout/klt-venv/bin/python generators/custom/Amphenol_SINE_ATM13-2P.py

Sources (archived in dropout-vendor-docs, Amphenol-SINE/ATM/):
- Holes: drawing ATM13-2P-BMXX rev. A2 (10 Jul 2020), "Recommended PCB layout, view from components
  side of PCB": 2x Ø1.20 +0.2/-0 pin holes 4.20 apart; 3x Ø3.43 holes for #4-20 thread-forming
  screws (inserted from the solder side into the housing bosses, 0.68-1.13 N-m): one on the pin
  centreline 6.00 from the pin row toward the mating face, two 18.02 apart, 12.35 from it
  (6.35 behind the pin row; outer screw to nearer pin 6.91).
- Body: same drawing. Flange 36.8 x 27.0 with the flange seal face 16.5 in front of the pin row
  (top boss 10.5 behind it, pins 6.0 further), overall length 39.7, 26.8 from the rear to the flange
  face, mating shroud 16.6 x 16.2, pins Ø1.0 with tails 3.05 below the boss faces. The rear deck
  width and the heights are read from the drawing views (not dimensioned): the 3D model is an
  envelope, not a manufacturer model.
- Pin numbering: the drawing's mounting-face (bottom) view marks PIN #1 on the left with the
  mating face up; seen from the component side with the mating face toward +y, pin 1 is on the
  left (x = 0) and pin 2 on the right. Check against the cavity letters moulded on a sample.

Origin at pin 1, mating face toward +y (the panel / board edge side).
"""
from fplib import (CRT_W, FAB_W, METAL, SILK_W, footprint_text, line, model_ref, poly,
                   r, text, up, write_footprint, write_model)

LIB = "DropOut_Connector_Amphenol"
NAME = "Amphenol_SINE_ATM13-2P-BMxx_1x02_P4.20mm_Horizontal"
DRAWING = "https://www.amphenol-sine.com/pdf/datasheet/ATM13-2P-BM04.pdf"

PITCH = 4.20
XC = PITCH / 2                  # pin-pair centreline
PIN_DRILL = 1.3                 # Ø1.20 +0.2/-0 (drawing), mid-tolerance
PIN_PAD = 2.2                   # 0.45 mm annular ring, size 20 contact (7.5 A)
SCREW_DRILL = 3.43              # Ø3.43 (drawing), NPTH
SCREWS = [(XC, 6.00), (XC - 18.02 / 2, 6.00 - 12.35), (XC + 18.02 / 2, 6.00 - 12.35)]
CRT_CLR = 0.5                   # KLC F5.3: connectors

FLANGE_FACE = 16.5              # 10.5 + 6.0 from the pin row
REAR = FLANGE_FACE - 26.8       # -10.3
FRONT = REAR + 39.7             # 29.4, mating face
# Body outline seen from above, from the rear (-y) to the mating face (+y): (y0, y1, half width,
# height). None = the shroud, which does not reach the board.
SECTIONS = [
    (REAR, 1.8, 12.0, 6.0),             # rear deck with the two outer screw bosses
    (1.8, FLANGE_FACE, 18.4, 25.5),     # housing and flange, 36.8 wide, 27.0 tall (1.5 below the board top)
    (FLANGE_FACE, FRONT, 8.3, None),    # mating shroud 16.6 x 16.2 through the panel cutout
]
AXIS_Z = 9.3                            # mating axis above the board (read from the side view)
SHROUD_Z = (AXIS_Z - 8.1, AXIS_Z + 8.1)
TAIL = 3.05
PIN_D = 1.0


def stepped(offset):
    """Stepped outline grown by offset, corners on the grown contour."""
    ys = [s[0] for s in SECTIONS] + [SECTIONS[-1][1]]
    hws = [s[2] for s in SECTIONS]
    right = [(XC + hws[0] + offset, ys[0] - offset)]
    for i in range(len(hws) - 1):
        a, b = hws[i], hws[i + 1]
        yb = ys[i + 1] - offset if b > a else ys[i + 1] + offset
        right += [(XC + a + offset, yb), (XC + b + offset, yb)]
    right.append((XC + hws[-1] + offset, ys[-1] + offset))
    left = [(2 * XC - x, y) for x, y in right]
    return right + left[::-1] + [right[0]]


def polyline(pts, layer, w):
    return "\n".join(line(*pts[i], *pts[i + 1], layer, w) for i in range(len(pts) - 1))


def tht_pad(num, x, y, shape):
    extra = " (roundrect_rratio 0.25)" if shape == "roundrect" else ""
    return (f'\t(pad "{num}" thru_hole {shape} (at {r(x)} {r(y)}) (size {PIN_PAD} {PIN_PAD}) '
            f'(drill {PIN_DRILL})\n\t\t(layers "*.Cu" "*.Mask"){extra})')


def npth(x, y):
    return (f'\t(pad "" np_thru_hole circle (at {r(x)} {r(y)}) (size {SCREW_DRILL} {SCREW_DRILL}) '
            f'(drill {SCREW_DRILL})\n\t\t(layers "*.Cu" "*.Mask"))')


def footprint():
    fab = stepped(0)
    silk_off = FAB_W / 2 + SILK_W / 2 + 0.04          # 0.15 outside the body line
    silk = stepped(silk_off)
    yc = (REAR + FRONT) / 2
    crt = [(XC + up(x - XC, 0.01), yc + up(y - yc, 0.01)) for x, y in stepped(CRT_CLR)]
    top = SECTIONS[0][0] - silk_off
    # pin 1 marker: silk triangle on the rear edge above pin 1, fab triangle inside the body edge
    tri = [(0, top - 0.05), (-0.45, top - 0.45), (0.45, top - 0.45), (0, top - 0.05)]
    ftri = [(-0.8, SECTIONS[0][0]), (0, SECTIONS[0][0] + 0.8), (0.8, SECTIONS[0][0])]
    body = [
        text("Reference", "REF**", SECTIONS[0][0] - CRT_CLR - 1.0, "F.SilkS"),
        text("Value", NAME, FRONT + CRT_CLR + 1.0, "F.Fab"),
        polyline(silk, "F.SilkS", SILK_W),
        poly(tri, "F.SilkS", SILK_W),
        polyline(fab, "F.Fab", FAB_W),
        polyline(ftri, "F.Fab", FAB_W),
        polyline(crt, "F.CrtYd", CRT_W),
        line(XC - SECTIONS[1][2], FLANGE_FACE, XC + SECTIONS[1][2], FLANGE_FACE, "Cmts.User", FAB_W),
        f'\t(fp_text user "panel / flange seal face" (at {r(XC)} {r(FLANGE_FACE - 1.0)} 0) (layer "Cmts.User")\n'
        f'\t\t(effects (font (size 1 1) (thickness 0.15))))',
        f'\t(fp_text user "3x #4-20 thread-forming screws from the solder side, 0.68-1.13 N-m" (at {r(XC)} {r(FRONT + CRT_CLR + 2.6)} 0) (layer "Cmts.User")\n'
        f'\t\t(effects (font (size 0.8 0.8) (thickness 0.12))))',
        f'\t(fp_text user "${{REFERENCE}}" (at {r(XC)} 11.0 0) (layer "F.Fab")\n'
        f'\t\t(effects (font (size 1 1) (thickness 0.15))))',
        tht_pad(1, 0, 0, "roundrect"), tht_pad(2, PITCH, 0, "circle"),
        *[npth(x, y) for x, y in SCREWS],
        model_ref(LIB, NAME),
    ]
    descr = ("Amphenol SINE BoardLock ATM13-2P-BMxx 2-pin right-angle PCB receptacle with flange (mates ATM06-2S), "
             "4.20 mm pitch, 3x #4-20 screw bosses; PCB layout and body per drawing ATM13-2P-BMXX rev. A2, "
             f"{DRAWING}")
    tags = "connector Amphenol SINE ATM ATM13 ATM13-2P ATM06-2S BoardLock horizontal right angle sealed automotive"
    return footprint_text(NAME, descr, tags, body, attr="through_hole")


def model():
    import cadquery as cq
    box = lambda x0, x1, y0, y1, z0, z1: cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0) \
        .translate(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    housing = None
    for y0, y1, hw, h in SECTIONS:
        z0, z1 = (0, h) if h else SHROUD_Z
        b = box(XC - hw, XC + hw, y0, y1, z0, z1)
        housing = b if housing is None else housing.union(b)
    housing = housing.cut(box(XC - 6.8, XC + 6.8, FRONT - 11.0, FRONT + 1, AXIS_Z - 6.6, AXIS_Z + 6.6))
    for x, y in SCREWS:                                 # screw holes in the bosses
        housing = housing.cut(cq.Workplane("XY").circle(2.79 / 2).extrude(6.4).translate((x, y, -1)))
    metal = None
    for x in (0, PITCH):
        tail = cq.Workplane("XY").circle(PIN_D / 2).extrude(TAIL + 1.0).translate((x, 0, -TAIL))
        mate = cq.Workplane("XZ").circle(PIN_D / 2).extrude(-9.0).translate((x, FRONT - 11.0, AXIS_Z))
        part = tail.union(mate)
        metal = part if metal is None else metal.union(part)
    return [(housing, (0.55, 0.56, 0.58)), (metal, METAL)]


if __name__ == "__main__":
    print("footprint ", write_footprint(LIB, NAME, footprint()))
    print("3D model  ", write_model(LIB, NAME, model()))
