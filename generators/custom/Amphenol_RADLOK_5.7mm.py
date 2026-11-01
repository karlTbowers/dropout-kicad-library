#!/usr/bin/env python3
"""3D models for Amphenol Technical Products International RADLOK 5.7 mm parts (120 A, 1000 V):

- RL9057-101-F1 (black), -F1OR (orange), -F1RE (red): feed-through panel receptacle, RADSOK pin in front,
  M6 x 1.0 threaded stud behind, square flange with seal, 4 x M3 screws.
- RL00571-16, -25 (+BK, RE): right-angle cable plug, tubular crimp lug for 16 or 25 mm².
- RL00572-16, -25 (+BK, RE): right-angle cable plug, stamped (open-barrel) crimp lug for 16 or 25 mm².

Usage: ~/.cache/dropout/klt-venv/bin/python generators/custom/Amphenol_RADLOK_5.7mm.py [receptacles] [plugs]

None of these has a footprint (docs/CONTRIBUTING.md "Parts not placed on the PCB"): the feed-through's
M6 stud screws into a Würth REDCUBE 74660016 on the board, and the plugs are cable parts.

No official model is public (searched 2026-11-01: Amphenol's sites, CADENAS/3Dfindit, KiCad and the
trusted libraries; distributor CAD tabs are aggregator models). Sources, archived in dropout-vendor-docs
Amphenol-TPI/RADLOK/:
- Customer drawing "RADLOK Feed Thru Pin To Thread" rev. H (2018-01-11), size 5.7 row: A 25.0 flange,
  B 17.0 screw pitch, C 49.6 overall, D Ø15.2 front body, E Ø14.7 panel hole, F 2.8 key notch, G 18.2
  across the notches, H 10 thread, I 24.2 panel face to stud tip, M6x1.0-6g, P M3, 3 mm max. panel.
- Customer drawing "RADLOK Connector Tubular Lug Version" rev. H (2021-01-19), 5.7 rows: A 18.5 wide,
  B 33.0 front to collar, C 23.8 high, D 9.4 boss, E Ø11.5 boss, F 47.7 overall, G 19.0 barrel,
  D1/D2 Ø5.5/8.5 (16 mm²) and Ø7.2/9.5 (25 mm²).
- Customer drawing "RADLOK Connector Stamped Lug Version" rev. C (2018-02-23), 5.7 row: A 18.5, B 30.0,
  C 21.9, D 9.2, E Ø11.2, F 43.6.
- Customer drawing "RadLok Pin" rev. G (2018-07-09): pin Ø5.7, tip groove, hex.
- Data sheet IDS-67-1: photos (black feed-through housings, red release clip on the plugs).
Estimated (marked ESTIMATE): everything else, from the drawings' views (not to scale, so only their
proportions are used, anchored on the table dimensions) and the data sheet photos.

Frame (all models): z is the RADSOK axis. z = 0 is the feed-through's rear contact face (the metal
shoulder a lug, busbar or REDCUBE seats on); the stud points +z; the feed-through's front face is at
z = -29.1. The plugs are drawn mated on it (boss face on that front face), cable toward +x. Every model is
symmetric about the XZ plane, so KiCad's mirrored model Y needs no correction. On a REDCUBE 74660016
footprint, give the feed-through and its plug the offset z = -2.6 mm (the REDCUBE spigot end), as the
SurLok Plus SLPRATPSx models; rotate a plug about z to aim its cable.
"""
import sys
from dataclasses import dataclass

import cadquery as cq

from fplib import METAL, write_model

LIB = "DropOut_Connector_Amphenol"

BLACK, ORANGE, RED = (0.10, 0.10, 0.10), (0.93, 0.47, 0.05), (0.78, 0.09, 0.09)
SEAL = (0.28, 0.28, 0.30)          # ESTIMATE: flange seal, dark grey
CLIP = (0.80, 0.10, 0.10)          # drawings: "Clip, Red"; data sheet photos: red clip on orange plugs
BRASS = (0.80, 0.62, 0.25)         # RADSOK socket (data sheet photo)

# ---------------------------------------------------------------- feed-through RL9057-101-F1x
Z_TIP = 10.0                       # drawing H: thread length from the contact face
Z_PANEL = Z_TIP - 24.2             # drawing I: -14.2, panel face (seal's back)
Z_PIN_TIP = Z_TIP - 49.6           # drawing C: -39.6
SEAL_T = 1.0                       # ESTIMATE: drawing proportions
FLANGE_T = 3.0                     # ESTIMATE: drawing proportions
Z_SEAL = Z_PANEL - SEAL_T          # -15.2
Z_FLANGE = Z_SEAL - FLANGE_T       # -18.2, flange front face
FLANGE, FLANGE_R = 25.0, 2.0       # drawing A; corner radius ESTIMATE
PITCH_SCREW = 17.0                 # drawing B
HOLE_D = 3.4                       # ESTIMATE: M3 clearance (drawing P: M3)
R_FRONT = 15.2 / 2                 # drawing D
Z_FRONT = -29.1                    # ESTIMATE: front body 10.9 long (drawing proportions; pin 10.5 beyond)
R_RING, RING_T = 8.25, 0.8         # ESTIMATE: drawing front view, ring around the body's base
R_REAR = 6.5                       # ESTIMATE: Ø13.0 rear body, through the Ø14.7 panel hole (drawing E)
KEY_W, KEY_R, KEY_L = 2.6, 8.8, 2.8  # ESTIMATE: keys in the panel hole's notches (drawing F 2.8, G 18.2)
POCKET_D = 1.2                     # ESTIMATE: drawing front view, 8 pockets in the flange face
R_PIN = 5.7 / 2                    # RADSOK size
R_SHOULDER = 5.25                  # ESTIMATE: metal contact shoulder Ø10.5 (drawing side view)
SHOULDER_PROUD = 0.4               # ESTIMATE
HEX_AF, HEX_T = 10.0, 2.0          # pin drawing S 10 (hex in the front face, drawing front view); depth ESTIMATE
GROOVE_Z, GROOVE_W, GROOVE_D = 2.6, 0.8, 0.45  # ESTIMATE: pin drawing, latch groove behind the tip
M6_MAJOR, M6_MINOR, M6_PITCH = 6.0, 4.92, 1.0  # ISO M6 coarse
R_RELIEF, RELIEF_L = 2.4, 1.0      # ESTIMATE: thread relief


def revolve(points):
    """Solid of revolution about the global z axis from (r, z) points."""
    return cq.Workplane("XZ").polyline(points).close().revolve(360, (0, 0, 0), (0, 1, 0))


def square_plate(z0, t, hole_r):
    holes = [(sx * PITCH_SCREW / 2, sy * PITCH_SCREW / 2) for sx in (-1, 1) for sy in (-1, 1)]
    return (cq.Workplane("XY").workplane(offset=z0).rect(FLANGE, FLANGE).extrude(t)
            .edges("|Z").fillet(FLANGE_R)
            .faces(">Z").workplane().pushPoints(holes).hole(HOLE_D)
            .faces(">Z").workplane().hole(2 * hole_r))


def ft_housing():
    body = revolve([(R_SHOULDER + 0.05, -SHOULDER_PROUD), (R_REAR - 0.6, -SHOULDER_PROUD),
                    (R_REAR, -SHOULDER_PROUD - 0.6), (R_REAR, Z_FLANGE), (R_RING, Z_FLANGE),
                    (R_RING, Z_FLANGE - RING_T), (R_FRONT, Z_FLANGE - RING_T), (R_FRONT, Z_FRONT + 0.5),
                    (R_FRONT - 0.5, Z_FRONT), (R_PIN, Z_FRONT), (R_PIN, -1.0), (R_SHOULDER + 0.05, -1.0)])
    flange = square_plate(Z_FLANGE, FLANGE_T, R_REAR)
    # Eight pockets in the flange's front face, two per side, clipped by the ring (drawing front view).
    pockets = cq.Workplane("XY")
    for a, b in ((3.5, 8.5), (-3.5, 8.5), (3.5, -8.5), (-3.5, -8.5)):
        pockets = pockets.union(cq.Workplane("XY").workplane(offset=Z_FLANGE - 0.1)
                                .center(a, b).rect(5.0, 3.8).extrude(POCKET_D + 0.1).edges("|Z").fillet(0.6))
        pockets = pockets.union(cq.Workplane("XY").workplane(offset=Z_FLANGE - 0.1)
                                .center(b, a).rect(3.8, 5.0).extrude(POCKET_D + 0.1).edges("|Z").fillet(0.6))
    pockets = pockets.cut(cq.Workplane("XY").workplane(offset=Z_FLANGE - 1).circle(R_RING + 0.6).extrude(5))
    flange = flange.cut(pockets)
    keys = cq.Workplane("XY")
    for side in (1, -1):
        keys = keys.union(cq.Workplane("XY").workplane(offset=Z_PANEL)
                          .center(0, side * (R_REAR + KEY_R - 0.5) / 2)
                          .rect(KEY_W, KEY_R - R_REAR + 0.5).extrude(KEY_L))
    h = body.union(flange).union(keys)
    hex_pocket = (cq.Workplane("XY").workplane(offset=Z_FRONT - 0.1)
                  .polygon(6, HEX_AF / 0.8660254).extrude(HEX_T + 0.1))
    return h.cut(hex_pocket)


def thread_profile(z0, z_tip):
    """(r, z) points: 60° grooves at the M6 pitch from z0 to a chamfered tip at z_tip."""
    rmaj, rmin = M6_MAJOR / 2, M6_MINOR / 2
    flank = (rmaj - rmin) * 0.5774
    pts, z = [], z0
    while z + M6_PITCH <= z_tip - 0.6 + 1e-9:
        pts += [(rmin, z), (rmaj, z + flank), (rmaj, z + M6_PITCH - flank - 0.125), (rmin, z + M6_PITCH - 0.125)]
        z += M6_PITCH
    return pts + [(rmin, z), (rmaj - 0.3, z + 0.3), (rmin, z_tip), (0, z_tip)]


def ft_pin():
    """RADSOK pin, contact shoulder and M6 stud as one silver-plated part; hex in the front face."""
    t = Z_PIN_TIP
    pts = [(0, t), (R_PIN - 0.6, t), (R_PIN, t + 0.6), (R_PIN, t + GROOVE_Z),
           (R_PIN - GROOVE_D, t + GROOVE_Z), (R_PIN - GROOVE_D, t + GROOVE_Z + GROOVE_W),
           (R_PIN, t + GROOVE_Z + GROOVE_W), (R_PIN, -1.0), (R_SHOULDER, -1.0), (R_SHOULDER, 0),
           (R_RELIEF, 0), (R_RELIEF, RELIEF_L)] + thread_profile(RELIEF_L, Z_TIP)
    pin = revolve(pts)
    hex_ = cq.Workplane("XY").workplane(offset=Z_FRONT).polygon(6, HEX_AF / 0.8660254).extrude(HEX_T)
    return pin.union(hex_.cut(cq.Workplane("XY").workplane(offset=Z_FRONT - 1).circle(R_PIN).extrude(HEX_T + 2)))


def ft_seal():
    return square_plate(Z_SEAL, SEAL_T, R_REAR)


# ---------------------------------------------------------------- plugs RL00571 / RL00572
@dataclass
class Plug:
    A: float                       # drawing: width
    B: float                       # drawing: front end to the collar's back
    C: float                       # drawing: height, boss face to top
    D: float                       # drawing: boss length
    E: float                       # drawing: boss diameter
    F: float                       # drawing: overall length
    t_mid: float                   # ESTIMATE: top of the lower body (drawing side view)
    x_low: float                   # ESTIMATE: end of the lower body (from the axis)
    collar_t: float                # ESTIMATE: collar thickness
    neck_top: float                # ESTIMATE: drawing side view, top of the transition where it leaves the body
    neck: tuple                    # ESTIMATE: (half width, t0, t1) where the transition meets the collar
    collar: tuple                  # ESTIMATE: (half width, t0, t1)
    x_cap: float                   # ESTIMATE: end of the ribbed cap's flat top
    slope_end: float               # ESTIMATE: where the cap's back slopes down to t_mid
    ribs: int                      # drawing side view: grip slots per side


TUBULAR = Plug(A=18.5, B=33.0, C=23.8, D=9.4, E=11.5, F=47.7, t_mid=17.6, x_low=17.15, collar_t=2.0,
               neck_top=23.8, neck=(7.0, 11.0, 22.2), collar=(9.7, 8.6, 23.8), x_cap=13.0, slope_end=17.15, ribs=11)
STAMPED = Plug(A=18.5, B=30.0, C=21.9, D=9.2, E=11.2, F=43.6, t_mid=16.3, x_low=17.6, collar_t=1.6,
               neck_top=16.3, neck=(8.6, 9.8, 15.7), collar=(9.25, 9.4, 16.3), x_cap=12.5, slope_end=15.0, ribs=10)
TUBE = {"16": (5.5 / 2, 8.5 / 2), "25": (7.2 / 2, 9.5 / 2)}   # tubular drawing D1, D2
R_BORE = 3.7                       # ESTIMATE: boss bore around the RADSOK socket
R_SOCK_IN, R_SOCK_OUT = 2.95, 3.65  # ESTIMATE: RADSOK socket for the Ø5.7 pin


def box(x0, x1, y, t0, t1):
    return cq.Workplane("XY").workplane(offset=t0).center((x0 + x1) / 2, 0).rect(x1 - x0, 2 * y).extrude(t1 - t0)


def plug_housing(p):
    x0 = -p.A / 2                  # ESTIMATE: socket axis A/2 behind the rounded front end
    x_col0 = x0 + p.B - p.collar_t
    lower = (box(x0, p.x_low, p.A / 2, p.D, p.t_mid).edges("|Z and <X").fillet(4.5)
             .edges("|Z and >X").fillet(1.0).faces("<Z").edges().fillet(0.5))
    ycap = p.A / 2 - 0.6           # ESTIMATE: cap inset from the sides (drawing views)
    cap = (box(x0 + 0.3, p.slope_end, ycap, p.t_mid - 0.5, p.C).edges("|Z and <X").fillet(4.2)
           .faces(">Z").edges().fillet(0.8))
    slope = (cq.Workplane("XZ", origin=(0, p.A, 0))
             .polyline([(p.x_cap, p.C + 1), (p.slope_end + 1, p.C + 1), (p.slope_end + 1, p.t_mid),
                        (p.slope_end, p.t_mid), (p.x_cap, p.C)]).close().extrude(2 * p.A))
    cap = cap.cut(slope)
    yn, n0, n1 = p.neck
    neck = (cq.Workplane("YZ").workplane(offset=p.x_low - 0.2).center(0, (p.D + p.neck_top) / 2)
            .rect(p.A, p.neck_top - p.D).workplane(offset=x_col0 - p.x_low + 0.2)
            .center(0, (n0 + n1) / 2 - (p.D + p.neck_top) / 2).rect(2 * yn, n1 - n0).loft())
    yc, c0, c1 = p.collar
    collar = (box(x_col0, x0 + p.B, yc, c0, c1).edges("|X").fillet(1.2).edges("|Y or |Z").fillet(0.4))
    boss = (cq.Workplane("XY").circle(p.E / 2).extrude(p.D + 0.5).faces("<Z").edges().chamfer(0.4))
    h = lower.union(cap).union(neck).union(collar).union(boss)
    # Grip slots on both sides of the cap (drawing side view), rounded ends.
    xs = [x0 + 2.8 + i * (p.x_cap - 2.0 - x0 - 2.8) / (p.ribs - 1) for i in range(p.ribs)]
    hs = p.C - p.t_mid - 1.6
    for side in (1, -1):
        for x in xs:
            h = h.cut(cq.Workplane("XZ", origin=(0, side * ycap, 0)).center(x, (p.C + p.t_mid) / 2)
                      .slot2D(hs, 0.8, 90).extrude(side * 0.5))
    # Release clip pocket in the front (the red clip sits in it), latch windows and label recess on top.
    h = h.cut(box(x0 - 1, x0 + 2.5, 4.5, p.t_mid - 2.5, p.C - 1.2))
    for side in (1, -1):
        h = h.cut(box(x0 + 1.2, x0 + 3.6, 1.5, p.C - 1.0, p.C + 1).translate((0, side * 4.7, 0)))
    h = h.cut(box(x0 + 5.5, p.x_cap - 4.5, ycap - 2.0, p.C - 0.15, p.C + 1))
    # Bore for the RADSOK socket.
    return h.cut(cq.Workplane("XY").workplane(offset=-1).circle(R_BORE).extrude(p.C - 2.0))


def plug_clip(p):
    x0 = -p.A / 2
    return box(x0 + 0.3, x0 + 2.5, 4.4, p.t_mid - 2.4, p.C - 1.3).edges("|X").fillet(0.5)


def plug_socket(p):
    """RADSOK socket: brass sleeve with the louvre band drawn as two grooves."""
    s = revolve([(R_SOCK_IN + 0.3, 0.8), (R_SOCK_OUT, 0.8), (R_SOCK_OUT, p.C - 3.0),
                 (R_SOCK_IN, p.C - 3.0), (R_SOCK_IN, 1.1)])
    for t in (2.5, p.C - 7.0):
        s = s.cut(revolve([(R_SOCK_IN - 0.1, t), (R_SOCK_IN + 0.25, t), (R_SOCK_IN + 0.25, t + 0.6),
                           (R_SOCK_IN - 0.1, t + 0.6)]))
    return s


def tubular_lug(p, cable):
    """Tubular crimp barrel along +x at mid height, with an inspection hole on top."""
    r_in, r_out = TUBE[cable]
    tb = (p.D + p.C) / 2           # ESTIMATE: barrel centred on the housing height (section X-X)
    x0 = -p.A / 2
    x_end, x_start = x0 + p.F, x0 + p.F - 19.0   # drawing F; G 19.0 barrel length
    tube = (cq.Workplane("YZ").workplane(offset=x_start).center(0, tb).circle(r_out).circle(r_in)
            .extrude(x_end - x_start).faces(">X").edges().chamfer(0.3))
    hole = cq.Workplane("XY").workplane(offset=tb).center(x0 + p.B + 3.0, 0).circle(0.75).extrude(r_out + 1)
    return tube.cut(hole)


def stamped_lug(p):
    """Open-barrel crimp lug: tongue from the collar, base with serrations, two wings standing up."""
    x0 = -p.A / 2
    xc, x_end = x0 + p.B, x0 + p.F
    xw = xc + 1.7                  # ESTIMATE: wings start (drawing side view)
    tb0, tb1 = 11.8, 12.8          # ESTIMATE: drawing side view, base sheet
    t_top = 26.6                   # ESTIMATE: drawing side view, open wings above the housing
    lug = box(xc - 3.0, x_end, 5.0, tb0, tb1)
    for x in (xw + 2.5, xw + 4.0, xw + 5.5):
        lug = lug.cut(box(x - 0.2, x + 0.2, 4.2, tb1 - 0.2, tb1 + 0.1))
    for side in (1, -1):
        wing = (cq.Workplane("XZ", origin=(0, side * 6.0 if side > 0 else -5.0, 0))
                .polyline([(xc + 0.2, tb1), (x_end, tb1), (x_end, t_top - 1.2), (x_end - 1.2, t_top),
                           (xw + 1.2, t_top), (xw, t_top - 1.2), (xw, tb1 + 2.2)]).close().extrude(1.0))
        lug = lug.union(wing)
    return lug


def place(w):
    """Plug frame (t up from the boss face, cable +x) -> feed-through frame, mated."""
    return w.rotate((0, 0, 0), (1, 0, 0), 180).translate((0, 0, Z_FRONT))


def receptacles():
    ft = [(ft_seal(), SEAL), (ft_pin(), METAL)]
    housing = ft_housing()
    for mpn, color in {"RL9057-101-F1": BLACK, "RL9057-101-F1OR": ORANGE, "RL9057-101-F1RE": RED}.items():
        print("3D model  ", write_model(LIB, f"Amphenol_RADLOK_{mpn}", [(housing, color), *ft]))


def plugs():
    colours = {"": ORANGE, "BK": BLACK, "RE": RED}            # data sheet: blank orange, BK, RE
    for series, p in (("RL00571", TUBULAR), ("RL00572", STAMPED)):
        body = place(plug_housing(p))
        common = [(place(plug_clip(p)), CLIP), (place(plug_socket(p)), BRASS)]
        for cable in ("16", "25"):
            lug = place(tubular_lug(p, cable) if series == "RL00571" else stamped_lug(p))
            for suffix, color in colours.items():
                mpn = f"{series}-{cable}{suffix}"
                print("3D model  ", write_model(LIB, f"Amphenol_RADLOK_{mpn}",
                                                [(body, color), *common, (lug, METAL)]))


if __name__ == "__main__":
    which = sys.argv[1:] or ["receptacles", "plugs"]
    for name in which:
        {"receptacles": receptacles, "plugs": plugs}[name]()
