#!/usr/bin/env python3
"""TE DEUTSCH DT13-2P right-angle PCB header footprint and 3D model (no generator covers it).

Usage: ~/.cache/dropout/klt-venv/bin/python generators/custom/TE_DEUTSCH-DT_DT13-2P.py

Sources (archived in dropout-vendor-docs, TE/DT/):
- Holes: TE application specification 114-151046 rev. A, §3.4 p. 5, DT13-2P recommended PCB layout:
  2x Ø1.88±0.05 pin holes at 5.46 pitch, 3x Ø3.43 +0.12/-0 holes for #4-20 Plastite 48 screws
  (inserted from the solder side into the housing bosses), centre screw on the pin centreline
  6.10 from the pin row, outer screws 18.31 apart, 8.00 from the centre screw.
- Body: TE customer drawing DT13-2P rev. B (pins Ø1.56, tails 3.10 below the boss faces,
  1.420 x 1.390 x 1.080 in envelope, flange face .610 from the pin row) and the dimensions of
  TE's own STEP model (CVM 99), which is not redistributed.
- Pin numbering: the drawing's front (mating face) view marks cavity 2; with the mating face
  toward +y and the board below, pin 1 is on the left (x = 0) and pin 2 on the right. The
  application spec's layout figure, labelled "component side", shows the opposite pin under a
  strict reading (it matches the drawing's mounting-face view); the customer drawing takes
  priority (114-151046 §2.3). Check against the cavity numbers moulded on a sample.

Origin at pin 1, mating face toward +y (the panel / board edge side).
"""
from fplib import (CRT_W, FAB_W, METAL, SILK_W, footprint_text, line, model_ref, poly,
                   r, text, up, write_footprint, write_model)

LIB = "DropOut_Connector_TE-Connectivity"
NAME = "TE_DEUTSCH-DT_DT13-2P_1x02_P5.46mm_Horizontal"
DRAWING = "https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocNm=DT13-2P&DocType=Customer%20Drawing&DocLang=English&DocFormat=pdf&PartCntxt=DT13-2P"

PITCH = 5.46
XC = PITCH / 2                  # pin-pair centreline
PIN_DRILL = 1.9                 # Ø1.88 ±0.05 finished (114-151046)
PIN_PAD = 3.2                   # 0.65 mm annular ring for the 13 A contact
SCREW_DRILL = 3.5               # Ø3.43 +0.12/-0 (114-151046), NPTH
SCREWS = [(XC, 6.10), (XC - 18.31 / 2, -(8.00 - 6.10)), (XC + 18.31 / 2, -(8.00 - 6.10))]
CRT_CLR = 0.5                   # KLC F5.3: connectors

# Body outline seen from above, from the rear (-y) to the mating face (+y): (y0, y1, half width).
# Heights above the board (z) from TE's model. Pins sit on y = 0.
SECTIONS = [
    (-5.97, -0.30, 13.22, 3.88),    # rear deck with the two outer screw bosses (.160 behind them)
    (-0.30, 4.00, 16.60, 24.00),    # pin block
    (4.00, 15.49, 17.65, 27.66),    # main housing up to the flange seal face (.610 from the pins)
    (15.49, 30.10, 8.57, None),     # mating shroud, 17.15 x 17.02, through the panel cutout
]
SHROUD_Z = (5.43, 22.45)            # shroud bottom/top; mating axis 13.94 above the board
FRONT = SECTIONS[-1][1]             # mating face, 1.420 in from the rear
TAIL = 3.10                         # pin tail below the boss faces
PIN_D = 1.56


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
    # courtyard on a 0.01 grid, rounded away from the body centre (XC, 12.0)
    crt = [(XC + up(x - XC, 0.01), 12.0 + up(y - 12.0, 0.01)) for x, y in stepped(CRT_CLR)]
    top = SECTIONS[0][0] - silk_off
    # pin 1 marker: silk triangle on the rear edge above pin 1, fab triangle inside the body edge
    tri = [(0, top - 0.05), (-0.45, top - 0.45), (0.45, top - 0.45), (0, top - 0.05)]
    ftri = [(-0.8, SECTIONS[0][0]), (0, SECTIONS[0][0] + 0.8), (0.8, SECTIONS[0][0])]
    y_ref = SECTIONS[0][0] - CRT_CLR - 1.0
    body = [
        text("Reference", "REF**", y_ref, "F.SilkS"),
        text("Value", NAME, FRONT + CRT_CLR + 1.0, "F.Fab"),
        polyline(silk, "F.SilkS", SILK_W),
        poly(tri, "F.SilkS", SILK_W),
        polyline(fab, "F.Fab", FAB_W),
        polyline(ftri, "F.Fab", FAB_W),
        polyline(crt, "F.CrtYd", CRT_W),
        line(XC - SECTIONS[2][2], SECTIONS[2][1], XC + SECTIONS[2][2], SECTIONS[2][1], "Cmts.User", FAB_W),
        f'\t(fp_text user "panel / flange seal face" (at {r(XC)} {r(SECTIONS[2][1] - 1.0)} 0) (layer "Cmts.User")\n'
        f'\t\t(effects (font (size 1 1) (thickness 0.15))))',
        f'\t(fp_text user "3x #4-20 Plastite 48 screws from the solder side, 0.90 N-m" (at {r(XC)} {r(FRONT + CRT_CLR + 2.6)} 0) (layer "Cmts.User")\n'
        f'\t\t(effects (font (size 0.8 0.8) (thickness 0.12))))',
        f'\t(fp_text user "${{REFERENCE}}" (at {r(XC)} 10.5 0) (layer "F.Fab")\n'
        f'\t\t(effects (font (size 1 1) (thickness 0.15))))',
        tht_pad(1, 0, 0, "roundrect"), tht_pad(2, PITCH, 0, "circle"),
        *[npth(x, y) for x, y in SCREWS],
        model_ref(LIB, NAME),
    ]
    descr = ("TE DEUTSCH DT13-2P 2-pin right-angle PCB header (mates DT06-2S), 5.46 mm pitch, panel flange, "
             "3x #4-20 screw bosses; PCB layout per TE 114-151046 rev. A sec. 3.4, body per customer drawing "
             f"DT13-2P rev. B, {DRAWING}")
    tags = "connector TE DEUTSCH DT DT13 DT13-2P DT06-2S horizontal right angle sealed automotive"
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
    zc = sum(SHROUD_Z) / 2
    housing = housing.cut(box(XC - 7.3, XC + 7.3, FRONT - 13.0, FRONT + 1, zc - 7.2, zc + 7.2))
    for x, y in SCREWS:                                 # screw holes in the bosses
        housing = housing.cut(cq.Workplane("XY").circle(2.79 / 2).extrude(6).translate((x, y, -1)))
    metal = None
    for x in (0, PITCH):
        tail = cq.Workplane("XY").circle(PIN_D / 2).extrude(TAIL + 1.0).translate((x, 0, -TAIL))
        mate = cq.Workplane("XZ").circle(PIN_D / 2).extrude(-11.0) \
            .translate((x, FRONT - 13.0, zc))
        part = tail.union(mate)
        metal = part if metal is None else metal.union(part)
    return [(housing, (0.55, 0.56, 0.58)), (metal, METAL)]


if __name__ == "__main__":
    print("footprint ", write_footprint(LIB, NAME, footprint()))
    print("3D model  ", write_model(LIB, NAME, model()))
