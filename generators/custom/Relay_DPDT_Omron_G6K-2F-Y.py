#!/usr/bin/env python3
"""Omron (ARATAS) G6K(U)-2F-Y surface-mount DPDT signal relay: footprint and 3D model.

Usage: ~/.cache/dropout/klt-venv/bin/python generators/custom/Relay_DPDT_Omron_G6K-2F-Y.py

Source: Omron G6K datasheet Cat. No. K106-E1-16 (03/2026), p. 7 "Single-winding Latching
G6KU-2F-Y / G6KU-2F-Y-T1" (the same drawing as G6K-2F-Y on p. 6):
- Mounting Dimensions (TOP VIEW), tolerance +/-0.1 mm: eight lands 0.8 x 1.8 mm in two rows 7 mm
  apart (land centres); along a row the lands are at 0, 3.2, 5.4 and 7.6 mm from the pin 1/8 land
  (3.2 mm coil-to-contact pitch, 2.2 mm between contacts, the -Y "terminal arrangement").
- Outline: body 10 +/-0.2 long, 6.5 +/-0.2 wide, 5.2 +/-0.2 high; 7.8 mm across the outside-L
  terminals, terminals 0.5 +/-0.1 wide, the pin 1/8 land centre 1.2 mm from the body end; the
  terminals leave the body 1.6 mm above the seating plane.
- Terminal Arrangement (TOP VIEW): pins 1-4 along one long side, 8-5 opposite; the orientation mark
  is at the pin 1/8 end.
The datasheet's top view has the rows horizontal with pin 1 bottom left; the footprint is that view
turned 90 degrees clockwise, as KiCad's stock Relay_SMD:Relay_DPDT_Omron_G6K-2F-Y: pin 1 top left,
pins 1-4 down the left column (x = -3.5), pins 8-5 down the right column (x = +3.5). Same land
pattern as the stock footprint (compared 2026-10-28); redrawn here for DropOut's model path, a
generated model and a fab outline with the pin 1 chamfer.

3D model dimensions the drawing does not give are marked ESTIMATE.
"""
from fplib import (CRT_CLR, CRT_W, FAB_W, METAL, SILK_PAD, SILK_W, chamfered_rect, fab_ref, footprint_text,
                   line, model_ref, smd_pad, text, up, write_footprint, write_model)

LIB = "DropOut_Relay_SMD"
NAME = "Relay_DPDT_Omron_G6K-2F-Y"

PAD_W, PAD_L = 0.8, 1.8            # land: 0.8 along the row, 1.8 across (p. 7 mounting dimensions)
ROW_X = 3.5                        # rows 7 mm apart
PIN_Y = [-3.8, -0.6, 1.6, 3.8]     # 0, 3.2, 5.4, 7.6 from pin 1, centred on the body
LEFT = [1, 2, 3, 4]                # x = -3.5, top to bottom
RIGHT = [8, 7, 6, 5]               # x = +3.5, top to bottom

BODY_X, BODY_Y, BODY_H = 6.5, 10.0, 5.2   # p. 7 outline (nominal)
TERM_SPAN = 7.8                    # across the outside-L terminals
TERM_W = 0.5                       # terminal width
TERM_Z = 1.6                       # terminals leave the body 1.6 above the seating plane
TERM_T = 0.15                      # ESTIMATE: terminal thickness (not given; typical for G6K stampings)
STANDOFF = 0.05                    # ESTIMATE: body clearance above the seating plane
EDGE_CHAMFER = 0.2                 # ESTIMATE: top edge chamfer as drawn on the outline (about 0.2 mm)
MARK = (2.6, 0.7, 0.05)            # ESTIMATE: orientation mark (oval, length x width x depth), scaled from
                                   # the hatched mark on the terminal-arrangement view; printed black on the
                                   # light case in the datasheet photo (p. 7), modelled as a dark inlay
MARK_Y = -BODY_Y / 2 + 0.9         # ESTIMATE: mark centre, at the pin 1/8 end
GATE = (0.8, 0.3, 0.1)             # ESTIMATE: moulding gate notch at the middle of each long top edge,
                                   # drawn on the 10 mm outline view


def pads():
    out = [smd_pad(n, -ROW_X, y, PAD_L, PAD_W) for n, y in zip(LEFT, PIN_Y)]
    out += [smd_pad(n, ROW_X, y, PAD_L, PAD_W) for n, y in zip(RIGHT, PIN_Y)]
    return out


def footprint():
    pad_x1 = ROW_X + PAD_L / 2                     # 4.4
    bx, by = BODY_X / 2, BODY_Y / 2
    crt_x, crt_y = up(max(pad_x1, bx) + CRT_CLR, 0.05), up(by + CRT_CLR, 0.05)
    sx, sy = bx + SILK_W / 2 + 0.05, by + SILK_W / 2 + 0.05     # silk just outside the body
    clr = PAD_W / 2 + SILK_PAD + SILK_W / 2                      # silk end to land centre (y)
    body = [
        text("Reference", "REF**", -crt_y - 0.8, "F.SilkS"),
        text("Value", NAME, crt_y + 0.8, "F.Fab"),
        line(-sx, -sy, sx, -sy, "F.SilkS", SILK_W), line(-sx, sy, sx, sy, "F.SilkS", SILK_W),
        # pin 1 mark: the top-left silk corner runs out over the pin 1 land row
        line(-sx, PIN_Y[0] - clr, -pad_x1, PIN_Y[0] - clr, "F.SilkS", SILK_W),
    ]
    # long sides: silk between the lands (the body edge passes under them)
    edges = [-sy] + [v for y in PIN_Y for v in (y - clr, y + clr)] + [sy]
    for x in (-sx, sx):
        for y0, y1 in zip(edges[0::2], edges[1::2]):
            if y1 - y0 > 0.1:
                body.append(line(x, y0, x, y1, "F.SilkS", SILK_W))
    body += [
        line(-crt_x, -crt_y, crt_x, -crt_y, "F.CrtYd", CRT_W), line(crt_x, -crt_y, crt_x, crt_y, "F.CrtYd", CRT_W),
        line(crt_x, crt_y, -crt_x, crt_y, "F.CrtYd", CRT_W), line(-crt_x, crt_y, -crt_x, -crt_y, "F.CrtYd", CRT_W),
        chamfered_rect(-bx, -by, bx, by, 1.0, "F.Fab", FAB_W),
        fab_ref(1.0),
        *pads(),
        model_ref(LIB, NAME),
    ]
    return body


def model():
    import cadquery as cq
    bx, by = BODY_X / 2, BODY_Y / 2
    body = (cq.Workplane("XY").box(BODY_X, BODY_Y, BODY_H - STANDOFF)
            .translate((0, 0, STANDOFF + (BODY_H - STANDOFF) / 2))
            .edges(">Z").chamfer(EDGE_CHAMFER))
    # orientation mark: shallow oval recess at the pin 1/8 end of the top face
    mark = (cq.Workplane("XY").workplane(offset=BODY_H - MARK[2]).center(0, MARK_Y)
            .slot2D(MARK[0], MARK[1], 0).extrude(MARK[2] + 0.01))
    body = body.cut(mark)
    inlay = (cq.Workplane("XY").workplane(offset=BODY_H - MARK[2]).center(0, MARK_Y)
             .slot2D(MARK[0], MARK[1], 0).extrude(MARK[2] - 0.01))
    # moulding gate notches on the long top edges, mid-length
    for sx in (-1, 1):
        notch = cq.Workplane("XY").box(GATE[1] * 2, GATE[0], GATE[2] * 2).translate((sx * bx, 0, BODY_H))
        body = body.cut(notch)
    # outside-L terminals: out of the body side at TERM_Z, down the side, foot outward to 7.8 mm
    metal = None
    tip = TERM_SPAN / 2
    for side, ys in ((-1, PIN_Y), (1, PIN_Y)):
        for y in ys:
            leg = cq.Workplane("XY").box(TERM_T, TERM_W, TERM_Z).translate((side * (bx + TERM_T / 2), y, TERM_Z / 2))
            foot = cq.Workplane("XY").box(tip - bx, TERM_W, TERM_T).translate((side * (bx + tip) / 2, y, TERM_T / 2))
            shoulder = cq.Workplane("XY").box(0.3, TERM_W, TERM_T).translate((side * (bx - 0.15 + TERM_T), y, TERM_Z - TERM_T / 2))
            t = leg.union(foot).union(shoulder)
            metal = t if metal is None else metal.union(t)
    # KiCad's model Y is the footprint's -y: mirror so the orientation mark stays at the pin 1 end
    # case colour: light grey-white, as the datasheet photo (p. 7) and KiCad's stock G6K models
    return [(body.mirror("XZ"), (0.90, 0.90, 0.87)), (inlay.mirror("XZ"), (0.08, 0.08, 0.08)),
            (metal.mirror("XZ"), METAL)]


if __name__ == "__main__":
    descr = ("Omron G6K(U)-2F-Y(-T1) DPDT surface-mount signal relay, 10x6.5x5.2mm, outside-L terminals, "
             "land pattern from the datasheet Mounting Dimensions (TOP VIEW), Cat. No. K106-E1-16 p. 7, "
             "https://www.aratas.com/us-en/datasheet_pdf/K106-E1.pdf")
    tags = "Omron ARATAS G6K G6KU G6K-2F-Y G6KU-2F-Y relay DPDT latching SMD"
    print("footprint ", write_footprint(LIB, NAME, footprint_text(NAME, descr, tags, footprint())))
    print("3D model  ", write_model(LIB, NAME, model()))
