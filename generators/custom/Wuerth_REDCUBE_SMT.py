#!/usr/bin/env python3
"""Würth Elektronik REDCUBE SMT power terminal footprints and 3D models (an annular SMD pad around a
non-plated hole; no generator covers it).

Usage: ~/.cache/dropout/klt-venv/bin/python generators/custom/Wuerth_REDCUBE_SMT.py [WE_KICAD_LIBRARY]

WE_KICAD_LIBRARY is a checkout of Würth's official KiCad library
(https://github.com/WurthElektronik/KiCad-Library). With it, the script also writes the 3D models
from Würth's STEP files; without it, it writes only the footprints.

Sources (archived in dropout-vendor-docs, Wuerth/REDCUBE/):
- 74660016 WP-SMRT, reverse with internal thread, M6 (data sheet rev. 001.001, 2022-02-10, p. 1): Ø12.0
  flange 3.0 high on the board, Ø9.0 spigot below it (5.6 overall), so 2.6 into the board; M6 through
  thread; brass, tin; 85 A; 3.9 N·m. 74660016R is the same part on tape and reel (same drawing).
- "Recommended Land Pattern": solder pad ring Ø9.3 / Ø13.0 around a Ø9.3 non-plated through hole.
- "Stencil Suggestion": ring Ø9.5 / Ø12.8 split into four by 1.0 wide gaps, 150 µm paste.
- Würth's official KiCad library (REDCUBE_SMD_Wurth.pretty/MP_Wurth_WP-SMRT_74660016, commit c905610)
  has the same paste but a solid Ø13.0 copper disc and no hole, although its own 3D model puts the
  spigot 2.6 below the board surface. We follow the data sheet; the hole is required.
- Copper pulled back from the hole: the data sheet's ring starts at the hole edge (Ø9.3), which fails
  KiCad's hole clearance (0.25) and solder-mask bridge checks on every board, and fabs pull copper back
  from NPTH edges anyway. The copper ring is Ø9.8 / Ø13.0 (0.25 clear of the hole); hole and stencil stay
  as in the data sheet (user's decision 2026-10-26).
- 3D model: Würth's STEP from that library (REDCUBE_SMD_Wurth.3dshapes/MP_Wurth_WP-SMRT_74660016.step),
  already in the footprint frame (flange on z = 0, spigot down). Written by write_we_model(): geometry
  and colours unchanged, marked as modified and crediting WE eiSos, as Würth's license requires.

Origin at the centre of the hole.
"""
import math
import sys
from pathlib import Path

from fplib import CRT_W, FAB_W, SILK_PAD, SILK_W, footprint_text, model_ref, r, text, up, write_footprint
from Wuerth_REDCUBE_PressFit import LIB, write_we_model

WE_COMMIT = "c905610"            # Würth KiCad library commit the models were taken from

PARTS = {
    "Wuerth_REDCUBE-SMT_WP-SMRT_74660016": dict(
        hole=9.3, pad=(9.8, 13.0),   # data sheet ring Ø9.3 / Ø13.0, pulled back 0.25 from the hole
        paste=(9.5, 12.8), paste_gap=1.0, flange=12.0, thread=6.0,
        we_model="MP_Wurth_WP-SMRT_74660016.step",
        descr="Würth REDCUBE SMT WP-SMRT, reverse with internal thread, M6, Ø12 flange, Ø9.3 non-plated hole "
              "for the Ø9.0 spigot, 85 A (data sheet 74660016 rev. 001.001 p. 1), "
              "https://www.we-online.com/components/products/datasheet/74660016.pdf",
        tags="REDCUBE SMT power terminal M6 internal thread reverse WP-SMRT 74660016 74660016R"),
}


def circle(rad, layer, w):
    return (f'\t(fp_circle (center 0 0) (end {r(rad)} 0) (stroke (width {w}) (type solid)) (fill no)'
            f' (layer "{layer}"))')


def ring_pad(num, d_in, d_out):
    """Annular SMD pad as KiCad's stock footprints draw one: a round anchor on the ring and a circle
    primitive whose line width is the ring width."""
    rm, w = (d_in + d_out) / 4, (d_out - d_in) / 2
    return (f'\t(pad "{num}" smd custom (at {r(rm)} 0) (size {r(w)} {r(w)})\n'
            f'\t\t(layers "F.Cu" "F.Mask")\n'
            f'\t\t(options (clearance outline) (anchor circle))\n'
            f'\t\t(primitives\n'
            f'\t\t\t(gr_circle (center {r(-rm)} 0) (end 0 0) (width {r(w)}) (fill no))\n'
            f'\t\t))')


def paste_segments(d_in, d_out, gap, step=5.0):
    """Four paste-only pads: the ring d_in..d_out cut by two `gap` wide bars on the axes."""
    ri, ro, g = d_in / 2, d_out / 2, gap / 2
    pads = []
    for q in range(4):
        a0 = q * 90.0
        arc = lambda rad: [a0 + math.degrees(math.asin(g / rad)), a0 + 90 - math.degrees(math.asin(g / rad))]
        oa, ia = arc(ro), arc(ri)
        n = max(2, math.ceil((oa[1] - oa[0]) / step))
        outer = [oa[0] + (oa[1] - oa[0]) * i / n for i in range(n + 1)]
        inner = [ia[1] - (ia[1] - ia[0]) * i / n for i in range(n + 1)]
        pts = ([(ro * math.cos(math.radians(a)), ro * math.sin(math.radians(a))) for a in outer] +
               [(ri * math.cos(math.radians(a)), ri * math.sin(math.radians(a))) for a in inner])
        rm, am = (ri + ro) / 2, math.radians(a0 + 45)
        ax, ay = rm * math.cos(am), rm * math.sin(am)
        prim = " ".join(f"(xy {r(x - ax)} {r(y - ay)})" for x, y in pts)
        pads.append(f'\t(pad "" smd custom (at {r(ax)} {r(ay)}) (size 0.5 0.5)\n'
                    f'\t\t(layers "F.Paste")\n'
                    f'\t\t(options (clearance outline) (anchor circle))\n'
                    f'\t\t(primitives\n\t\t\t(gr_poly (pts {prim}) (width 0) (fill yes))\n\t\t))')
    return pads


def footprint(name, p):
    pad_r = p["pad"][1] / 2
    silk = pad_r + SILK_PAD + SILK_W / 2                 # silk 0.2 clear of the pad
    crt = up(silk + SILK_W / 2, 0.05)                   # courtyard encloses pad (+0.25), body and silk
    notes = ["Ø9.3 non-plated hole for the Ø9.0 spigot (2.6 mm below the flange)",
             "Copper Ø9.8-13.0: data sheet Ø9.3 pulled back 0.25 from the hole",
             "Paste 150 µm, 4 segments per Würth stencil suggestion; 3.9 N·m max."]
    body = [
        text("Reference", "REF**", -crt - 1.0, "F.SilkS"),
        text("Value", name, crt + 1.0, "F.Fab"),
        circle(silk, "F.SilkS", SILK_W),
        circle(p["flange"] / 2, "F.Fab", FAB_W),
        circle(p["thread"] / 2, "F.Fab", FAB_W),
        circle(crt, "F.CrtYd", CRT_W),
        *[f'\t(fp_text user "{t}" (at 0 {r(crt + 2.4 + 1.2 * i)} 0) (layer "Cmts.User")\n'
          f'\t\t(effects (font (size 0.8 0.8) (thickness 0.12))))' for i, t in enumerate(notes)],
        f'\t(fp_text user "${{REFERENCE}}" (at 0 {r(-p["flange"] / 2 + 1.2)} 0) (layer "F.Fab")\n'
        f'\t\t(effects (font (size 1 1) (thickness 0.15))))',
        f'\t(pad "" np_thru_hole circle (at 0 0) (size {p["hole"]} {p["hole"]}) (drill {p["hole"]})\n'
        f'\t\t(layers "*.Cu" "*.Mask"))',
        ring_pad("1", *p["pad"]),
        *paste_segments(*p["paste"], p["paste_gap"]),
        model_ref(LIB, name),
    ]
    return footprint_text(name, p["descr"], p["tags"], body, attr="smd")


if __name__ == "__main__":
    we = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    for name, p in PARTS.items():
        print("footprint ", write_footprint(LIB, name, footprint(name, p)))
        if we:
            src = we / "3dmodels" / "REDCUBE_SMD_Wurth.3dshapes" / p["we_model"]
            print("3D model  ", write_we_model(src, name, WE_COMMIT))
