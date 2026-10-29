#!/usr/bin/env python3
"""3D models for Amphenol Industrial SurLok Plus 5.7 mm Gen 1.0 (1000 V DC) receptacles with threaded
(M6 stud) termination and flange panel mount: SLPRATPSB (black), SLPRATPSO (orange), SLPRATPSR (red).

Usage: ~/.cache/dropout/klt-venv/bin/python generators/custom/Amphenol_SurLok-Plus_SLPRAT.py

These parts have no footprint (user's decision 2026-10-28): the receptacle sits on the enclosure wall
and its M6 stud screws into a Würth REDCUBE 74660016 (WP-SMRT, M6 internal through thread) on the
board. The symbols are `on_board: false`; a designer who wants the connector in the board's 3D view
adds this model to the 74660016 footprint by hand (see Frame).

No official model or dimensioned drawing is public (searched 2026-10-28: Amphenol Industrial's site,
KiCad and the trusted libraries, CADENAS/3Dfindit, GitHub; distributor CAD tabs are aggregator models,
which DropOut doesn't use). The user is asking Amphenol for the customer drawing and STEP; until then
this is a detailed model built from the catalog (archived in dropout-vendor-docs,
Amphenol-Industrial/SurLok-Plus/surlok-plus-series-ic-10.pdf, IC-10 of 23 Oct 2025).

From the catalog (exact):
- p. 6, Gen 1.0 receptacle, screw termination, 5.7 mm: A = 16.5 (mating face to the flange's panel
  face), B = 36.7 (mating face to stud tip), C = 1.0 (flange gasket), D = 27 (square flange).
- p. 13, panel layout, 5.7 mm: Ø14.3 cutout (the rear body passes through it), 4 × M4 screws on an
  18 × 18 square; screw termination "M6 Nut", 3 N·m (so the stud is M6; coarse pitch 1.0 assumed).
- p. 7: the 5.7 mm plug is 18 wide (D), so the receptacle front fits inside 18.
Estimated (marked ESTIMATE below): every other size. The catalog's p. 6 screw-termination photo is the
10.3 mm part (its stud scales to M10 against D = 35, at about 22 px/mm in the PDF image), so its
proportions were scaled to the 5.7 mm part's catalog dimensions and kept inside the cutout and plug:
front lip, front body, flange-to-body fillet, flange thickness, rear-body length, the metal contact
disc on the rear face, the thread relief, stud length, mating bore and the pin's touch-proof cap.

Frame: z is the connector axis. z = 0 is the rear contact face (the metal disc the lug, busbar or
REDCUBE seats on); the stud points +z, the mating face is at z = -27.8. The model is symmetric about
the XZ and YZ planes, so KiCad's mirrored model Y needs no correction. To show the connector under a
board with the REDCUBE 74660016 on top (its Ø9.0 spigot ends 2.6 below the board's top surface),
add this model to that footprint with offset z = -2.6 mm.
"""
import cadquery as cq

from fplib import METAL, write_model

LIB = "DropOut_Connector_Amphenol"

COLORS = {                         # catalog p. 6 colour code
    "SLPRATPSB": (0.10, 0.10, 0.10),   # B black
    "SLPRATPSO": (0.93, 0.47, 0.05),   # O orange
    "SLPRATPSR": (0.78, 0.09, 0.09),   # R red
}
GASKET = (0.88, 0.88, 0.86)        # flange gasket, light grey as in the catalog photo
CAP = (0.92, 0.92, 0.90)           # touch-proof pin cap

# Axial positions (z, mm). Catalog: A, B, C. ESTIMATE: the split of the rear stack.
A, B, C = 16.5, 36.7, 1.0
Z_FRONT = -27.8                    # mating face; B = 36.7 to the stud tip
Z_TIP = Z_FRONT + B                # 8.9
Z_FLANGE_BACK = Z_FRONT + A        # -11.3: flange panel face (gasket starts here)
Z_GASKET_BACK = Z_FLANGE_BACK + C  # -10.3: gasket face against the panel
FLANGE_T = 2.5                     # ESTIMATE: photo, flange 78 px of the 10.3 mm part's A = 25.8
Z_FLANGE_FRONT = Z_FLANGE_BACK - FLANGE_T
STUD_RELIEF = 1.2                  # ESTIMATE: unthreaded relief between contact face and thread
# Rear stack B - A - C = 19.2: rear body 10.3 + relief 1.2 + thread 7.7 (ESTIMATE: photo proportions
# 16.8 : 2.0 : 12.6 of the 10.3 mm part, scaled to 19.2), so the contact face is at z = 0.

# Radii (mm).
R_REAR = 6.65                      # ESTIMATE: Ø13.3 rear body, under the Ø14.3 panel cutout
R_DISC = 5.0                       # ESTIMATE: Ø10 contact disc (photo: 0.75 of the rear body)
R_FRONT = 7.0                      # ESTIMATE: Ø14.0 front body (photo: 0.94 of the cutout ratio)
R_LIP = 7.7                        # ESTIMATE: Ø15.4 latch lip, inside the plug's 18
LIP_L = 2.2                        # ESTIMATE: lip length
FILLET = 2.0                       # ESTIMATE: flange-to-front-body fillet
R_BORE = 5.2                       # ESTIMATE: Ø10.4 mating bore for the plug's socket insulator
Z_BORE = -17.0                     # ESTIMATE: bore floor
R_PIN = 2.85                       # RADSOK size 5.7 mm pin (catalog: "5.7mm")
Z_PIN = -26.0                      # ESTIMATE: metal pin end, cap beyond
CAP_OUT = 1.0                      # ESTIMATE: cap stands 1.0 proud of the mating face (photo)
FLANGE = 27.0                      # catalog D
FLANGE_R = 2.0                     # ESTIMATE: flange corner radius
HOLE_PITCH = 18.0                  # catalog p. 13
HOLE_D = 4.3                       # ESTIMATE: M4 clearance
M6_MAJOR, M6_MINOR, PITCH = 6.0, 4.92, 1.0   # ISO M6 coarse
R_RELIEF = 2.4                     # ESTIMATE: thread relief radius


def revolve(points):
    """Solid of revolution about z from (r, z) points (closed automatically)."""
    return cq.Workplane("XZ").polyline(points).close().revolve(360, (0, 0, 0), (0, 1, 0))


def housing():
    lip_back = Z_FRONT + LIP_L
    w = (cq.Workplane("XZ")
         .moveTo(R_DISC, 0)
         .lineTo(R_REAR - 0.5, 0)
         .lineTo(R_REAR, -0.5)                                  # rear edge chamfer
         .lineTo(R_REAR, Z_FLANGE_FRONT)
         .lineTo(R_FRONT + FILLET, Z_FLANGE_FRONT)
         .threePointArc((R_FRONT + FILLET * (1 - 0.7071), Z_FLANGE_FRONT - FILLET * (1 - 0.7071)),
                        (R_FRONT, Z_FLANGE_FRONT - FILLET))     # concave fillet into the flange
         .lineTo(R_FRONT, lip_back)
         .lineTo(R_LIP - 0.3, lip_back)
         .lineTo(R_LIP, lip_back - 0.3)                         # lip ramp the plug latch rides over
         .lineTo(R_LIP, Z_FRONT + 0.6)
         .threePointArc((R_LIP - 0.6 + 0.6 * 0.7071, Z_FRONT + 0.6 - 0.6 * 0.7071),
                        (R_LIP - 0.6, Z_FRONT))                 # rounded front edge
         .lineTo(R_BORE + 0.4, Z_FRONT)
         .lineTo(R_BORE, Z_FRONT + 0.4)                         # lead-in chamfer into the bore
         .lineTo(R_BORE, Z_BORE)
         .lineTo(R_PIN, Z_BORE)
         .lineTo(R_PIN, -1.0)
         .lineTo(R_DISC, -1.0)
         .close()
         .revolve(360, (0, 0, 0), (0, 1, 0)))
    # Latch groove behind the lip (ESTIMATE: 0.4 wide, 0.3 deep; the line on the photo's lip).
    groove = revolve([(R_FRONT - 0.3, lip_back + 0.4), (R_FRONT + 0.1, lip_back + 0.4),
                      (R_FRONT + 0.1, lip_back), (R_FRONT - 0.3, lip_back)])
    w = w.cut(groove)
    holes = [(sx * HOLE_PITCH / 2, sy * HOLE_PITCH / 2) for sx in (-1, 1) for sy in (-1, 1)]
    flange = (cq.Workplane("XY").workplane(offset=Z_FLANGE_FRONT)
              .rect(FLANGE, FLANGE).extrude(FLANGE_T)
              .edges("|Z").fillet(FLANGE_R)
              .faces(">Z").workplane().pushPoints(holes).hole(HOLE_D)
              .faces(">Z").workplane().hole(2 * R_PIN))
    return w.union(flange)


def gasket():
    holes = [(sx * HOLE_PITCH / 2, sy * HOLE_PITCH / 2) for sx in (-1, 1) for sy in (-1, 1)]
    return (cq.Workplane("XY").workplane(offset=Z_FLANGE_BACK)
            .rect(FLANGE, FLANGE).extrude(C)
            .edges("|Z").fillet(FLANGE_R)
            .faces(">Z").workplane().pushPoints(holes).hole(HOLE_D)
            .faces(">Z").workplane().hole(2 * R_REAR))


def terminal():
    """Contact pin, rear contact disc, thread relief and M6 stud as one metal part. The thread is
    drawn as 60° grooves at the M6 pitch (a helix adds nothing at board-render scale)."""
    rmaj, rmin = M6_MAJOR / 2, M6_MINOR / 2
    pts = [(0, Z_PIN), (R_PIN, Z_PIN), (R_PIN, -1.0), (R_DISC, -1.0), (R_DISC, 0),
           (R_RELIEF, 0), (R_RELIEF, STUD_RELIEF)]
    z = STUD_RELIEF
    while z + PITCH <= Z_TIP - 0.6 + 1e-9:
        flank = (rmaj - rmin) * 0.5774                    # tan 30°: 60° thread flanks
        pts += [(rmin, z), (rmaj, z + flank), (rmaj, z + PITCH - flank - 0.125), (rmin, z + PITCH - 0.125)]
        z += PITCH
    pts += [(rmin, z), (rmaj - 0.3, z + 0.3), (rmin, Z_TIP), (0, Z_TIP)]   # tip chamfer
    return revolve(pts)


def cap():
    return revolve([(0, Z_PIN), (R_PIN, Z_PIN), (R_PIN, Z_FRONT - CAP_OUT + 0.6),
                    (R_PIN - 0.6, Z_FRONT - CAP_OUT), (0, Z_FRONT - CAP_OUT)])


if __name__ == "__main__":
    parts_common = [(gasket(), GASKET), (terminal(), METAL), (cap(), CAP)]
    body = housing()
    for mpn, color in COLORS.items():
        print("3D model  ", write_model(LIB, f"Amphenol_SurLok-Plus_{mpn}", [(body, color), *parts_common]))
