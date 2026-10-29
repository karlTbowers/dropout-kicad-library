#!/usr/bin/env python3
"""Six-lead flat-lead SOT packages with each manufacturer's own land pattern: Diodes SOT563 and
Nexperia SOT666 (the same 1.6 x 1.2 mm body class, but different recommended lands, so one footprint
per manufacturer, vendor-prefixed per KLC F2).

Usage: ~/.cache/dropout/klt-venv/bin/python generators/custom/SOT-563_SOT-666.py

Sources:
- Diodes SOT563: DMC2710UVQ data sheet DS43454 Rev. 3-2 (June 2022) p. 10 and DMC2400UVQ DS44119
  Rev. 2-2 p. 10 (identical): Package Outline Dimensions (A 0.55..0.60, b 0.15..0.30, c 0.10..0.18,
  D 1.50..1.70, E 1.55..1.70, E1 1.10..1.25, e 0.50, L 0.10..0.30) and Suggested Pad Layout
  (C 0.500 pitch, C1 1.270 between the land rows, X 0.300 x Y 0.670 lands, X1 1.300, Y1 1.940).
- Nexperia SOT666: package information SOT666 (1 June 2022) Fig. 1 outline (A 0.5..0.6, bp 0.17..0.27,
  c 0.08..0.18, D 1.5..1.7, E 1.1..1.3, HE 1.5..1.7, e 0.5, Lp 0.1..0.3) and Fig. 2 reflow soldering
  footprint (sot666_fr): corner lands 0.5 x 0.375 (paste 0.45 x 0.325) at 1.7 between the rows and
  1.075 apart, centre lands 0.65 x 0.3 (paste 0.6 x 0.25) reaching 2.45 overall with their inner
  edges in line with the corner lands. KiCad's stock Package_TO_SOT_SMD:SOT-666 has the same lands;
  ours adds Nexperia's smaller paste apertures.
Both drawings show pins 1-3 along one long side with pin 1 at the index; the footprints have pin 1 top
left and pins 1-3 down the left column, 4-6 up the right (KiCad's stock orientation).
3D model dimensions the drawings do not give are marked ESTIMATE.
"""
from fplib import (CRT_CLR, CRT_W, FAB_W, METAL, SILK_PAD, SILK_W, chamfered_rect, fab_ref, footprint_text,
                   line, model_ref, smd_pad, text, up, write_footprint, write_model)

LIB = "DropOut_Package_TO_SOT_SMD"
PIN_Y = {1: -1, 2: 0, 3: 1, 4: 1, 5: 0, 6: -1}    # pitch multiples; 1-3 left (x < 0), 4-6 right


def diodes_pads():
    # Suggested Pad Layout: X 0.30 (along the row) x Y 0.67, rows C1 = 1.27 apart, pitch C = 0.5
    return [smd_pad(n, (-1 if n <= 3 else 1) * 1.27 / 2, PIN_Y[n] * 0.5, 0.67, 0.30) for n in PIN_Y], 1.27 / 2 + 0.335, 0.5 + 0.15


def nexperia_pads():
    out = []
    for n in PIN_Y:
        sx = -1 if n <= 3 else 1
        if PIN_Y[n]:     # corner land 0.5 x 0.375 at x 0.85, y 1.075/2; paste 0.45 x 0.325
            out.append(smd_pad(n, sx * 0.85, PIN_Y[n] * 1.075 / 2, 0.5, 0.375, extra=" (solder_paste_margin -0.025)"))
        else:            # centre land 0.65 x 0.3, inner edge at 0.6 (in line with the corners); paste 0.6 x 0.25
            out.append(smd_pad(n, sx * 0.925, 0, 0.65, 0.3, extra=" (solder_paste_margin -0.025)"))
    return out, 1.25, 1.075 / 2 + 0.375 / 2


# name: (pads, body x (E1/E), body y (D), height, lead span (E/HE), lead width, lead length, lead thickness,
#        descr, tags)
PARTS = {
    "Diodes_SOT-563": (diodes_pads, 1.2, 1.6, 0.575, 1.6, 0.2, 0.2, 0.11,
        "Diodes Incorporated SOT563, 6 pin, 1.6x1.2mm body, 0.5mm pitch, flat leads (DMC2710UVQ data sheet DS43454 "
        "Rev. 3-2 p. 10, Suggested Pad Layout), https://www.diodes.com/assets/Datasheets/DMC2710UVQ.pdf",
        "SOT-563 SOT563 Diodes flat lead"),
    "Nexperia_SOT-666": (nexperia_pads, 1.2, 1.6, 0.55, 1.6, 0.22, 0.2, 0.13,
        "Nexperia SOT666, 6 pin, 1.6x1.2x0.55mm body, 0.5mm pitch, flat leads (SOT666 package information 1 June "
        "2022 Fig. 2, reflow soldering footprint), https://assets.nexperia.com/documents/package-information/SOT666.pdf",
        "SOT-666 SOT666 Nexperia flat lead"),
}


def footprint(name, pads, x_ext, y_ext, bx, by):
    hx, hy = bx / 2, by / 2
    crt_x = up(max(x_ext, hx) + CRT_CLR, 0.05)
    crt_y = up(max(y_ext, hy) + CRT_CLR, 0.05)
    sy = max(y_ext + SILK_PAD, hy) + SILK_W / 2           # silk lines above and below the lands
    return [
        text("Reference", "REF**", -crt_y - 0.8, "F.SilkS"),
        text("Value", name, crt_y + 0.8, "F.Fab"),
        line(-x_ext, -sy, hx, -sy, "F.SilkS", SILK_W),       # top line runs out over pin 1: pin 1 mark
        line(-hx, sy, hx, sy, "F.SilkS", SILK_W),
        line(-crt_x, -crt_y, crt_x, -crt_y, "F.CrtYd", CRT_W), line(crt_x, -crt_y, crt_x, crt_y, "F.CrtYd", CRT_W),
        line(crt_x, crt_y, -crt_x, crt_y, "F.CrtYd", CRT_W), line(-crt_x, crt_y, -crt_x, -crt_y, "F.CrtYd", CRT_W),
        chamfered_rect(-hx, -hy, hx, hy, 0.3, "F.Fab", FAB_W),
        fab_ref(0.5),
        *pads,
        model_ref(LIB, name),
    ]


def model(bx, by, h, span, lw, ll, lt):
    import cadquery as cq
    gap = 0.02                                   # ESTIMATE: mould clearance above the leads' underside
    body = (cq.Workplane("XY").box(bx, by, h - gap).translate((0, 0, gap + (h - gap) / 2))
            .edges("|Z").fillet(0.05)            # ESTIMATE: corner radius of the moulded body
            .faces(">Z").edges().chamfer(0.04))  # ESTIMATE: top edge break
    dot = (cq.Workplane("XY").workplane(offset=h - 0.02).center(-bx / 2 + 0.25, -by / 2 + 0.25)
           .circle(0.1).extrude(0.03))           # ESTIMATE: pin 1 index dot (shown on both drawings)
    body = body.cut(dot)
    metal = None
    for n, k in PIN_Y.items():
        sx = -1 if n <= 3 else 1
        x0, x1 = sx * (bx / 2 - 0.15), sx * span / 2   # ESTIMATE: lead runs 0.15 under the body
        lead = cq.Workplane("XY").box(abs(x1 - x0), lw, lt).translate(((x0 + x1) / 2, k * 0.5, lt / 2))
        metal = lead if metal is None else metal.union(lead)
    # KiCad's model Y is the footprint's -y: mirror so the index dot stays at pin 1
    return [(body.mirror("XZ"), (0.15, 0.15, 0.15)), (metal.mirror("XZ"), METAL)]


if __name__ == "__main__":
    for name, (make, bx, by, h, span, lw, ll, lt, descr, tags) in PARTS.items():
        pads, x_ext, y_ext = make()
        print("footprint ", write_footprint(LIB, name, footprint_text(name, descr, tags, footprint(name, pads, x_ext, y_ext, bx, by))))
        print("3D model  ", write_model(LIB, name, model(bx, by, h, span, lw, ll, lt)))
