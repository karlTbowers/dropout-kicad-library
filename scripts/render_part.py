#!/usr/bin/env python3
"""Render a part for visual review: every symbol unit and its footprint as PNG, plus the 3D
model's bounding box.

Usage (tools Python, for the STEP bounding box):
  ~/.cache/dropout/klt-venv/bin/python scripts/render_part.py <Library>:<Symbol> [-o DIR]

Writes DIR/<Symbol>_unit<N>.png and DIR/<footprint>.png (default DIR: a temp folder, printed),
then prints the STEP bounding box. Read the PNGs: pin names and numbers readable and not
overlapping, every pin visible, pin 1 marking, courtyard, fab and silk.
macOS only for the PNGs (qlmanage); SVGs are padded to a square first because qlmanage crops
thumbnails to a square.
"""
import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_symbol_fields import properties, top_level_symbols  # noqa: E402
from symbolgen import kicad_cli  # noqa: E402

REPO = Path(__file__).resolve().parent.parent


def square_svg(path):
    t = path.read_text()
    m = re.search(r'viewBox="([-\d.]+) ([-\d.]+) ([\d.]+) ([\d.]+)"', t)
    if not m:
        return
    x, y, w, h = map(float, m.groups())
    s = max(w, h)
    t = t.replace(m.group(0), f'viewBox="{x - (s - w) / 2} {y - (s - h) / 2} {s} {s}"', 1)
    t = re.sub(r'(<svg[^>]*?)\swidth="[^"]*"', rf'\1 width="{s}mm"', t, count=1)
    t = re.sub(r'(<svg[^>]*?)\sheight="[^"]*"', rf'\1 height="{s}mm"', t, count=1)
    path.write_text(t)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("symbol", help="<Library>:<Symbol>, e.g. DropOut_Power:LM74910HQRGERQ1")
    ap.add_argument("-o", "--out")
    ap.add_argument("--size", type=int, default=1200, help="PNG size in pixels")
    args = ap.parse_args()
    lib, name = args.symbol.split(":", 1)
    lib_file = REPO / "symbols" / f"{lib}.kicad_sym"
    body = dict(top_level_symbols(lib_file.read_text())).get(name)
    if body is None:
        sys.exit(f"render_part: {name} not found in {lib_file}")
    fp = properties(body).get("Footprint", "")
    out = Path(args.out or tempfile.mkdtemp(prefix=f"render-{name}-"))
    svg = out / "svg"
    svg.mkdir(parents=True, exist_ok=True)
    cli = kicad_cli() or sys.exit("render_part: kicad-cli not found")
    subprocess.run([cli, "sym", "export", "svg", str(lib_file), "-s", name, "-o", str(svg)], check=True, capture_output=True)
    step = None
    if ":" in fp:
        fp_lib, fp_name = fp.split(":", 1)
        mod = REPO / "footprints" / f"{fp_lib}.pretty" / f"{fp_name}.kicad_mod"
        with tempfile.TemporaryDirectory() as td:
            one = Path(td) / "one.pretty"
            one.mkdir()
            shutil.copy(mod, one)
            subprocess.run([cli, "fp", "export", "svg", str(one), "-o", str(svg)], check=True, capture_output=True)
        step = REPO / "3dmodels" / f"{fp_lib}.3dshapes" / f"{fp_name}.step"
    for f in svg.glob("*.svg"):
        square_svg(f)
        subprocess.run(["qlmanage", "-t", "-s", str(args.size), "-o", str(out), str(f)], capture_output=True)
        png = out / f"{f.name}.png"
        if png.exists():
            png.rename(out / f"{f.stem}.png")
    for p in sorted(out.glob("*.png")):
        print(p)
    if step and step.exists():
        try:
            import cadquery as cq
            b = cq.importers.importStep(str(step)).val().BoundingBox()
            print(f"STEP {step.name}: x {b.xmin:.2f}..{b.xmax:.2f}  y {b.ymin:.2f}..{b.ymax:.2f}  z {b.zmin:.2f}..{b.zmax:.2f}")
        except ImportError:
            print("STEP bounding box skipped (run with ~/.cache/dropout/klt-venv/bin/python)")
    elif fp:
        print(f"no 3D model at {step}")


if __name__ == "__main__":
    main()
