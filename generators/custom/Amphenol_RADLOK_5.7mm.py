#!/usr/bin/env python3
"""3D models for Amphenol RADLOK 5.7 mm parts (120 A, 1000 V; made by Amphenol Technical Products International,
sold by Amphenol Tuchel Industrial):

- RL9057-101-F1 (black), -F1OR (orange), -F1RE (red): feed-through panel receptacle, RADSOK pin in front,
  M6 x 1.0 threaded stud behind, square flange with seal, 4 x M4 screws.
- RL00571-16, -25 (+BK, RE): right-angle cable plug, tubular crimp lug for 16 or 25 mm².
- RL00572-16, -25 (+BK, RE): right-angle cable plug, stamped (open-barrel) crimp lug for 16 or 25 mm².

Usage: ~/.cache/dropout/klt-venv/bin/python generators/custom/Amphenol_RADLOK_5.7mm.py [receptacles] [plugs]

None of these has a footprint (docs/CONTRIBUTING.md "Parts not placed on the PCB"): the feed-through's
M6 stud screws into a Würth REDCUBE 74660016 on the board, and the plugs are cable parts.

Sources, archived in dropout-vendor-docs Amphenol-TPI/RADLOK/:
- Amphenol Tuchel's customer STEPs c3d-rl9057-101-f1bk-01-000.stp (feed-through) and c3d-rl00571-25or-01-000.stp
  (tubular plug), from amphenol-industrial.de: single uncoloured solids with no licence stated, so they are
  measured only and not redistributed (as the SurLok Plus SLPPA25BSx plug's STEP). Everything marked "STEP"
  below was measured on them. There is none for the stamped plug.
- Customer drawing "RADLOK Feed Thru Pin To Thread" rev. K (2022-04-25; 5.7 mm row as rev. H): A 25.0 flange,
  B 17.0 screw pitch, C 49.6 overall, D Ø15.2 front tube, E Ø14.7 panel hole, F 2.8 key notch, G 18.2 across
  the notches, H 10 thread, I 24.2 panel face to stud tip, M6x1.0-6g, P M4 (M3 is the 3.6 mm size only),
  3 mm max. panel.
- Customer drawing "RADLOK Connector Tubular Lug Version" rev. L (2024-02-20), 5.7 rows: A 18.5 wide,
  B 33.0 front to collar, C 23.8 high, D 9.4 boss, E Ø11.5 boss, F 47.7 overall, G 19.0 barrel,
  D1/D2 Ø5.5/8.5 (16 mm²) and Ø7.2/9.5 (25 mm²).
- Customer drawing "RADLOK Connector Stamped Lug Version" rev. C (2018-02-23), 5.7 row: A 18.5, B 30.0,
  C 21.9, D 9.2, E Ø11.2, F 43.6.
- Amphenol Tuchel's PowerLok/RADLOK/HC32 catalogue (2020) and data sheet IDS-67-1: the same tables, photos
  (black feed-through housings, red release clip on the plugs).
Estimated (marked ESTIMATE): what neither the drawings nor the STEPs give, e.g. the split between seal and
flange, gusset and pocket sizes, the stamped plug's lug.

Frame (all models): z is the RADSOK axis. z = 0 is the feed-through's rear seating face (what a lug, busbar
or REDCUBE seats on); the stud points +z; the feed-through's front tube ends at z = -27.6. The plugs are drawn
mated: boss fully in the tube, housing on the tube's front face, cable toward +x. Every model is symmetric
about the XZ plane, so KiCad's mirrored model Y needs no correction. On a REDCUBE 74660016 footprint, give
the feed-through and its plug the offset z = -2.6 mm (the REDCUBE spigot end), as the SurLok Plus SLPRATPSx
models; rotate a plug about z to aim its cable.
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
Z_TIP = 10.0                       # drawing H, STEP: stud tip
Z_PIN_TIP = Z_TIP - 49.6           # drawing C, STEP: -39.6
M6_MAJOR, M6_MINOR, M6_PITCH = 6.0, 4.92, 1.0  # ISO M6 coarse
R_RELIEF, RELIEF_L = 2.35, 1.0     # STEP: Ø4.7 relief between the seat and the thread
R_SEAT = 4.7                       # STEP: Ø9.4 seating face at z = 0
R_METAL = 4.0                      # ESTIMATE: the pin's metal shoulder showing in the seating face
Z_CONE = -1.6                      # STEP: cone from the seat out to the rear body
R_REAR = 7.0                       # STEP: Ø14.0 rear body, through the Ø14.7 panel hole (drawing E)
Z_KEY = -10.85                     # STEP: keys from here to the seal, along ±x
KEY_W, KEY_R = 2.6, 8.7            # STEP: radial reach; width ESTIMATE (drawing F 2.8 notch)
Z_SEAL = -13.35                    # STEP: seal's panel face (drawing I gives -14.2)
SEAL_T = 1.0                       # ESTIMATE: STEP shows one 4.5 thick stack for seal and flange
Z_FLANGE = -17.85                  # STEP: flange front face
FLANGE, FLANGE_R = 25.0, 2.0       # drawing A, STEP 24.8-25.0; corner radius ESTIMATE
PITCH_SCREW = 17.0                 # drawing B
HOLE_D = 4.3                       # STEP: Ø4.3 (drawing P: M4)
POCKET_D = 1.1                     # STEP: section area drop over the last 1.1 of the flange
R_TUBE, R_BORE_FT = 7.5, 6.15      # STEP: Ø15.0 front tube (drawing D 15.2), Ø12.3 bore for the plug's boss
Z_TUBE_END = -27.6                 # STEP: front face of the tube
Z_FLOOR = -18.0                    # STEP: bore floor (9.6 deep; the plug's boss is 9.4)
R_GUSSET0, Z_GUSSET1 = 11.4, -22.1  # STEP: four gussets along ±x/±y, flange r 11.4 down to the tube at -22.1
GUSSET_T = 1.6                     # ESTIMATE: STEP diagonal rays miss them
HEX_AF, HEX_T = 7.8, 0.6           # STEP: pin hex at the bore floor (7.8 across flats, 9.4 across corners)
R_PIN = 2.85                       # STEP, RADSOK size 5.7
GROOVE = (-36.6, -37.85, 2.2)      # STEP: latch groove (z from, z to, radius)
TIP = (-39.1, 2.7, 1.8)            # STEP: tip chamfer (z where it starts, r there, r at the tip)
Z_MATE = Z_TUBE_END + 9.4          # plug boss face when mated: housing on the tube's front face (drawing D 9.4)


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
    seal_front = Z_SEAL - SEAL_T
    body = revolve([(R_METAL, 0), (R_SEAT, 0), (R_REAR - 0.1, Z_CONE), (R_REAR, Z_CONE - 0.1),
                    (R_REAR, seal_front), (R_TUBE, seal_front), (R_TUBE, Z_TUBE_END + 0.3),
                    (R_TUBE - 0.3, Z_TUBE_END), (R_BORE_FT + 0.3, Z_TUBE_END), (R_BORE_FT, Z_TUBE_END + 0.3),
                    (R_BORE_FT, Z_FLOOR), (R_PIN, Z_FLOOR), (R_PIN, -0.6), (R_METAL, -0.6)])
    flange = square_plate(Z_FLANGE, seal_front - Z_FLANGE, R_REAR)
    # Eight pockets in the flange's front face, two per side, clipped by a ring round the tube (drawing
    # front view; depth from the STEP).
    pockets = cq.Workplane("XY")
    for a, b in ((3.5, 8.5), (-3.5, 8.5), (3.5, -8.5), (-3.5, -8.5)):
        for cx, cy, w, h in ((a, b, 5.0, 3.6), (b, a, 3.6, 5.0)):
            pockets = pockets.union(cq.Workplane("XY").workplane(offset=Z_FLANGE - 0.1)
                                    .center(cx, cy).rect(w, h).extrude(POCKET_D + 0.1).edges("|Z").fillet(0.6))
    pockets = pockets.cut(cq.Workplane("XY").workplane(offset=Z_FLANGE - 1).circle(R_TUBE + 1.4).extrude(5))
    flange = flange.cut(pockets)
    # Four gussets from the flange face down to the tube, along ±x and ±y (STEP).
    gussets = cq.Workplane("XY")
    for ang in (0, 90, 180, 270):
        g = (cq.Workplane("XZ", origin=(0, GUSSET_T / 2, 0))
             .polyline([(R_TUBE - 0.5, Z_FLANGE + 0.1), (R_GUSSET0, Z_FLANGE + 0.1), (R_GUSSET0, Z_FLANGE),
                        (R_TUBE, Z_GUSSET1), (R_TUBE - 0.5, Z_GUSSET1)]).close().extrude(GUSSET_T))
        gussets = gussets.union(g.rotate((0, 0, 0), (0, 0, 1), ang))
    keys = cq.Workplane("XY")
    for side in (1, -1):
        keys = keys.union(cq.Workplane("XY").workplane(offset=Z_SEAL)
                          .center(side * (R_REAR + KEY_R - 0.5) / 2, 0)
                          .rect(KEY_R - R_REAR + 0.5, KEY_W).extrude(Z_KEY - Z_SEAL))
    return body.union(flange).union(gussets).union(keys)


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
    """RADSOK pin, seating shoulder and M6 stud as one silver-plated part; hex at the bore floor."""
    g0, g1, rg = GROOVE
    zt, r_t, r_tip = TIP
    pts = [(0, Z_PIN_TIP), (r_tip, Z_PIN_TIP), (r_t, zt), (R_PIN, zt + 0.3), (R_PIN, g1), (rg, g1), (rg, g0),
           (R_PIN, g0), (R_PIN, -0.6), (R_METAL, -0.6), (R_METAL, 0), (R_RELIEF, 0),
           (R_RELIEF, RELIEF_L)] + thread_profile(RELIEF_L, Z_TIP)
    pin = revolve(pts)
    hex_ = cq.Workplane("XY").workplane(offset=Z_FLOOR - HEX_T).polygon(6, HEX_AF / 0.8660254).extrude(HEX_T)
    return pin.union(hex_)


def ft_seal():
    return square_plate(Z_SEAL - SEAL_T, SEAL_T, R_REAR)


# ---------------------------------------------------------------- plugs RL00571 / RL00572
@dataclass
class Plug:
    A: float                       # drawing: width
    B: float                       # drawing: front end to the collar's back
    C: float                       # drawing: overall height, boss face to the top
    D: float                       # drawing: boss length
    E: float                       # drawing: boss diameter
    F: float                       # drawing: overall length
    x_front: float                 # front end, from the socket axis
    t_top: float                   # top of the housing (the tubular collar stands higher)
    t_mid: float                   # seam between the lower body and the ribbed cap
    x_body: float                  # end of the straight body, from the socket axis
    trans: tuple                   # (half width, t0, t1) where the transition meets the collar
    collar_t: float                # collar thickness
    collar: tuple                  # (half width, t0, t1)
    x_cap: float                   # end of the ribbed region
    slope: tuple                   # stamped only: (x where the cap starts down, x where it reaches t_mid)
    t_lug: float                   # tubular: barrel axis height; stamped: base sheet bottom
    ribs: int                      # drawing side view: grip slots per side


# Tubular: measured on Amphenol Tuchel's customer STEP c3d-rl00571-25or-01-000.stp (no licence stated, not
# redistributed): socket axis 10.45 behind the front end, front corners r 4.6 in plan, housing to t 21.9 with
# a seam at t 16.1 and the cap 0.55 narrower, straight to 12.0 behind the axis, then flaring down to t 7.6 and
# up to 22.8 while narrowing to 15.4 wide; collar 1.25 thick, 17.3 wide, t 6.6-23.85 (C); barrel axis t 15.25.
TUBULAR = Plug(A=18.5, B=33.0, C=23.85, D=9.4, E=11.5, F=47.7, x_front=-10.45, t_top=21.9, t_mid=16.1,
               x_body=12.0, trans=(7.7, 7.6, 22.8), collar_t=1.25, collar=(8.65, 6.6, 23.85), x_cap=11.5,
               slope=None, t_lug=15.25, ribs=11)
# Stamped: no customer STEP. The drawing's C 21.9 equals the tubular housing's top, so the housing is taken as
# the tubular one (ESTIMATE); the cap sloping down to a low collar rim and the lug are ESTIMATES from the
# drawing's side view.
STAMPED = Plug(A=18.5, B=30.0, C=21.9, D=9.2, E=11.2, F=43.6, x_front=-10.45, t_top=21.9, t_mid=16.1,
               x_body=17.0, trans=(8.6, 9.8, 15.7), collar_t=1.6, collar=(9.25, 9.2, 16.1), x_cap=11.5,
               slope=(11.5, 14.5), t_lug=11.8, ribs=10)
TUBE = {"16": (5.5 / 2, 8.5 / 2), "25": (7.2 / 2, 9.5 / 2)}   # tubular drawing D1, D2
R_BORE = 3.7                       # ESTIMATE: boss bore around the RADSOK socket
R_SOCK_IN, R_SOCK_OUT = 2.95, 3.65  # ESTIMATE: RADSOK socket for the Ø5.7 pin
CAP_INSET, CAP_ROUND = 0.55, 1.5   # STEP: cap 17.4 wide, 15.3 at the very top


def box(x0, x1, y, t0, t1):
    return cq.Workplane("XY").workplane(offset=t0).center((x0 + x1) / 2, 0).rect(x1 - x0, 2 * y).extrude(t1 - t0)


def plug_housing(p):
    x0 = p.x_front
    x_col0 = x0 + p.B - p.collar_t
    lower = (box(x0, p.x_body, p.A / 2, p.D, p.t_mid + 0.01).edges("|Z and <X").fillet(4.6)
             .faces("<Z").edges().fillet(0.5))
    ycap = p.A / 2 - CAP_INSET
    x_cap_end = p.slope[1] if p.slope else p.x_body
    cap = (box(x0 + CAP_INSET, x_cap_end, ycap, p.t_mid, p.t_top).edges("|Z and <X").fillet(4.6 - CAP_INSET)
           .faces(">Z").edges().fillet(CAP_ROUND))
    if p.slope:                    # stamped: the cap's back runs down to the lower body (drawing side view)
        cap = cap.cut(cq.Workplane("XZ", origin=(0, p.A, 0))
                      .polyline([(p.slope[0], p.t_top + 1), (p.slope[1] + 1, p.t_top + 1), (p.slope[1] + 1, p.t_mid),
                                 (p.slope[1], p.t_mid), (p.slope[0], p.t_top)]).close().extrude(2 * p.A))
    t_start = p.t_mid if p.slope else p.t_top
    yn, n0, n1 = p.trans
    trans = (cq.Workplane("YZ").workplane(offset=p.x_body - 0.2).center(0, (p.D + t_start) / 2)
             .rect(p.A, t_start - p.D).workplane(offset=x_col0 - p.x_body + 0.2)
             .center(0, (n0 + n1) / 2 - (p.D + t_start) / 2).rect(2 * yn, n1 - n0).loft())
    yc, c0, c1 = p.collar
    collar = box(x_col0, x0 + p.B, yc, c0, c1).edges("|X").fillet(3.5 if not p.slope else 1.2)
    boss = cq.Workplane("XY").circle(p.E / 2).extrude(p.D + 0.5).faces("<Z").edges().chamfer(0.4)
    h = lower.union(cap).union(trans).union(collar).union(boss)
    # Seam groove between the lower body and the cap (STEP: section dip at t 16.1).
    for side in (1, -1):
        h = h.cut(box(x0 + 4.6, p.x_body - 0.5, 0.3, p.t_mid - 0.2, p.t_mid + 0.2).translate((0, side * (p.A / 2 - 0.15), 0)))
    # Grip slots on both sides of the cap (drawing side view), rounded ends.
    xs = [x0 + 3.2 + i * (p.x_cap - 1.5 - x0 - 3.2) / (p.ribs - 1) for i in range(p.ribs)]
    hs = p.t_top - p.t_mid - 2.2
    for side in (1, -1):
        for x in xs:
            h = h.cut(cq.Workplane("XZ", origin=(0, side * ycap, 0)).center(x, (p.t_top + p.t_mid) / 2 - 0.3)
                      .slot2D(hs, 0.8, 90).extrude(side * 0.5))
    # Release clip pocket in the front (the red clip sits in it), latch windows and label recess on top.
    h = h.cut(box(x0 - 1, x0 + 2.5, 4.5, p.t_mid - 2.5, p.t_top - 1.2))
    for side in (1, -1):
        h = h.cut(box(x0 + 1.4, x0 + 3.8, 1.5, p.t_top - 1.0, p.t_top + 1).translate((0, side * 4.7, 0)))
    h = h.cut(box(x0 + 5.5, p.x_cap - 3.0, ycap - 2.5, p.t_top - 0.15, p.t_top + 1))
    # Bore for the RADSOK socket.
    return h.cut(cq.Workplane("XY").workplane(offset=-1).circle(R_BORE).extrude(p.t_top - 0.4 + 1))


def plug_clip(p):
    x0 = p.x_front
    return box(x0 + 0.3, x0 + 2.5, 4.4, p.t_mid - 2.4, p.t_top - 1.3).edges("|X").fillet(0.5)


def plug_socket(p):
    """RADSOK socket: brass sleeve with the louvre band drawn as two grooves."""
    s = revolve([(R_SOCK_IN + 0.3, 0.8), (R_SOCK_OUT, 0.8), (R_SOCK_OUT, p.t_top - 0.6),
                 (R_SOCK_IN, p.t_top - 0.6), (R_SOCK_IN, 1.1)])
    for t in (2.5, p.t_top - 7.0):
        s = s.cut(revolve([(R_SOCK_IN - 0.1, t), (R_SOCK_IN + 0.25, t), (R_SOCK_IN + 0.25, t + 0.6),
                           (R_SOCK_IN - 0.1, t + 0.6)]))
    return s


def tubular_lug(p, cable):
    """Tubular crimp barrel along +x at mid height, with an inspection hole on top."""
    r_in, r_out = TUBE[cable]
    tb = p.t_lug
    x0 = p.x_front
    x_end, x_start = x0 + p.F, x0 + p.F - 19.0   # drawing F; G 19.0 barrel length
    tube = (cq.Workplane("YZ").workplane(offset=x_start).center(0, tb).circle(r_out).circle(r_in)
            .extrude(x_end - x_start).faces(">X").edges().chamfer(0.3))
    hole = cq.Workplane("XY").workplane(offset=tb).center(x0 + p.B + 3.0, 0).circle(0.75).extrude(r_out + 1)
    return tube.cut(hole)


def stamped_lug(p):
    """Open-barrel crimp lug: tongue from the collar, base with serrations, two wings standing up."""
    x0 = p.x_front
    xc, x_end = x0 + p.B, x0 + p.F
    xw = xc + 1.7                  # ESTIMATE: wings start (drawing side view)
    tb0, tb1 = p.t_lug, p.t_lug + 1.0  # ESTIMATE: drawing side view, base sheet
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
    return w.rotate((0, 0, 0), (1, 0, 0), 180).translate((0, 0, Z_MATE))


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
