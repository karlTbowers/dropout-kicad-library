#!/usr/bin/env python3
"""TE DEUTSCH DT13-2P right-angle PCB header footprint and 3D model (no generator covers it).

Usage: ~/.cache/dropout/klt-venv/bin/python generators/custom/TE_DEUTSCH-DT_DT13-2P.py

Sources (archived in dropout-vendor-docs, TE/DT/):
- Holes: TE application specification 114-151046 rev. A, §3.4 p. 5, DT13-2P recommended PCB layout:
  2x Ø1.88±0.05 pin holes at 5.46 pitch, 3x Ø3.43 +0.12/-0 holes for #4-20 Plastite 48 screws
  (inserted from the solder side into the housing bosses), centre screw on the pin centreline
  6.10 from the pin row, outer screws 18.31 apart, 8.00 from the centre screw.
- Body: TE customer drawing DT13-2P rev. B (pins Ø1.56, tails 3.10 below the boss faces,
  1.420 x 1.390 x 1.080 in envelope, flange face .610 from the pin row) and the dimensions of
  TE's own STEP model (CVM 99), which is not redistributed.
- Pin numbering: the drawing's front (mating face) view marks cavity 2; with the mating face
  toward +y and the board below, pin 1 is on the left (x = 0) and pin 2 on the right. The
  application spec's layout figure, labelled "component side", shows the opposite pin under a
  strict reading (it matches the drawing's mounting-face view); the customer drawing takes
  priority (114-151046 §2.3). Amphenol's AT13-2P-BMXX drawing labels the pins on its
  mounting-face view the same way.

Origin at pin 1, mating face toward +y (the panel / board edge side). Geometry: dt_header.py.
"""
from dt_header import Header, footprint, model
from fplib import write_footprint, write_model

DRAWING = "https://www.te.com/commerce/DocumentDelivery/DDEController?Action=srchrtrv&DocNm=DT13-2P&DocType=Customer%20Drawing&DocLang=English&DocFormat=pdf&PartCntxt=DT13-2P"

HEADER = Header(
    lib="DropOut_Connector_TE-Connectivity",
    name="TE_DEUTSCH-DT_DT13-2P_1x02_P5.46mm_Horizontal",
    descr=("TE DEUTSCH DT13-2P 2-pin right-angle PCB header (mates DT06-2S), 5.46 mm pitch, panel flange, "
           "3x #4-20 screw bosses; PCB layout per TE 114-151046 rev. A sec. 3.4, body per customer drawing "
           f"DT13-2P rev. B, {DRAWING}"),
    tags="connector TE DEUTSCH DT DT13 DT13-2P DT06-2S horizontal right angle sealed automotive",
    screw_note="3x #4-20 Plastite 48 screws from the solder side, 0.90 N-m",
    pitch=5.46,
    pin_drill=1.9,              # Ø1.88 ±0.05 finished (114-151046)
    pin_pad=3.2,                # 0.65 mm annular ring for the 13 A contact
    screw_drill=3.5,            # Ø3.43 +0.12/-0 (114-151046), NPTH
    screw_span=18.31, screw_back=8.00, screw_front=6.10,
    # Heights above the board (z) from TE's model. Pins sit on y = 0.
    sections=[
        (-5.97, -0.30, 13.22, 3.88),    # rear deck with the two outer screw bosses (.160 behind them)
        (-0.30, 4.00, 16.60, 24.00),    # pin block
        (4.00, 15.49, 17.65, 27.66),    # main housing up to the flange seal face (.610 from the pins)
        (15.49, 30.10, 8.57, None),     # mating shroud, 17.15 x 17.02, through the panel cutout
    ],
    shroud_z=(5.43, 22.45),             # mating axis 13.94 above the board
    tail=3.10, pin_d=1.56, boss_hole=2.79,
)

if __name__ == "__main__":
    print("footprint ", write_footprint(HEADER.lib, HEADER.name, footprint(HEADER)))
    print("3D model  ", write_model(HEADER.lib, HEADER.name, model(HEADER)))
