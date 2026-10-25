#!/usr/bin/env python3
"""Render a part for visual review: every symbol unit and its footprint as PNG, 3D views of the
footprint with its model as KiCad places it, and the model's bounding box.

Usage (tools Python, for the STEP bounding box):
  ~/.cache/dropout/klt-venv/bin/python scripts/render_part.py <Library>:<Symbol> [-o DIR]

Writes DIR/<Symbol>_unit<N>.png, DIR/<footprint>.png and DIR/<footprint>_3d_{top,bottom,iso}.png
(default DIR: a temp folder, printed), then prints the STEP bounding box. Read the PNGs: pin names
and numbers readable and not overlapping, every pin visible, pin 1 marking, courtyard, fab and
silk; in 3D, the model on its pads, seated on the board, and facing the right way (KiCad's model
Y is the footprint's -y: from below, housings show through mounting holes).
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


POINT = re.compile(r"\((?:start|end|mid|center|xy|at) (-?[\d.]+) (-?[\d.]+)")


def render_3d(cli, fp_lib, fp_name, mod, out, size):
    """Place the footprint on a board just larger than it (the library mounted at
    lib/dropout-kicad-library, as in a project) and render it with kicad-cli: top, bottom, angled."""
    text = mod.read_text()
    pts = [(float(x), float(y)) for x, y in POINT.findall(text)]
    xs, ys = [p[0] for p in pts] or [0], [p[1] for p in pts] or [0]
    placed = text.replace(f'(footprint "{fp_name}"', f'(footprint "{fp_lib}:{fp_name}"\n\t(at 0 0)', 1)
    board = ('(kicad_pcb (version 20260206) (generator "render_part")\n(general (thickness 1.6))\n'
             '(layers (0 "F.Cu" signal) (2 "B.Cu" signal) (1 "F.Mask" user) (3 "B.Mask" user)'
             ' (5 "F.SilkS" user) (7 "B.SilkS" user) (25 "Edge.Cuts" user))\n'
             f"{placed}\n(gr_rect (start {min(xs) - 1} {min(ys) - 1}) (end {max(xs) + 1} {max(ys) + 1})"
             ' (stroke (width 0.05) (type solid)) (fill no) (layer "Edge.Cuts"))\n)\n')
    views = {"top": ["--side", "top"], "bottom": ["--side", "bottom"],
             "iso": ["--side", "top", "--rotate", "-50,0,30"]}
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / "lib").mkdir()
        (Path(td) / "lib" / "dropout-kicad-library").symlink_to(REPO)  # resolves ${KIPRJMOD}/lib/...
        pcb = Path(td) / "board.kicad_pcb"
        pcb.write_text(board)
        for view, opts in views.items():
            png = out / f"{fp_name}_3d_{view}.png"
            r = subprocess.run([cli, "pcb", "render", *opts, "--quality", "high", "-w", str(size), "-h", str(size),
                                "-o", str(png), str(pcb)], capture_output=True, text=True)
            msg = [l for l in (r.stdout + r.stderr).splitlines() if "Could not" in l or ("rror" in l and "NSCocoa" not in l)]
            if r.returncode != 0 or msg:
                print(f"3D render {view}: {' '.join(msg) or r.returncode}")


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
        # The footprint's own model link: KLC F9.3 drops suffixes like _Pad0.7x0.7mm from it
        m = re.search(r'\(model "[^"]*/3dmodels/([^"/]+\.3dshapes/[^"/]+\.step)"', mod.read_text())
        step = REPO / "3dmodels" / (m.group(1) if m else f"{fp_lib}.3dshapes/{fp_name}.step")
        if step.exists():
            render_3d(cli, fp_lib, fp_name, mod, out, args.size)
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
