#!/usr/bin/env python3
"""1210 (3225) wire-wound 4-terminal common mode chokes for automotive Ethernet: TDK ACT1210E and
Murata DLW32MH (no kicad-library-tools generator covers 4-pad chokes).

Usage: ~/.cache/dropout/klt-venv/bin/python generators/custom/L_CommonModeChoke_1210.py

All three use the same recommended land pattern: four pads, 2.0 mm inner gap, 4.1 mm outer span,
0.4 mm between the pads of one end, 1.6 mm over both (TDK ACT1210E data sheet 20240325 p. 3,
"Recommended land pattern"; Murata JEFL243C_9124E-01 and JEFL243C-9132D-01 §11.1 "Land dimensions",
a/b/c/d = 2.0/4.1/0.4/1.6). The pad numbering differs: TDK numbers the left end 1 (top) and 2,
the right end 3 (bottom) and 4 (windings 1-4, 2-3); Murata numbers the top row 1, 2 and the bottom
row 4, 3 (windings 1-2, 4-3). Both are drawn from their top views with pin 1 top left.
"""
from fplib import (BODY, CRT_CLR, CRT_W, FAB_W, METAL, SILK_W, chamfered_rect, fab_ref, footprint_text,
                   line, model_ref, rect, smd_pad, text, up, write_footprint, write_model)

LIB = "DropOut_Inductor_SMD"

# Land pattern (mm)
GAP_X, SPAN_X, GAP_Y, SPAN_Y = 2.0, 4.1, 0.4, 1.6
PAD_W = (SPAN_X - GAP_X) / 2          # 1.05
PAD_H = (SPAN_Y - GAP_Y) / 2          # 0.6
PAD_X = (GAP_X + PAD_W) / 2           # 1.525
PAD_Y = (GAP_Y + PAD_H) / 2           # 0.5

TL, BL, BR, TR = (-PAD_X, -PAD_Y), (-PAD_X, PAD_Y), (PAD_X, PAD_Y), (PAD_X, -PAD_Y)

PARTS = {
    # name: (pad positions by number, body L, body W, overall L with terminals, height, descr)
    "L_CommonModeChoke_TDK_ACT1210E_3.2x2.5mm": (
        {1: TL, 2: BL, 3: BR, 4: TR}, 3.2, 2.5, 3.9, 2.5,
        "TDK ACT1210E common mode filter, 3.2x2.5mm (data sheet 20240325 p. 3, recommended land pattern), "
        "https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/6152/ACT1210E.pdf"),
    "L_CommonModeChoke_Murata_DLW32MHxxxXK2_3.2x2.5mm": (
        {1: TL, 2: TR, 3: BR, 4: BL}, 3.2, 2.5, 3.2, 2.5,
        "Murata DLW32MH_XK2 common mode choke coil, 3.2x2.5mm (reference specification JEFL243C_9124E-01 "
        "§5 and §11.1), https://pim.murata.com/en-us/pim/details/?partNum=DLW32MH201XK2%23"),
    "L_CommonModeChoke_Murata_DLW32MHxxxMX2_3.2x2.5mm": (
        {1: TL, 2: TR, 3: BR, 4: BL}, 3.2, 2.5, 3.5, 2.5,
        "Murata DLW32MH_MX2 metal-terminal common mode choke coil, 3.2x2.5mm body, 3.5mm over terminals "
        "(reference specification JEFL243C-9132D-01 §5 and §11.1), "
        "https://pim.murata.com/en-us/pim/details/?partNum=DLW32MH241MX2%23"),
}


def footprint(name, pads, body_l, body_w, overall_l):
    crt_x = up(max(SPAN_X / 2, overall_l / 2) + CRT_CLR, 0.05)
    crt_y = up(max(SPAN_Y / 2, body_w / 2) + CRT_CLR, 0.05)
    sy = body_w / 2 + SILK_W / 2 + 0.05          # silk just outside the body, far from the pads
    sx = body_l / 2
    sx1 = max(SPAN_X, overall_l) / 2 + SILK_W / 2   # pin 1 mark: top line runs past the left end
    body = [
        text("Reference", "REF**", -crt_y - 0.8, "F.SilkS"),
        text("Value", name, crt_y + 0.8, "F.Fab"),
        line(-sx1, -sy, sx, -sy, "F.SilkS", SILK_W), line(-sx, sy, sx, sy, "F.SilkS", SILK_W),
        rect(-crt_x, -crt_y, crt_x, crt_y, "F.CrtYd", CRT_W),
        chamfered_rect(-body_l / 2, -body_w / 2, body_l / 2, body_w / 2, 0.5, "F.Fab", FAB_W),
        fab_ref(0.8),
        *(smd_pad(n, x, y, PAD_W, PAD_H) for n, (x, y) in sorted(pads.items())),
        model_ref(LIB, name),
    ]
    return body


def model(body_l, body_w, overall_l, height):
    import cadquery as cq
    box = lambda x0, x1, y0, y1, z0, z1: cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0) \
        .translate(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    core = box(-body_l / 2, body_l / 2, -body_w / 2, body_w / 2, 0.3, height).edges("|Z").fillet(0.1)
    term_l = max(0.6, (overall_l - body_l) / 2 + 0.6)
    terms = None
    for sx in (-1, 1):
        for sy in (-1, 1):
            x0, x1 = sorted((sx * overall_l / 2, sx * (overall_l / 2 - term_l)))
            t = box(x0, x1, sy * PAD_Y - 0.2, sy * PAD_Y + 0.2, 0.0, 0.5)
            terms = t if terms is None else terms.union(t)
    return [(core, BODY), (terms, METAL)]


if __name__ == "__main__":
    for name, (pads, bl, bw, ol, h, descr) in PARTS.items():
        fp = footprint_text(name, descr, "common mode choke filter automotive Ethernet 1210 3225",
                            footprint(name, pads, bl, bw, ol))
        print("footprint ", write_footprint(LIB, name, fp))
        print("3D model  ", write_model(LIB, name, model(bl, bw, ol, h)))
