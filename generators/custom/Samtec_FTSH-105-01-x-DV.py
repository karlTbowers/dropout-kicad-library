#!/usr/bin/env python3
"""3D model for Samtec_FTSH-105-01-x-DV_2x05_P1.27mm_Vertical_SMD (footprint made by the
kicad-library-tools pin_header_socket generator from generators/connector/pin_header_socket/
DropOut_Samtec.yaml, which has no model generator).

Dimensions: Samtec FTSH-1XX-XX-XXX-DV-XXX-XXX-X-XX print rev. FZ, Fig. 1 and Table 1:
body 3.43 (.135) x 5 x 1.27 mm, 2.51 (.099) high; .016 (0.41) square posts, -01 lead style
3.05 (.120) above the body; tails 5.84 (.230) tip to tip. The -K keying piece is not modelled.

Run with the tools Python: ~/.cache/dropout/klt-venv/bin/python generators/custom/Samtec_FTSH-105-01-x-DV.py
"""
from fplib import BODY, write_model

LIB = "DropOut_Connector_Samtec"
NAME = "Samtec_FTSH-105-01-x-DV_2x05_P1.27mm_Vertical_SMD"
GOLD = (0.86, 0.74, 0.32)
POS, PITCH = 5, 1.27
BODY_W, BODY_H = 3.43, 2.51
POST, POST_H = 0.41, 3.05
TAIL_X, TAIL_T = 5.84 / 2, 0.2


def model():
    import cadquery as cq
    box = lambda x0, x1, y0, y1, z0, z1: cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0) \
        .translate(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    length = POS * PITCH
    body = box(-BODY_W / 2, BODY_W / 2, -length / 2, length / 2, TAIL_T, BODY_H)
    metal = None
    for i in range(POS):
        y = (i - (POS - 1) / 2) * PITCH
        for side in (-1, 1):
            x = side * PITCH / 2
            pin = box(x - POST / 2, x + POST / 2, y - POST / 2, y + POST / 2, 0, BODY_H + POST_H) \
                .union(box(min(x, side * TAIL_X), max(x, side * TAIL_X), y - POST / 2, y + POST / 2, 0, TAIL_T))
            metal = pin if metal is None else metal.union(pin)
    return [(body, BODY), (metal, GOLD)]


if __name__ == "__main__":
    print("3D model  ", write_model(LIB, NAME, model()))
