#!/usr/bin/env python3
"""Amphenol Sine Systems BoardLock AT13-2P-BMxx right-angle PCB header footprint and 3D model.

Usage: ~/.cache/dropout/klt-venv/bin/python generators/custom/Amphenol_AT13-2P-BMxx.py

Source: Amphenol Sine drawing C-AT13-2P-BMXX rev. A2 (10 Jul 2020, "REF: DT13-2P"), covering
AT13-2P-BM01..BM04 (gold/tin plating, with or without potting); archived in dropout-vendor-docs,
Amphenol-Sine/BoardLock/.
- Holes, "recommended PCB layout": 2x Ø1.80 +0.1/-0 pin holes at 5.40 ±0.05 pitch (TE's DT13-2P
  layout is Ø1.88 ±0.05 at 5.46, so this is a separate footprint), 3x Ø3.43 holes for #4-20
  [M3.12 x 1.27] thread-forming screws from the solder side (0.68-1.13 N-m), outer screws
  18.31 ±0.10 apart, 8.00 ±0.10 behind the centre screw, centre screw 6.10 ±0.10 from the pin row.
- Body: 36.1 overall, 21.5 from the flange to the rear, flange seal face 15.5 from the pin row,
  rear 4.1 behind the outer screws, flange 35.2 wide, boss block 26.4, shroud 17.1; 27.4 tall
  with the mating axis 13.8 above the board; pin spacer 3.9; pins Ø1.58, tails 3.1 ±0.4.
  Section depths not dimensioned on the drawing are scaled from its top view.
- Pin numbering: the drawing's mounting-face view marks the pins "2" and "1", which gives pin 1
  on the left (x = 0) with the mating face toward +y, as for TE's DT13-2P.

Origin at pin 1, mating face toward +y (the panel / board edge side). Geometry: dt_header.py.
"""
from dt_header import Header, footprint, model
from fplib import write_footprint, write_model

DRAWING = "https://www.amphenol-sine.com/pdf/datasheet/AT13-2P-BM04.pdf"

HEADER = Header(
    lib="DropOut_Connector_Amphenol",
    name="Amphenol_AT13-2P-BMxx_1x02_P5.40mm_Horizontal",
    descr=("Amphenol Sine BoardLock AT13-2P-BMxx 2-pin right-angle PCB header (mates AT06-2S / DT06-2S), "
           "5.40 mm pitch, panel flange, 3x #4-20 screw bosses; PCB layout and body per drawing "
           f"C-AT13-2P-BMXX rev. A2, {DRAWING}"),
    tags="connector Amphenol Sine BoardLock AT AT13 AT13-2P AT06-2S DT13-2P horizontal right angle sealed automotive",
    screw_note="3x #4-20 thread-forming screws from the solder side, 0.68-1.13 N-m",
    pitch=5.40,
    pin_drill=1.85,             # Ø1.80 +0.1/-0 finished: middle of the range
    pin_pad=3.2,                # 0.675 mm annular ring for the 13 A contact
    screw_drill=3.43,           # Ø3.43, NPTH
    screw_span=18.31, screw_back=8.00, screw_front=6.10,
    sections=[
        (-6.00, 0.60, 13.20, 3.90),     # pin spacer / rear deck under the outer bosses (4.1 behind them)
        (0.60, 4.60, 16.80, 22.60),     # pin block
        (4.60, 15.50, 17.60, 27.40),    # housing up to the flange seal face (15.5 from the pins)
        (15.50, 30.10, 8.55, None),     # mating shroud, 17.1, through the panel cutout (36.1 overall)
    ],
    shroud_z=(5.25, 22.35),             # mating axis 13.8 above the board
    tail=3.10, pin_d=1.58, boss_hole=2.79,
)

if __name__ == "__main__":
    print("footprint ", write_footprint(HEADER.lib, HEADER.name, footprint(HEADER)))
    print("3D model  ", write_model(HEADER.lib, HEADER.name, model(HEADER)))
