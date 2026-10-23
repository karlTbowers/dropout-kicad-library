#!/usr/bin/env python3
"""Test point footprints: a bare 1 mm copper pad, and SMD/THT wire loops for a scope ground spring
or clip. No kicad-library-tools generator covers test points (KiCad's stock TestPoint footprints
are hand-made); the bare pad and the Keystone patterns match the stock ones.

Usage: ~/.cache/dropout/klt-venv/bin/python generators/custom/TestPoint.py

Sources (archived in dropout-vendor-docs):
- Harwin S1751-XX / S1751-XXR customer information sheets (issues 9/10, 2023): body 3.25 x 1.63,
  loop 2.00 high, recommended pad 3.45 x 1.85.
- Harwin S2751-46R (issue 1, 2015): body 2.00 x 1.20, 1.40 high, recommended PCB layout 2.20 x 1.40.
- Harwin S2761-46R (issue 1, 2015): body 1.60 x 0.80, 1.15 high, recommended PCB layout 1.80 x 1.00.
- Keystone catalog M75 p. 61: 5015 micro miniature, body 2.7 x 1.0, 1.5 high, pad 3.4 x 1.8;
  5016 compact, loop 3.8 wide, foot 2.8, 2.3 high, pad 4.7 x 3.4.
- Keystone catalog M75 p. 62: 5000-5004 miniature, base dia 2.5, 4.6 above the board, loop I.D.
  1.25, mounting hole 1.0.
- Vero terminal assemblies 20-XXXX data sheets (2015; bead diameters from the 2011 issue):
  20-2137 for a 1.02 mm hole, bead dia 2.35; 20-2136 for a 1.32 mm hole, bead dia 3.0. Loop
  2.9-3.3 above the board, leg 2.4-2.9 below.
SMD loops: the loop axis is along Y, so the opening faces the board's Y direction.
"""
from fplib import (CRT_CLR, CRT_W, FAB_W, METAL, SILK_PAD, SILK_W, fab_ref, footprint_text, model_ref, r,
                   rect, smd_pad, text, up, write_footprint, write_model)

LIB = "DropOut_TestPoint"
BEAD = (0.12, 0.12, 0.12)
NYLON = (0.1, 0.1, 0.1)
KEYSTONE_P61 = "https://www.keyelco.com/userAssets/file/K75p61.pdf"
KEYSTONE_P62 = "https://www.keyelco.com/userAssets/file/K75p62.pdf"
HARWIN = "https://content.harwin.com/m/"
VERO = "http://www.farnell.com/datasheets/2042719.pdf"


def circle(cx, cy, rad, layer, w):
    return (f'\t(fp_circle (center {r(cx)} {r(cy)}) (end {r(cx + rad)} {r(cy)})\n'
            f'\t\t(stroke (width {w}) (type solid)) (fill no) (layer "{layer}"))')


def tht_pad(size, drill):
    return (f'\t(pad "1" thru_hole circle (at 0 0) (size {r(size)} {r(size)}) (drill {r(drill)})\n'
            f'\t\t(layers "*.Cu" "*.Mask"))')


def labels(name, y_top, y_bot, fab_size=0.5):
    return [text("Reference", "REF**", y_top - 0.8, "F.SilkS"), text("Value", name, y_bot + 0.8, "F.Fab"),
            fab_ref(fab_size)]


def bare_pad(name, d):
    """Exposed copper pad: mask opening, no paste, nothing placed or bought."""
    crt = up(d / 2 + 0.5, 0.05)          # as KiCad's stock TestPoint_Pad_D1.0mm (courtyard dia 2.0)
    pad = (f'\t(pad "1" smd circle (at 0 0) (size {r(d)} {r(d)})\n'
           f'\t\t(layers "F.Cu" "F.Mask"))')
    return [*labels(name, -crt, crt)[:2],
            circle(0, 0, d / 2 + SILK_PAD + SILK_W / 2, "F.SilkS", SILK_W),
            circle(0, 0, crt, "F.CrtYd", CRT_W), circle(0, 0, d / 2, "F.Fab", FAB_W), fab_ref(0.5), pad]


def smd_loop(name, pad_wh, body_xy):
    pw, ph = pad_wh
    bx, by = body_xy
    cx = up(max(pw, bx) / 2 + CRT_CLR, 0.05)
    cy = up(max(ph, by) / 2 + CRT_CLR, 0.05)
    sx, sy = pw / 2 + SILK_PAD + SILK_W / 2, ph / 2 + SILK_PAD + SILK_W / 2
    return [*labels(name, -max(cy, sy), max(cy, sy))[:2],
            rect(-sx, -sy, sx, sy, "F.SilkS", SILK_W), rect(-cx, -cy, cx, cy, "F.CrtYd", CRT_W),
            rect(-bx / 2, -by / 2, bx / 2, by / 2, "F.Fab", FAB_W), labels(name, 0, 0)[2],
            smd_pad(1, 0, 0, pw, ph, rratio=0.1), model_ref(LIB, name)]


def tht_loop(name, pad_d, drill, base_d):
    crt = up(max(pad_d, base_d) / 2 + CRT_CLR, 0.05)
    return [*labels(name, -crt, crt)[:2],
            circle(0, 0, max(pad_d, base_d) / 2 + SILK_PAD + SILK_W / 2, "F.SilkS", SILK_W),
            circle(0, 0, crt, "F.CrtYd", CRT_W), circle(0, 0, base_d / 2, "F.Fab", FAB_W), labels(name, 0, 0)[2],
            tht_pad(pad_d, drill), model_ref(LIB, name)]


# --- 3D models -------------------------------------------------------------------------------

def smd_loop_model(bx, by, h, t):
    """A strip of thickness t bent into a closed rectangular loop, axis along Y."""
    import cadquery as cq
    outer = cq.Workplane("XZ").center(0, h / 2).rect(bx, h).extrude(by / 2, both=True)
    inner = cq.Workplane("XZ").center(0, h / 2).rect(bx - 2 * t, h - 2 * t).extrude(by, both=True)
    return [(outer.cut(inner).edges("|Y").fillet(min(t, 0.2) * 0.9), METAL)]


def tht_loop_model(base_d, base_h, loop_od, wire, leg_d, leg_len, top, base_color):
    """Insulating base or bead on the board, a wire loop above it (axis along Y), a leg below."""
    import cadquery as cq
    base = cq.Workplane("XY").circle(base_d / 2).extrude(base_h)
    zc = top - loop_od / 2
    loop = (cq.Workplane("XZ").center(0, zc).circle(loop_od / 2).circle(loop_od / 2 - wire)
            .extrude(wire / 2, both=True))
    stem = cq.Workplane("XY").circle(wire / 2).extrude(zc - loop_od / 2 + wire)
    leg = cq.Workplane("XY").workplane(offset=-leg_len).circle(leg_d / 2).extrude(leg_len)
    return [(base, base_color), (loop.union(stem).union(leg), METAL)]


PARTS = {
    # name: (footprint body, model or None, description, tags, attr)
    "TestPoint_Pad_D1.0mm": (
        lambda n: bare_pad(n, 1.0), None,
        "Exposed copper test pad, diameter 1.0mm, solder mask opening only (no paste, no part), "
        "https://github.com/karlTbowers/dropout-kicad-library/blob/main/generators/custom/TestPoint.py",
        "test point pad exposed copper", "exclude_from_pos_files exclude_from_bom"),
    "TestPoint_Harwin_S1751": (
        lambda n: smd_loop(n, (3.45, 1.85), (3.25, 1.63)), lambda: smd_loop_model(3.25, 1.63, 2.0, 0.39),
        "Harwin S1751 SMD test terminal (loop), 3.25x1.63mm, 2.0mm high (customer information sheet "
        f"S1751-XX), {HARWIN}386120eba96d2840/original/DRG-02200-Technical-Drawing-Datasheet-S1751-pdf.pdf",
        "test point loop SMD Harwin S1751", "smd"),
    "TestPoint_Harwin_S2751": (
        lambda n: smd_loop(n, (2.2, 1.4), (2.0, 1.2)), lambda: smd_loop_model(2.0, 1.2, 1.4, 0.2),
        "Harwin S2751 SMT test terminal (loop), 2.0x1.2mm, 1.4mm high (customer information sheet "
        f"S2751-46R), {HARWIN}ae67ab610c42d529/original/DRG-02222-Technical-Drawing-Datasheet-S2751R-pdf.pdf",
        "test point loop SMD Harwin S2751", "smd"),
    "TestPoint_Harwin_S2761": (
        lambda n: smd_loop(n, (1.8, 1.0), (1.6, 0.8)), lambda: smd_loop_model(1.6, 0.8, 1.15, 0.2),
        "Harwin S2761 SMT test terminal (loop), 1.6x0.8mm, 1.15mm high (customer information sheet "
        f"S2761-46R), {HARWIN}d630047163058eb1/original/DRG-02223-Technical-Drawing-Datasheet-S2761R-pdf.pdf",
        "test point loop SMD Harwin S2761", "smd"),
    "TestPoint_Keystone_5015_Micro-Mini": (
        lambda n: smd_loop(n, (3.4, 1.8), (2.7, 1.0)), lambda: smd_loop_model(2.7, 1.0, 1.5, 0.25),
        f"Keystone 5015/5084/5017/5085 SMT micro miniature test point (catalog M75 p. 61), {KEYSTONE_P61}",
        "test point loop SMD Keystone 5015", "smd"),
    "TestPoint_Keystone_5016_Compact": (
        lambda n: smd_loop(n, (4.7, 3.4), (3.8, 2.8)), lambda: smd_loop_model(3.8, 1.0, 2.3, 0.38),
        f"Keystone 5016/5091/5018/5095 SMT compact test point (catalog M75 p. 61), {KEYSTONE_P61}",
        "test point loop SMD Keystone 5016", "smd"),
    "TestPoint_Keystone_5000-5004_Miniature": (
        lambda n: tht_loop(n, 2.0, 1.0, 2.5),
        lambda: tht_loop_model(2.5, 3.0, 1.25 + 0.5, 0.25, 0.5, 2.0, 4.6, NYLON),
        f"Keystone 5000-5004 THM miniature colour-keyed test point, 1.0mm hole (catalog M75 p. 62), {KEYSTONE_P62}",
        "test point loop THT Keystone 5000 5001", "through_hole"),
    "TestPoint_Vero_20-2137_Beaded": (
        lambda n: tht_loop(n, 2.0, 1.02, 2.35),
        lambda: tht_loop_model(2.35, 1.6, 1.2 + 0.8, 0.4, 0.6, 2.6, 3.2, BEAD),
        f"Vero 20-2137 wire loop test terminal with sintered glass bead, 1.02mm hole, bead dia 2.35mm, {VERO}",
        "test point loop THT beaded Vero 20-2137", "through_hole"),
    "TestPoint_Vero_20-2136_Beaded": (
        lambda n: tht_loop(n, 2.6, 1.32, 3.0),
        lambda: tht_loop_model(3.0, 1.6, 2.1 + 0.8, 0.4, 0.8, 2.6, 3.0, BEAD),
        f"Vero 20-2136 wire loop test terminal with sintered glass bead, 1.32mm hole, bead dia 3.0mm, {VERO}",
        "test point loop THT beaded Vero 20-2136", "through_hole"),
}


if __name__ == "__main__":
    for name, (fp, mdl, descr, tags, attr) in PARTS.items():
        print("footprint ", write_footprint(LIB, name, footprint_text(name, descr, tags, fp(name), attr=attr)))
        if mdl:
            print("3D model  ", write_model(LIB, name, mdl()))
