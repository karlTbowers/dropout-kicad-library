#!/usr/bin/env python3
"""DFN1006 (1.0 x 0.6 mm) two-terminal ESD diode footprints with each manufacturer's own land
pattern (they differ, so one footprint per package code). No kicad-library-tools generator covers
the Vishay T-shaped pads or Nexperia's offset paste apertures.

Usage: ~/.cache/dropout/klt-venv/bin/python generators/custom/D_DFN1006-2.py

Sources:
- Vishay DFN1006-2B: VETH100A1DD1 data sheet (doc 86195, rev. 1.3, 06-Feb-2026) p. 5, package
  dimensions and "Footprint recommendation" (drawing S8-V-3906.04-059 rev. 6): T-shaped pads,
  1.4 mm outer span, 0.4 mm gap, 0.3 x 0.55 mm inner part, 0.3 mm wide outer tab. Pin 1 is
  marked by the bar.
- Nexperia DFN1006-2 (SOD882-2): PESD1ETH10L-Q data sheet (9 Sep 2025) Fig. 10: lands 0.4 x 0.7
  at 0.7 pitch, R0.05 corners, solder resist 0.5 x 0.8, paste 0.3 x 0.6. Body 1.0 x 0.6 x 0.47.
- Nexperia DFN1006BD-2 (SOD882BD, side-wettable flanks): PESD1ETH10LS-Q data sheet (28 Jan 2025)
  Fig. 10: lands 0.5 x 0.7 with 0.3 gap, solder resist 0.6 x 0.8, paste 0.3 x 0.6 with 0.4 gap
  (offset 0.05 mm inward of the land centre). Body 1.0 x 0.6 x 0.47.
Nexperia pin 1 is K1, on the cathode-band side.
"""
from fplib import (BODY, CRT_CLR, CRT_W, FAB_W, METAL, SILK_PAD, SILK_W, chamfered_rect, custom_pad, fab_ref,
                   footprint_text, line, model_ref, r, rect, text, up, write_footprint, write_model)

LIB = "DropOut_Diode_SMD"
BODY_L, BODY_W, BODY_H = 1.0, 0.6, 0.47


def pad(num, x, y, w, h, layers, rratio=None, mask=None):
    shape = f"roundrect (at {r(x)} {r(y)}) (size {r(w)} {r(h)})" if rratio else f"rect (at {r(x)} {r(y)}) (size {r(w)} {r(h)})"
    extra = (f" (roundrect_rratio {rratio})" if rratio else "") + \
        (f" (solder_mask_margin {mask})" if mask is not None else "")
    lay = " ".join(f'"{l}"' for l in layers)
    return f'\t(pad "{num}" smd {shape}\n\t\t(layers {lay}){extra})'


def vishay_pads():
    # Per pad: inner part 0.3 (x) x 0.55 (y) next to the 0.4 gap, outer tab 0.2 (x) x 0.3 (y).
    out = []
    for num, s in ((1, -1), (2, 1)):
        ax = s * 0.35                                  # anchor: centre of the inner part
        tab = [(s * 0.5 - ax, -0.15), (s * 0.7 - ax, -0.15), (s * 0.7 - ax, 0.15), (s * 0.5 - ax, 0.15)]
        out.append(custom_pad(num, (ax, 0), (0.3, 0.55), [tab]))
    return out, 0.7, 0.275


def sod882_pads():
    out = [pad(n, s * 0.35, 0, 0.4, 0.7, ("F.Cu", "F.Mask", "F.Paste"), rratio=0.125, mask=0.05)
           for n, s in ((1, -1), (2, 1))]
    # paste 0.3 x 0.6 centred on the land: paste margin -0.05
    out = [p.replace("(solder_mask_margin 0.05)", "(solder_mask_margin 0.05) (solder_paste_margin -0.05)") for p in out]
    return out, 0.55, 0.35


def sod882bd_pads():
    out = []
    for n, s in ((1, -1), (2, 1)):
        out.append(pad(n, s * 0.4, 0, 0.5, 0.7, ("F.Cu", "F.Mask"), mask=0.05))
        out.append(pad("", s * 0.35, 0, 0.3, 0.6, ("F.Paste",)))
    return out, 0.65, 0.35


PARTS = {
    "Vishay_DFN1006-2B_1.0x0.6mm": (vishay_pads,
        "Vishay DFN1006-2B, 1.0x0.6x0.45mm (VETH100A1DD1 data sheet doc 86195 rev. 1.3 p. 5, footprint "
        "recommendation), https://www.vishay.com/docs/86195/veth100a1dd1.pdf", "DFN1006-2B diode ESD Vishay"),
    "Nexperia_DFN1006-2_SOD882-2_1.0x0.6mm": (sod882_pads,
        "Nexperia DFN1006-2 (SOD882-2), 1.0x0.6x0.47mm, pitch 0.65mm (PESD1ETH10L-Q data sheet Fig. 10, "
        "reflow soldering footprint), https://assets.nexperia.com/documents/data-sheet/PESD1ETH10L-Q.pdf",
        "DFN1006-2 SOD882 SOD-882 diode ESD Nexperia"),
    "Nexperia_DFN1006BD-2_SOD882BD_1.0x0.6mm": (sod882bd_pads,
        "Nexperia DFN1006BD-2 (SOD882BD) with side-wettable flanks, 1.0x0.6x0.47mm, pitch 0.65mm "
        "(PESD1ETH10LS-Q data sheet Fig. 10, reflow soldering footprint), "
        "https://assets.nexperia.com/documents/data-sheet/PESD1ETH10LS-Q.pdf",
        "DFN1006BD-2 SOD882BD diode ESD Nexperia side-wettable"),
}


def footprint(name, pads, x_ext, y_ext):
    crt_x = up(max(x_ext, BODY_L / 2) + CRT_CLR, 0.05)
    crt_y = up(max(y_ext + 0.05, BODY_W / 2) + CRT_CLR, 0.05)     # + solder mask margin
    sy = max(y_ext + 0.05 + SILK_PAD, BODY_W / 2) + SILK_W / 2
    sx0 = -(x_ext + 0.05 + SILK_PAD + SILK_W / 2)                   # pin 1 side: L-shaped silk
    return [
        text("Reference", "REF**", -crt_y - 0.8, "F.SilkS"),
        text("Value", name, crt_y + 0.8, "F.Fab"),
        line(sx0, -sy, BODY_L / 2, -sy, "F.SilkS", SILK_W), line(sx0, sy, BODY_L / 2, sy, "F.SilkS", SILK_W),
        line(sx0, -sy, sx0, sy, "F.SilkS", SILK_W),
        rect(-crt_x, -crt_y, crt_x, crt_y, "F.CrtYd", CRT_W),
        chamfered_rect(-BODY_L / 2, -BODY_W / 2, BODY_L / 2, BODY_W / 2, 0.15, "F.Fab", FAB_W),
        fab_ref(0.5),
        *pads,
        model_ref(LIB, name),
    ]


def model():
    import cadquery as cq
    box = lambda x0, x1, w, z0, z1: cq.Workplane("XY").box(x1 - x0, w, z1 - z0) \
        .translate(((x0 + x1) / 2, 0, (z0 + z1) / 2))
    body = box(-BODY_L / 2, BODY_L / 2, BODY_W, 0.02, BODY_H)
    terms = box(-BODY_L / 2, -BODY_L / 2 + 0.25, 0.5, 0.0, 0.1).union(box(BODY_L / 2 - 0.25, BODY_L / 2, 0.5, 0.0, 0.1))
    return [(body, BODY), (terms, METAL)]


if __name__ == "__main__":
    for name, (make, descr, tags) in PARTS.items():
        pads, x_ext, y_ext = make()
        print("footprint ", write_footprint(LIB, name, footprint_text(name, descr, tags, footprint(name, pads, x_ext, y_ext))))
        print("3D model  ", write_model(LIB, name, model()))
