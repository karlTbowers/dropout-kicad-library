#!/usr/bin/env python3
"""DO-218AC footprint and 3D model (no kicad-library-tools generator covers DO-218).

Usage (tools Python, for CadQuery):
  ~/.cache/dropout/klt-venv/bin/python generators/custom/D_DO-218AC.py

Writes footprints/DropOut_Diode_SMD.pretty/D_DO-218AC.kicad_mod and
3dmodels/DropOut_Diode_SMD.3dshapes/D_DO-218AC.step.

Source: Vishay XLD8A24CA datasheet (doc 87200, rev. 23-Jan-2026) page 4, "Package outline
dimensions" and "Mounting Pad Layout" (IPC-7351). Lead 1 is the small bent lead; lead 2 is
the metal heatsink under the body. The origin is the centre of the 15.30 mm pad span, within
0.1 mm of the package centre (outline 15.0..16.0 mm).
"""
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
LIB = "DropOut_Diode_SMD"
NAME = "D_DO-218AC"
DATASHEET = "https://www.vishay.com/doc?87200"

# Mounting pad layout (mm)
SPAN = 15.30                     # big pad left edge to small pad right edge
BIG = (9.80, 10.70)              # lead 2 / heatsink pad
SMALL = (2.15, 2.60)             # lead 1 pad
GAP = 3.35
assert abs(BIG[0] + GAP + SMALL[0] - SPAN) < 1e-9
X0 = -SPAN / 2
PAD2_X = X0 + BIG[0] / 2         # -2.75
PAD1_X = SPAN / 2 - SMALL[0] / 2  # 6.575

# Package outline (nominal of min..max), aligned to the pad span centre
BODY_LEN = 13.5                  # 13.3..13.7
BODY_W = 8.5                     # moulded body 8.3..8.7
OVERALL_W = 10.0                 # with heatsink flanges 9.5..10.5
OVERALL_LEN = 15.5               # body + lead 1, 15.0..16.0
HEIGHT = 4.85                    # 4.7..5.0
SINK_LEN = 10.0                  # heatsink 9.7..10.3
LEAD_W = 2.7                     # lead 1 width 2.4..3.0
LEAD_T = 0.6                     # lead thickness 0.5..0.7
LEAD_H = 3.0                     # lead 1 bend height 2.5..3.5
BODY_X0 = -OVERALL_LEN / 2
BODY_X1 = BODY_X0 + BODY_LEN
LEAD_X1 = OVERALL_LEN / 2

SILK_W, FAB_W, CRT_W = 0.12, 0.10, 0.05
SILK_PAD = 0.2                   # silk to copper clearance
CRT_CLR = 0.25


def r(v, grid=0.01):
    return round(round(v / grid) * grid, 4)


def line(x1, y1, x2, y2, layer, w):
    return (f'\t(fp_line (start {r(x1)} {r(y1)}) (end {r(x2)} {r(y2)})\n'
            f'\t\t(stroke (width {w}) (type solid)) (layer "{layer}"))')


def rect(x1, y1, x2, y2, layer, w):
    return "\n".join([line(x1, y1, x2, y1, layer, w), line(x2, y1, x2, y2, layer, w),
                      line(x2, y2, x1, y2, layer, w), line(x1, y2, x1, y1, layer, w)])


def pad(num, x, size):
    return (f'\t(pad "{num}" smd roundrect (at {r(x)} 0) (size {size[0]} {size[1]})\n'
            f'\t\t(layers "F.Cu" "F.Mask" "F.Paste") (roundrect_rratio 0.025))')


def footprint():
    big_top = BIG[1] / 2
    crt_x = max(LEAD_X1, SPAN / 2) + CRT_CLR
    crt_y = max(big_top, OVERALL_W / 2) + CRT_CLR
    crt_x, crt_y = r(crt_x, 0.05) + (0.05 if r(crt_x, 0.05) < crt_x else 0), r(crt_y, 0.05) + (0.05 if r(crt_y, 0.05) < crt_y else 0)
    sy = OVERALL_W / 2 + SILK_W / 2 + 0.05                 # silk just outside the body
    sx0 = PAD2_X + BIG[0] / 2 + SILK_PAD + SILK_W / 2       # clear of the heatsink pad
    sx1 = BODY_X1 + SILK_W / 2 + 0.05
    sy_lead = SMALL[1] / 2 + SILK_PAD + SILK_W / 2           # clear of the lead pad
    fab = "\n".join([
        rect(BODY_X0, -OVERALL_W / 2, BODY_X1, OVERALL_W / 2, "F.Fab", FAB_W),
        line(BODY_X1, -LEAD_W / 2, LEAD_X1, -LEAD_W / 2, "F.Fab", FAB_W),
        line(LEAD_X1, -LEAD_W / 2, LEAD_X1, LEAD_W / 2, "F.Fab", FAB_W),
        line(LEAD_X1, LEAD_W / 2, BODY_X1, LEAD_W / 2, "F.Fab", FAB_W),
    ])
    silk = "\n".join([
        line(sx0, -sy, sx1, -sy, "F.SilkS", SILK_W), line(sx1, -sy, sx1, -sy_lead, "F.SilkS", SILK_W),
        line(sx0, sy, sx1, sy, "F.SilkS", SILK_W), line(sx1, sy, sx1, sy_lead, "F.SilkS", SILK_W),
    ])
    text = lambda kind, val, y, layer, hide="": (
        f'\t(property "{kind}" "{val}" (at 0 {r(y)} 0) (layer "{layer}"){hide}\n'
        f'\t\t(effects (font (size 1 1) (thickness 0.15))))')
    model = f"${{KIPRJMOD}}/lib/dropout-kicad-library/3dmodels/{LIB}.3dshapes/{NAME}.step"
    return "\n".join([
        f'(footprint "{NAME}"', '\t(version 20260206)', '\t(generator "pcbnew")', '\t(generator_version "10.0")',
        '\t(layer "F.Cu")',
        f'\t(descr "DO-218AC (Vishay XLD8A24CA datasheet doc 87200 p. 4, mounting pad layout per IPC-7351), {DATASHEET}")',
        '\t(tags "diode TVS DO-218AC DO-218")',
        text("Reference", "REF**", -crt_y - 0.8, "F.SilkS"),
        text("Value", NAME, crt_y + 0.8, "F.Fab"),
        '\t(attr smd)',
        silk, rect(-crt_x, -crt_y, crt_x, crt_y, "F.CrtYd", CRT_W), fab,
        f'\t(fp_text user "${{REFERENCE}}" (at 0 0 0) (layer "F.Fab")\n\t\t(effects (font (size 1 1) (thickness 0.15))))',
        pad(1, PAD1_X, SMALL), pad(2, PAD2_X, BIG),
        f'\t(model "{model}"\n\t\t(offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))',
        ')', ''])


def model(path):
    import cadquery as cq
    body = cq.Workplane("XY").box(BODY_LEN, BODY_W, HEIGHT - 0.1, centered=(False, True, False)) \
        .translate((BODY_X0, 0, 0.1)).edges("|Z").fillet(0.3)
    sink = cq.Workplane("XY").box(SINK_LEN, OVERALL_W, 0.1 + 0.4, centered=(False, True, False)).translate((BODY_X0, 0, 0))
    foot = cq.Workplane("XY").box(LEAD_X1 - (PAD1_X - SMALL[0] / 2), LEAD_W, LEAD_T, centered=(False, True, False)) \
        .translate((PAD1_X - SMALL[0] / 2, 0, 0))
    rise = cq.Workplane("XY").box(LEAD_T, LEAD_W, LEAD_H, centered=(False, True, False)).translate((LEAD_X1 - LEAD_T, 0, 0))
    arm = cq.Workplane("XY").box(LEAD_X1 - BODY_X1, LEAD_W, LEAD_T, centered=(False, True, False)) \
        .translate((BODY_X1, 0, LEAD_H - LEAD_T))
    metal = sink.union(foot).union(rise).union(arm)
    asm = cq.Assembly(name=NAME)
    asm.add(body, name="body", color=cq.Color(0.15, 0.15, 0.15))
    asm.add(metal, name="pins", color=cq.Color(0.82, 0.82, 0.84))
    asm.export(str(path))


def write_normalised(path, text):
    """Write the footprint, then let kicad-cli rewrite it in KiCad's own format."""
    import shutil, subprocess, tempfile
    cli = shutil.which("kicad-cli") or "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
    with tempfile.TemporaryDirectory() as td:
        src, out = Path(td) / "in.pretty", Path(td) / "out.pretty"
        src.mkdir()
        (src / path.name).write_text(text)
        subprocess.run([cli, "fp", "upgrade", "--force", str(src), "-o", str(out)], check=True, capture_output=True)
        shutil.copyfile(out / path.name, path)


def main():
    fp = REPO / "footprints" / f"{LIB}.pretty" / f"{NAME}.kicad_mod"
    st = REPO / "3dmodels" / f"{LIB}.3dshapes" / f"{NAME}.step"
    fp.parent.mkdir(parents=True, exist_ok=True)
    st.parent.mkdir(parents=True, exist_ok=True)
    write_normalised(fp, footprint())
    model(st)
    print(f"footprint  {fp.relative_to(REPO)}\n3D model   {st.relative_to(REPO)}")


if __name__ == "__main__":
    main()
