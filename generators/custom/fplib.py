"""Shared helpers for DropOut's custom footprint scripts (packages no kicad-library-tools
generator covers). Layer widths and text follow KiCad's stock footprints: silk 0.12, fab 0.10,
courtyard 0.05 lines, Reference on F.SilkS, Value and ${REFERENCE} on F.Fab.
"""
import math
import shutil
import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SILK_W, FAB_W, CRT_W = 0.12, 0.10, 0.05
SILK_PAD = 0.2      # silk to copper clearance
CRT_CLR = 0.25      # courtyard clearance around pads and body


def r(v, grid=0.0001):
    return round(round(v / grid) * grid, 4)


def up(v, grid=0.01):
    """Round away from zero to a grid (courtyards)."""
    return math.copysign(math.ceil(abs(v) / grid - 1e-9) * grid, v)


def line(x1, y1, x2, y2, layer, w):
    return (f'\t(fp_line (start {r(x1)} {r(y1)}) (end {r(x2)} {r(y2)})\n'
            f'\t\t(stroke (width {w}) (type solid)) (layer "{layer}"))')


def poly(points, layer, w, fill=True):
    pts = " ".join(f"(xy {r(x)} {r(y)})" for x, y in points)
    return (f'\t(fp_poly (pts {pts})\n\t\t(stroke (width {w}) (type solid)) '
            f'(fill {"yes" if fill else "no"}) (layer "{layer}"))')


def rect(x1, y1, x2, y2, layer, w):
    return "\n".join([line(x1, y1, x2, y1, layer, w), line(x2, y1, x2, y2, layer, w),
                      line(x2, y2, x1, y2, layer, w), line(x1, y2, x1, y1, layer, w)])


def chamfered_rect(x1, y1, x2, y2, c, layer, w):
    """Rectangle with the top-left corner chamfered (pin 1 on the fab layer)."""
    pts = [(x1 + c, y1), (x2, y1), (x2, y2), (x1, y2), (x1, y1 + c), (x1 + c, y1)]
    return "\n".join(line(*pts[i], *pts[i + 1], layer, w) for i in range(len(pts) - 1))


def smd_pad(num, x, y, w, h, rratio=0.25, extra=""):
    return (f'\t(pad "{num}" smd roundrect (at {r(x)} {r(y)}) (size {r(w)} {r(h)})\n'
            f'\t\t(layers "F.Cu" "F.Mask" "F.Paste") (roundrect_rratio {rratio}){extra})')


def custom_pad(num, anchor_xy, anchor_wh, polys):
    """Custom-shape SMD pad: a rectangular anchor plus filled polygons (relative to the anchor)."""
    prims = "\n".join(
        "\t\t\t(gr_poly (pts " + " ".join(f"(xy {r(x)} {r(y)})" for x, y in pts) + ") (width 0) (fill yes))"
        for pts in polys)
    return (f'\t(pad "{num}" smd custom (at {r(anchor_xy[0])} {r(anchor_xy[1])}) '
            f'(size {r(anchor_wh[0])} {r(anchor_wh[1])})\n'
            f'\t\t(layers "F.Cu" "F.Mask" "F.Paste")\n'
            f'\t\t(options (clearance outline) (anchor rect))\n'
            f'\t\t(primitives\n{prims}\n\t\t))')


def text(kind, val, y, layer, size=1.0):
    th = round(size * 0.15, 3)
    return (f'\t(property "{kind}" "{val}" (at 0 {r(y)} 0) (layer "{layer}")\n'
            f'\t\t(effects (font (size {size} {size}) (thickness {th}))))')


def fab_ref(size=1.0):
    th = round(size * 0.15, 3)
    return (f'\t(fp_text user "${{REFERENCE}}" (at 0 0 0) (layer "F.Fab")\n'
            f'\t\t(effects (font (size {size} {size}) (thickness {th}))))')


def model_ref(lib, name):
    path = f"${{KIPRJMOD}}/lib/dropout-kicad-library/3dmodels/{lib}.3dshapes/{name}.step"
    return f'\t(model "{path}"\n\t\t(offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))'


def footprint_text(name, descr, tags, body, attr="smd"):
    return "\n".join([f'(footprint "{name}"', '\t(version 20260206)', '\t(generator "pcbnew")',
                      '\t(generator_version "10.0")', '\t(layer "F.Cu")', f'\t(descr "{descr}")',
                      f'\t(tags "{tags}")', *body[:2], f'\t(attr {attr})', *body[2:], ')', ''])


def write_footprint(lib, name, text_):
    """Write the footprint, then let kicad-cli rewrite it in KiCad's own format."""
    path = REPO / "footprints" / f"{lib}.pretty" / f"{name}.kicad_mod"
    path.parent.mkdir(parents=True, exist_ok=True)
    cli = shutil.which("kicad-cli") or "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
    with tempfile.TemporaryDirectory() as td:
        src, out = Path(td) / "in.pretty", Path(td) / "out.pretty"
        src.mkdir()
        (src / path.name).write_text(text_)
        subprocess.run([cli, "fp", "upgrade", "--force", str(src), "-o", str(out)], check=True, capture_output=True)
        shutil.copyfile(out / path.name, path)
    return path


def write_model(lib, name, parts):
    """parts: list of (cadquery Workplane, (r, g, b)). Saved as one coloured STEP."""
    import cadquery as cq
    path = REPO / "3dmodels" / f"{lib}.3dshapes" / f"{name}.step"
    path.parent.mkdir(parents=True, exist_ok=True)
    asm = cq.Assembly(name=name)
    for i, (shape, color) in enumerate(parts):
        asm.add(shape, name=f"part{i}", color=cq.Color(*color))
    asm.export(str(path))
    return path


BODY = (0.15, 0.15, 0.15)
METAL = (0.82, 0.82, 0.84)
