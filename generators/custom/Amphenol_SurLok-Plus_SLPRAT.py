#!/usr/bin/env python3
"""3D models for Amphenol Industrial SurLok Plus 5.7 mm Gen 1.0 (1000 V DC) receptacles with threaded
(M6 stud) termination and flange panel mount: SLPRATPSB (black), SLPRATPSO (orange), SLPRATPSR (red).

Usage: ~/.cache/dropout/klt-venv/bin/python generators/custom/Amphenol_SurLok-Plus_SLPRAT.py

These parts have no footprint (user's decision 2026-10-28): the receptacle sits on the enclosure wall
and its M6 stud screws into a Würth REDCUBE 74660016 (WP-SMRT, M6 internal through thread) on the
board. The symbols are `on_board: false`; a designer who wants the connector in the board's 3D view
adds this model to the 74660016 footprint by hand (see Frame).

Sources, archived in dropout-vendor-docs Amphenol-Industrial/SurLok-Plus/ (rebuilt 2026-11-02; the first
model was estimated from catalogue photos because these hadn't been found):
- Customer drawing C10-730187 rev. F (2022-10-13), "5.7MM SURLOK PLUS RECEPTACLE", screw type, from the
  SLPRATPSB page on amphenol-industrial.de (Amphenol Tuchel). Stamped "controlled document", so it is
  measured from, not linked. Exact: 13.50 front face to flange, 16.50 to the flange's back (flange 3.0),
  gasket 1.0, 9.50 from the flange's back to the rear face (Ø14 rear body), stud 10.70 REF, M6 x 1.0;
  27 square flange with R4 corners, 4 x M4 on 18 x 18; panel cutout Ø14.20.
- Amphenol's customer STEP c3d-slpratpsb-01-000.stp (C10-730187-X20_CUS_D, one solid, no licence stated):
  measured only, not redistributed. Measured ("STEP" below): latch lip, tube and bore radii, flange fillet,
  bore depth, pin collar, hex shoulder, relief and thread, pin cap.
- Catalogue IC-10 (2025-10-23): A 16.5, B 36.7, C 1.0, D 27, as the drawing.
Estimated (marked ESTIMATE): the flange hole diameter and the split of the pin between metal and its
touch-proof cap; the STEP is one solid.

Frame: z is the connector axis. z = 0 is the seating face (the back of the stud's hex shoulder, what the
lug, busbar or REDCUBE seats on); the stud points +z; the front face is at z = -26.75 and the pin cap
stands 1.0 beyond it. The model is symmetric about the XZ and YZ planes, so KiCad's mirrored model Y needs
no correction. To show the connector under a board with the REDCUBE 74660016 on top (its Ø9.0 spigot ends
2.6 below the board's top surface), add this model to that footprint with offset z = -2.6 mm.
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

# Axial positions (z, mm), seating face at 0. Drawing: 13.50 / 16.50 / 1.0 / 9.50 / 10.70 REF.
Z_HEX = -0.75                      # STEP: hex shoulder 0.75 thick, behind the rear face
Z_REAR = Z_HEX                     # rear face of the body
Z_GASKET_BACK = Z_REAR - 8.5       # drawing: 9.50 flange back to rear face, less the 1.0 gasket -> -9.25
Z_FLANGE_BACK = Z_GASKET_BACK - 1.0    # -10.25
Z_FLANGE_FRONT = Z_FLANGE_BACK - 3.0   # drawing 16.50 - 13.50: -13.25
Z_FRONT = Z_FLANGE_FRONT - 13.5    # drawing 13.50: -26.75 front face
Z_TIP = Z_REAR + 10.7              # drawing 10.70 REF: 9.95
Z_CAP = Z_FRONT - 1.0              # STEP: cap 1.0 beyond the front face
Z_FLOOR = -7.0                     # STEP: bore floor 19.75 behind the front face

# Radii (mm).
R_REAR = 7.0                       # drawing Ø14, STEP
R_TUBE = 7.0                       # STEP: Ø14 front tube
R_LIP = 8.0                        # STEP: Ø16 latch lip, inside the plug's Ø16.1 skirt
R_LIP_FRONT = 6.8                  # STEP: front edge of the lip, rounded
LIP = (Z_FRONT + 1.0, Z_FRONT + 1.25, Z_FRONT + 2.75)  # STEP: lip full from here, to here, ramp to the tube
R_FILLET_END, Z_FILLET0 = 8.5, Z_FLANGE_FRONT - 1.75  # STEP: tube flares from Ø14 to Ø17 into the flange
R_BORE_FRONT, R_BORE_BACK = 6.2, 5.8   # STEP: bore Ø12.4 at the mouth tapering to Ø11.6
Z_BORE_TAPER = Z_FRONT + 8.0       # STEP: taper ends here
R_PIN = 2.8                        # STEP, RADSOK size 5.7
PIN_COLLAR = (-12.0, -11.0, 3.9)   # STEP: collar on the pin near the bore floor (z from, z to, r)
Z_CAP_END = Z_FRONT + 2.0          # ESTIMATE: where the cap meets the metal pin
FLANGE, FLANGE_R = 27.0, 4.0       # drawing: 27 square, R4 corners
HOLE_PITCH = 18.0                  # drawing
HOLE_D = 4.2                       # ESTIMATE: flange holes as the drawing's Ø4.20 panel holes (M4)
HEX_AF = 8.8                       # STEP: 8.8 across flats
R_RELIEF, Z_RELIEF = 2.6, 0.75     # STEP: relief from the seat to the thread
M6_MAJOR, M6_MINOR, PITCH = 6.0, 4.92, 1.0   # ISO M6 coarse


def revolve(points):
    """Solid of revolution about z from (r, z) points (closed automatically)."""
    return cq.Workplane("XZ").polyline(points).close().revolve(360, (0, 0, 0), (0, 1, 0))


def housing():
    lip0, lip1, lip2 = LIP
    w = (cq.Workplane("XZ")
         .moveTo(R_PIN, Z_REAR)
         .lineTo(R_REAR - 0.3, Z_REAR)
         .lineTo(R_REAR, Z_REAR - 0.3)                          # rear edge chamfer
         .lineTo(R_REAR, Z_FLANGE_FRONT)
         .lineTo(R_FILLET_END, Z_FLANGE_FRONT)
         .threePointArc((R_FILLET_END - (R_FILLET_END - R_TUBE) * 0.7071, Z_FILLET0 + (Z_FLANGE_FRONT - Z_FILLET0) * 0.7071),
                        (R_TUBE, Z_FILLET0))                     # concave flare into the flange
         .lineTo(R_TUBE, lip2)
         .lineTo(R_LIP, lip1)                                   # ramp the plug latch rides over
         .lineTo(R_LIP, lip0)
         .threePointArc((R_LIP_FRONT + 0.75, Z_FRONT + 0.25), (R_LIP_FRONT, Z_FRONT))   # rounded front
         .lineTo(R_BORE_FRONT + 0.3, Z_FRONT)
         .lineTo(R_BORE_FRONT, Z_FRONT + 0.3)                   # lead-in chamfer into the bore
         .lineTo(R_BORE_BACK, Z_BORE_TAPER)
         .lineTo(R_BORE_BACK, Z_FLOOR)
         .lineTo(R_PIN, Z_FLOOR)
         .close()
         .revolve(360, (0, 0, 0), (0, 1, 0)))
    holes = [(sx * HOLE_PITCH / 2, sy * HOLE_PITCH / 2) for sx in (-1, 1) for sy in (-1, 1)]
    flange = (cq.Workplane("XY").workplane(offset=Z_FLANGE_FRONT)
              .rect(FLANGE, FLANGE).extrude(Z_FLANGE_BACK - Z_FLANGE_FRONT)
              .edges("|Z").fillet(FLANGE_R)
              .faces(">Z").workplane().pushPoints(holes).hole(HOLE_D)
              .faces(">Z").workplane().hole(2 * R_BORE_BACK))
    return w.union(flange)


def gasket():
    holes = [(sx * HOLE_PITCH / 2, sy * HOLE_PITCH / 2) for sx in (-1, 1) for sy in (-1, 1)]
    return (cq.Workplane("XY").workplane(offset=Z_FLANGE_BACK)
            .rect(FLANGE, FLANGE).extrude(Z_GASKET_BACK - Z_FLANGE_BACK)
            .edges("|Z").fillet(FLANGE_R)
            .faces(">Z").workplane().pushPoints(holes).hole(HOLE_D)
            .faces(">Z").workplane().hole(2 * R_REAR))


def terminal():
    """Pin, collar, hex shoulder, relief and M6 stud as one metal part. The thread is drawn as 60°
    grooves at the M6 pitch (a helix adds nothing at board-render scale)."""
    rmaj, rmin = M6_MAJOR / 2, M6_MINOR / 2
    c0, c1, rc = PIN_COLLAR
    pts = [(0, Z_CAP_END), (R_PIN, Z_CAP_END), (R_PIN, c0), (rc, c0), (rc, c1), (R_PIN, c1),
           (R_PIN, Z_HEX), (R_RELIEF, Z_HEX), (R_RELIEF, Z_RELIEF)]
    z = Z_RELIEF + 0.25
    pts.append((R_RELIEF, z))
    while z + PITCH <= Z_TIP - 0.6 + 1e-9:
        flank = (rmaj - rmin) * 0.5774                    # tan 30°: 60° thread flanks
        pts += [(rmin, z), (rmaj, z + flank), (rmaj, z + PITCH - flank - 0.125), (rmin, z + PITCH - 0.125)]
        z += PITCH
    pts += [(rmin, z), (rmaj - 0.3, z + 0.3), (2.1, Z_TIP), (0, Z_TIP)]   # tip chamfer (STEP: Ø4.2 at the tip)
    hex_ = (cq.Workplane("XY").workplane(offset=Z_HEX).polygon(6, HEX_AF / 0.8660254).extrude(-Z_HEX)
            .rotate((0, 0, 0), (0, 0, 1), 30))           # flats facing ±x (STEP)
    return revolve(pts).union(hex_)


def cap():
    """Touch-proof cap on the pin tip, standing 1.0 beyond the front face (STEP)."""
    return revolve([(0, Z_CAP_END), (R_PIN, Z_CAP_END), (R_PIN - 0.2, Z_CAP + 0.5),
                    (2.4, Z_CAP + 0.25), (2.0, Z_CAP), (0, Z_CAP)])


if __name__ == "__main__":
    parts_common = [(gasket(), GASKET), (terminal(), METAL), (cap(), CAP)]
    body = housing()
    for mpn, color in COLORS.items():
        print("3D model  ", write_model(LIB, f"Amphenol_SurLok-Plus_{mpn}", [(body, color), *parts_common]))
