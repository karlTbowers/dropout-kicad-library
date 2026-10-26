#!/usr/bin/env python3
"""Render two 3D models side by side on two copies of the same footprint, to compare our model with a
trusted library's (add-part step 2a).

Usage:
  python3 scripts/compare_models.py <FootprintLib>:<footprint> LEFT.step RIGHT.step -o OUT_PREFIX
      [--labels "DropOut generated" "Würth official"] [--size 1600x900]

Writes OUT_PREFIX_iso.png (angled) and OUT_PREFIX_front.png (side view) with kicad-cli pcb render. Both
models are placed exactly as the footprint places its own (its offset, scale and rotation are kept); only
the model path changes. The labels are printed on the board's silkscreen.
"""
import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from symbolgen import kicad_cli  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
POINT = re.compile(r"\((?:start|end|mid|center|xy|at) (-?[\d.]+) (-?[\d.]+)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("footprint", help="<FootprintLib>:<footprint>, e.g. DropOut_TerminalBlock_Wuerth:Wuerth_...")
    ap.add_argument("left", type=Path)
    ap.add_argument("right", type=Path)
    ap.add_argument("-o", "--out", required=True, help="output prefix (…_iso.png, …_front.png)")
    ap.add_argument("--labels", nargs=2, default=["DropOut generated", "trusted library"])
    ap.add_argument("--size", default="1600x900")
    ap.add_argument("--zoom", default="0.7", help="kicad-cli camera zoom (smaller shows more)")
    args = ap.parse_args()
    lib, name = args.footprint.split(":", 1)
    text = (REPO / "footprints" / f"{lib}.pretty" / f"{name}.kicad_mod").read_text()
    crt = "".join(re.findall(r"\(fp_(?:line|rect|poly)\b.*?\(layer \"F\.CrtYd\"\)", text, re.S)) or text
    pts = [(float(x), float(y)) for x, y in POINT.findall(crt)]
    w = max(abs(p[0]) for p in pts) + 4         # half spacing: courtyard plus a gap
    h = max(abs(p[1]) for p in pts) + 3

    def placed(x, model):
        t = re.sub(r'\(model "[^"]*"', f'(model "{model.resolve()}"', text)
        return t.replace(f'(footprint "{name}"', f'(footprint "{lib}:{name}"\n\t(at {x:.2f} 0)', 1)

    label = f"{args.labels[0]} (left)   |   {args.labels[1]} (right)"
    bw = max(2 * w, len(label) * 0.6 + 2)     # board half width: both footprints and the label fit
    board = ('(kicad_pcb (version 20260206) (generator "compare_models")\n(general (thickness 1.6))\n'
             '(layers (0 "F.Cu" signal) (2 "B.Cu" signal) (1 "F.Mask" user) (3 "B.Mask" user)'
             ' (5 "F.SilkS" user) (7 "B.SilkS" user) (25 "Edge.Cuts" user))\n'
             f"{placed(-w, args.left)}\n{placed(w, args.right)}\n"
             f'(gr_text "{label}" (at 0 {h + 1.5:.2f}) (layer "F.SilkS") (effects (font (size 1.6 1.6) (thickness 0.25))))\n'
             f'(gr_rect (start {-bw:.2f} {-h:.2f}) (end {bw:.2f} {h + 3:.2f}) (stroke (width 0.05) (type solid))'
             ' (fill no) (layer "Edge.Cuts"))\n)\n')
    cli = kicad_cli() or sys.exit("compare_models: kicad-cli not found")
    width, height = args.size.split("x")
    with tempfile.TemporaryDirectory() as td:
        pcb = Path(td) / "compare.kicad_pcb"
        pcb.write_text(board)
        for view, opts in {"iso": ["--side", "top", "--rotate", "-55,0,25"], "front": ["--side", "front"]}.items():
            png = Path(f"{args.out}_{view}.png")
            r = subprocess.run([cli, "pcb", "render", *opts, "--zoom", args.zoom, "--quality", "high", "-w", width, "-h", height,
                                "-o", str(png), str(pcb)], capture_output=True, text=True)
            print(png if png.exists() else f"{view}: render failed: {(r.stdout + r.stderr)[-300:]}")


if __name__ == "__main__":
    main()
