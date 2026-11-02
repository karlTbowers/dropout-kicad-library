#!/usr/bin/env python3
"""Board fiducial footprints: a bare copper dot in a larger solder-mask opening, for the assembly
machines' vision system. A PCB feature with nothing to buy or place (docs/CONTRIBUTING.md "Parts with
nothing to buy").

Usage: ~/.cache/dropout/klt-venv/bin/python generators/custom/Fiducial.py

Geometry as KiCad's stock Fiducial_1mm_Mask2mm (kicad-library-tools generators/fiducial,
data/fiducial/fiducial_sizes.yaml: marking 1 mm, mask opening 2 mm, "Level A"): solder mask margin
0.5, copper clearance 0.1 beyond the mask opening, courtyard 0.25 outside the mask opening. Ours is
written here instead of by that generator because the stock footprint is typed `smd` and kept in the
position files; DropOut's no-buy parts leave both BOM and position files (`exclude_from_bom
exclude_from_pos_files`), and KLC F6.1 then wants no `smd` type, as on TestPoint_Pad_D1.0mm.
The pad is unnumbered (as stock), so the symbol has no pins. Origin at the dot's centre.
"""
from fplib import CRT_W, FAB_W, footprint_text, r, text, up, write_footprint

LIB = "DropOut_Fiducial"
CLR_OUTSET = 0.1                   # copper clearance beyond the mask opening (stock pad_clearance_outset)

PARTS = {                          # name: (marking diameter, mask opening diameter, comment)
    "Fiducial_1mm_Mask2mm": (1.0, 2.0, " (Level A)"),
}


def circle(rad, layer, w):
    return (f'\t(fp_circle (center 0 0) (end {r(rad)} 0) (stroke (width {w}) (type solid)) (fill no)'
            f' (layer "{layer}"))')


def fiducial(name, d, mask):
    margin = (mask - d) / 2
    crt = up(mask / 2 + 0.25, 0.01)
    pad = (f'\t(pad "" smd circle (at 0 0) (size {r(d)} {r(d)})\n'
           f'\t\t(layers "F.Cu" "F.Mask") (solder_mask_margin {r(margin)}) (clearance {r(margin + CLR_OUTSET)}))')
    return [text("Reference", "REF**", -crt - 0.7, "F.SilkS"), text("Value", name, crt + 0.7, "F.Fab"),
            circle(crt, "F.CrtYd", CRT_W), circle(mask / 2, "F.Fab", FAB_W),
            '\t(fp_text user "${REFERENCE}" (at 0 0 0) (layer "F.Fab")\n'
            '\t\t(effects (font (size 0.5 0.5) (thickness 0.08))))', pad]


if __name__ == "__main__":
    for name, (d, mask, comment) in PARTS.items():
        descr = (f"Fiducial, circular marking, {d:g}mm bare copper, {mask:g}mm soldermask opening{comment}; "
                 "PCB copper only, nothing to buy or place, "
                 "https://github.com/karlTbowers/dropout-kicad-library/blob/main/generators/custom/Fiducial.py")
        print("footprint ", write_footprint(LIB, name, footprint_text(
            name, descr, "fiducial", fiducial(name, d, mask), attr="exclude_from_pos_files exclude_from_bom")))
