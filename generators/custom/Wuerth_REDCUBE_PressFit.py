#!/usr/bin/env python3
"""Würth Elektronik REDCUBE PRESS-FIT power terminal footprints and 3D models (no generator covers
press-fit pin arrays).

Usage: ~/.cache/dropout/klt-venv/bin/python generators/custom/Wuerth_REDCUBE_PressFit.py [WE_KICAD_LIBRARY]

WE_KICAD_LIBRARY is a checkout of Würth's official KiCad library
(https://github.com/WurthElektronik/KiCad-Library). With it, the script also writes the 3D models
from Würth's STEP files; without it, it writes only the footprints.

Sources (archived in dropout-vendor-docs, Wuerth/REDCUBE/):
- 7461068 WP-RAFU, right angled, M8 (data sheet rev. 001.004, 2025-12-22, p. 1): 5 x 5 press-fit
  pins at 2.54 (10.16 grid), 13.0 square pin plate, body 20.0 above the board, pins 3.5 below,
  PCB 1.6 to 3.2 thick, 250 A.
- 7461114 WP-RAFU, right angled, M6 (data sheet rev. 001.004, 2025-12-22, p. 1): same pin plate and body as
  7461068 (5 x 5 at 2.54, 13.0 square, 20.0 tall), M6 through thread, 250 A, 3.9 N·m.
- 7461106 WP-RATR, right angled, two rows pin-plate, M6 (data sheet rev. 001.005, 2025-12-22, p. 1): 2 x 5
  press-fit pins, columns 10.16 apart, rows at 2.54 (10.16 span), 13.0 square, 20.0 tall, pins 3.5,
  PCB 1.6 to 3.2 thick, 240 A @ 20 °C, 3.9 N·m.
- 786202106 WP-PFIFUA, M6 blind thread, 10 mm (data sheet rev. 001.003, 2024-09-26, p. 1): 4 x 4
  press-fit pins at 2.54 (7.62 grid), 10.0 square body 10.5 above the board, pins 3.0 below, PCB
  1.6 to 2.7 thick, 180 A. "Recommended hole pattern": no components within 4 mm of the REDCUBE, and
  not within 3 mm of the PCB edge; the courtyard is drawn at the 4 mm keep-out.
- Holes (all): drill Ø1.60 -0.03 before plating, 25 to 60 µm copper, finished Ø1.475 ±0.05 for
  chemical surfaces (Ø1.45 ±0.05 for HAL). Each part gets two footprints: the plain name with the
  Ø1.475 finished drill, and `_HAL` with Ø1.45, as Würth's own KiCad library does.
- Pads: Ø1.8, the size in Würth's official KiCad library (REDCUBE_THT_Wurth.pretty, commit 802ff55);
  its pin grids match these data sheets. Silk, fab and courtyard are drawn here (KLC; the 786202106
  courtyard at the 4 mm keep-out, which Würth's footprint does not show).
- Press-fit pins: one electrical terminal, so every pad is numbered "1" and the symbol has one pin
  (as KiCad's stock REDCUBE footprints; user's decision 2026-10-26). Press in one movement, no
  rework or soldering afterwards, 0.1 mm min. gap under the part (Würth notes).
- 3D models: Würth's own STEP files from that library (REDCUBE_THT_Wurth.3dshapes/MP_Wurth_*.step),
  already in the footprint frame. Würth's license terms (License_Terms_WE_KiCad_library.pdf, §1.1)
  allow modifying the models and sharing the modified models if they are marked as modified and
  credit WE eiSos as the original provider: write_we_model() keeps the geometry and colours, renames
  the file to the footprint name and writes that marking into the STEP header.

Origin at the centre of the pin grid.
"""
import sys
from pathlib import Path

from fplib import (CRT_CLR, CRT_W, FAB_W, REPO, SILK_W, footprint_text, model_ref, r, rect, text, up,
                   write_footprint)

LIB = "DropOut_TerminalBlock_Wuerth"
PITCH = 2.54
DRILL = {"": 1.475, "_HAL": 1.45}   # finished hole: chemical Sn / ENIG, or hot-air levelled
PAD = 1.8                        # Würth's KiCad library; 0.74 mm between pads of the same terminal
WE_COMMIT = "802ff55"            # Würth KiCad library commit the models were taken from
WE_MODELS = {                    # footprint name -> Würth model file (REDCUBE_THT_Wurth.3dshapes)
    "Wuerth_REDCUBE-PRESS-FIT_WP-RAFU_7461068_PressFit": "MP_Wurth_WP-RAFU_7461068.step",
    "Wuerth_REDCUBE-PRESS-FIT_WP-RAFU_7461114_PressFit": "MP_Wurth_WP-RAFU_7461114.step",
    "Wuerth_REDCUBE-PRESS-FIT_WP-RATR_7461106_PressFit": "MP_Wurth_WP-RATR_7461106.step",
    "Wuerth_REDCUBE-PRESS-FIT_WP-PFIFUA_786202106_PressFit": "MP_Wurth_WP-PFIFUA_786202106.step",
}

PARTS = {
    "Wuerth_REDCUBE-PRESS-FIT_WP-RAFU_7461068_PressFit": dict(
        n=5, body=13.0, keepout=None,
        descr="Würth REDCUBE PRESS-FIT WP-RAFU, right angled, M8, 25 press-fit pins 2.54 mm, 250 A "
              "(data sheet 7461068 rev. 001.004 p. 1), https://www.we-online.com/components/products/datasheet/7461068.pdf",
        tags="REDCUBE press-fit power terminal M8 right angle WP-RAFU 7461068"),
    "Wuerth_REDCUBE-PRESS-FIT_WP-RAFU_7461114_PressFit": dict(
        n=5, body=13.0, keepout=None,
        descr="Würth REDCUBE PRESS-FIT WP-RAFU, right angled, M6, 25 press-fit pins 2.54 mm, 250 A "
              "(data sheet 7461114 rev. 001.004 p. 1), https://www.we-online.com/components/products/datasheet/7461114.pdf",
        tags="REDCUBE press-fit power terminal M6 right angle WP-RAFU 7461114"),
    "Wuerth_REDCUBE-PRESS-FIT_WP-RATR_7461106_PressFit": dict(
        n=(2, 5), cols=10.16, body=13.0, keepout=None,
        descr="Würth REDCUBE PRESS-FIT WP-RATR, right angled, two rows pin-plate, M6, 10 press-fit pins 2.54 mm, 240 A "
              "(data sheet 7461106 rev. 001.005 p. 1), https://www.we-online.com/components/products/datasheet/7461106.pdf",
        tags="REDCUBE press-fit power terminal M6 right angle WP-RATR 7461106"),
    "Wuerth_REDCUBE-PRESS-FIT_WP-PFIFUA_786202106_PressFit": dict(
        n=4, body=10.0, keepout=4.0,
        descr="Würth REDCUBE PRESS-FIT WP-PFIFUA, M6 blind thread, 16 press-fit pins 2.54 mm, 180 A, "
              "4 mm component keep-out (data sheet 786202106 rev. 001.003 p. 1), "
              "https://www.we-online.com/components/products/datasheet/786202106.pdf",
        tags="REDCUBE press-fit power terminal M6 WP-PFIFUA 786202106 automotive"),
}


def pins(p):
    """Pin centres: an n x n grid at PITCH, or (columns, rows) with the columns `cols` apart."""
    if isinstance(p["n"], tuple):
        nc, nr = p["n"]
        xs = [-p["cols"] / 2 + i * p["cols"] / (nc - 1) for i in range(nc)]
    else:
        nc = nr = p["n"]
        xs = [-(nc - 1) * PITCH / 2 + i * PITCH for i in range(nc)]
    o = (nr - 1) * PITCH / 2
    return [(x, -o + j * PITCH) for j in range(nr) for x in xs]


def tht_pad(x, y, drill):
    return (f'\t(pad "1" thru_hole circle (at {r(x)} {r(y)}) (size {PAD} {PAD}) (drill {drill})\n'
            f'\t\t(layers "*.Cu" "*.Mask"))')


def footprint(name, p, finish=""):
    """Footprint for the part `name`; finish "" (chemical surfaces) or "_HAL"."""
    h = p["body"] / 2
    crt = up(h + (p["keepout"] if p["keepout"] else CRT_CLR), 0.05)
    s = h + FAB_W / 2 + SILK_W / 2 + 0.04
    notes = [("Drill Ø1.60 -0.03 before plating, Cu 25-60 µm; finished Ø1.45 ±0.05: HAL surface finish only" if finish
              else "Drill Ø1.60 -0.03 before plating, Cu 25-60 µm; finished Ø1.475 ±0.05: chemical Sn / ENIG finish"),
             "Press-fit in one movement; no rework or soldering after insertion"]
    if p["keepout"]:
        notes.append("Courtyard = Würth 4 mm component keep-out; keep 3 mm from the PCB edge")
    body = [
        text("Reference", "REF**", -crt - 1.0, "F.SilkS"),
        text("Value", name + finish, crt + 1.0, "F.Fab"),
        rect(-s, -s, s, s, "F.SilkS", SILK_W),
        rect(-h, -h, h, h, "F.Fab", FAB_W),
        rect(-crt, -crt, crt, crt, "F.CrtYd", CRT_W),
        *[f'\t(fp_text user "{t}" (at 0 {r(crt + 2.4 + 1.2 * i)} 0) (layer "Cmts.User")\n'
          f'\t\t(effects (font (size 0.8 0.8) (thickness 0.12))))' for i, t in enumerate(notes)],
        f'\t(fp_text user "${{REFERENCE}}" (at 0 0 0) (layer "F.Fab")\n\t\t(effects (font (size 1 1) (thickness 0.15))))',
        *[tht_pad(x, y, DRILL[finish]) for x, y in pins(p)],
        model_ref(LIB, name + finish),         # KLC F9.3: the model carries the footprint's name
    ]
    descr = p["descr"] + (", HAL surface finish (finished hole 1.45 mm)" if finish else "")
    return footprint_text(name + finish, descr, p["tags"] + (" HAL" if finish else ""), body, attr="through_hole")


def write_we_model(src, name, commit=WE_COMMIT):
    """Copy Würth's model to <name>.step: geometry and colours unchanged (it is already in the footprint
    frame), header marked as modified by DropOut with WE eiSos credited, as Würth's license requires.
    `commit` is the Würth KiCad library commit the model was taken from."""
    from OCP.APIHeaderSection import APIHeaderSection_MakeHeader
    from OCP.IFSelect import IFSelect_RetDone
    from OCP.STEPCAFControl import STEPCAFControl_Reader, STEPCAFControl_Writer
    from OCP.STEPControl import STEPControl_AsIs
    from OCP.TCollection import TCollection_ExtendedString, TCollection_HAsciiString
    from OCP.TDocStd import TDocStd_Document

    doc = TDocStd_Document(TCollection_ExtendedString("XmlOcaf"))
    reader = STEPCAFControl_Reader()
    reader.SetColorMode(True)
    reader.SetNameMode(True)
    if reader.ReadFile(str(src)) != IFSelect_RetDone or not reader.Transfer(doc):
        sys.exit(f"cannot read {src}")
    writer = STEPCAFControl_Writer()
    writer.SetColorMode(True)
    writer.SetNameMode(True)
    writer.Transfer(doc, STEPControl_AsIs)
    header = APIHeaderSection_MakeHeader(writer.ChangeWriter().Model())
    header.SetName(TCollection_HAsciiString(name))
    header.SetAuthorValue(1, TCollection_HAsciiString(
        f"Original model provided by Wuerth Elektronik eiSos GmbH & Co. KG (WE eiSos), KiCad-Library {commit}: {src.name}"))
    header.SetOrganizationValue(1, TCollection_HAsciiString(
        "MODIFIED by DropOut: renamed and re-exported with this header; geometry and colours unchanged"))
    out = REPO / "3dmodels" / f"{LIB}.3dshapes" / f"{name}.step"
    out.parent.mkdir(parents=True, exist_ok=True)
    if writer.Write(str(out)) != IFSelect_RetDone:
        sys.exit(f"cannot write {out}")
    return out


if __name__ == "__main__":
    we = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    for name, p in PARTS.items():
        for finish in DRILL:
            print("footprint ", write_footprint(LIB, name + finish, footprint(name, p, finish)))
            if we:
                src = we / "3dmodels" / "REDCUBE_THT_Wurth.3dshapes" / WE_MODELS[name]
                print("3D model  ", write_we_model(src, name + finish))
