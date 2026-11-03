#!/usr/bin/env python3
"""3D models for the DropOut_Capacitor_SMD aluminium electrolytic / hybrid polymer cans.

Usage: ~/.cache/dropout/klt-venv/bin/python generators/custom/CP_Elec_SMD.py

The footprints come from kicad-library-tools' capacitor/SMD/elec_round_polarized generator
(generators/capacitor/SMD/elec_round_polarized/DropOut_Capacitor_SMD.yaml, run with --no-3d). Its
model generator at KLT_REF (scripts/klc_check.py) draws the can with the anode-side base chamfer
at +x and the cathode mark at -x, and no longer applies the spec's `rotation: 180` (model.py calls
make_radial_smd and exports without rotating), so the model came out turned half a turn on the
footprint: minus mark over pad 1 (+). KiCad's own Capacitor_SMD.3dshapes models, made before
that change, have the mark over pad 2. This script draws the same geometry with that module's
make_radial_smd and turns every part 180 deg about Z before export, so the anode side sits on
pad 1 and the model keeps zero offset and rotation in the footprint (KLC F9.3).

Parameters: L = the tallest built part's maximum height (data-sheet L + 0.3 mm), so a board's
height checks are conservative; A = base 6.6 mm; H = terminal span over both (Nichicon A 7.3 mm,
the larger of Nichicon and Chemi-Con); P = terminal gap (between Nichicon's 2.2 and Chemi-Con's
1.9 mm); W = terminal width 0.65 mm (Nichicon/Chemi-Con 0.5-0.8, Panasonic 0.65).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from klc_check import tools_dir  # noqa: E402
from fplib import write_model  # noqa: E402

sys.path.insert(0, str(tools_dir() / "src"))
from generators.capacitor.SMD.elec_round_polarized.cp_radial_smd import make_radial_smd  # noqa: E402

LIB = "DropOut_Capacitor_SMD"
# kicad-library-tools shaderColors: "metal grey pins" and "black body" diffuse colours
METAL = (0.824, 0.820, 0.781)
BLACK = (0.148, 0.145, 0.145)

MODELS = {
    # Chemi-Con HXC F61 / Panasonic ZC D: 5.8 +/- 0.3
    "CP_Elec_6.3x5.8": dict(L=6.1, D=6.3, A=6.6, H=7.3, P=2.0, W=0.65, PM=True, rotation=180),
    # Nichicon GYF / UCZ 6.3x7.7: 7.7 +/- 0.3
    "CP_Elec_6.3x7.7": dict(L=8.0, D=6.3, A=6.6, H=7.3, P=2.0, W=0.65, PM=True, rotation=180),
}

for name, params in MODELS.items():
    body, base, mark, pins = make_radial_smd(params)   # reads `rotation` but does not apply it
    turn = lambda s: s.rotate((0, 0, 0), (0, 0, 1), 180)
    parts = [(turn(body), METAL), (turn(base), BLACK), (turn(pins), METAL)]
    if mark is not None:
        parts.append((turn(mark), BLACK))
    print(write_model(LIB, name, parts))
