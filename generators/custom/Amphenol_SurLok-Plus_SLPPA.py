#!/usr/bin/env python3
"""3D models for Amphenol Industrial SurLok Plus 5.7 mm Gen 1.0 (1000 V DC) right-angle plugs, 25 mm²
crimp, with back shell, sealed, no keyway: SLPPA25BSB (black), SLPPA25BSR (red).

Usage: ~/.cache/dropout/klt-venv/bin/python generators/custom/Amphenol_SurLok-Plus_SLPPA.py

These plugs are cable parts: they mate the SLPRATPSx receptacles (generators/custom/
Amphenol_SurLok-Plus_SLPRAT.py) and have no footprint. The model is drawn in the receptacle model's
frame, mated, so the same model offset shows both (see Frame).

Sources (archived in dropout-vendor-docs, Amphenol-Industrial/SurLok-Plus/):
- Customer drawing C10-730186 rev. D, "5.7MM SURLOK PLUS RIGHTANGLE PLUG" (cdr-slppa25bsb-01-000.pdf,
  served for SLPPA25BSB and SLPPA25BSR by Amphenol Tuchel Industrial, amphenol-industrial.de).
  Exact: 22.6 overall height, nose Ø11.3 standing 6.6 below the body, 18 wide, 30 from the head's back
  to the back shell, 55.1 overall length (REF), cable Ø10.8 max for 25 mm².
- Catalog IC-10 p. 7: the same A/B/C/D (22.6, 55.1, 30, 18).
- Amphenol Tuchel's customer STEP (c3d-slppa25bsb-01-000.stp, a hollow single-body envelope, orange for
  every colour, no licence stated): measured only, not redistributed. Measured: head Ø18.0 round on
  the mating axis, skirt bore Ø16.1, top saddle, elbow bottom 2.0 below the skirt, back shell (hex
  flats 16.0 across on a Ø17.5 barrel, Ø16.0 collars, cable bore Ø10.2), side buttons 0.2 proud,
  three back ribs 1.0 proud.
- A GrabCAD community model of SLPPA25BSB (no licence stated; measured only): recess depth, seal and
  socket positions. Its nose is about 1.3 shorter than the drawing; the drawing wins.
Estimated (marked ESTIMATE below): everything not listed as exact or measured. The RADSOK lettering
is not modelled.

Frame: the receptacle model's. z is the mating axis, z = -27.8 is the receptacle's mating face, which
seats on the plug's recess floor when mated; the plug lies at z < -12.6 (its nose tip) and the cable
leaves toward +x. Symmetric about the XZ plane, so KiCad's mirrored model Y needs no correction. To
show the plug mated on a receptacle fitted to a REDCUBE 74660016 footprint, give it the receptacle's
offset (z = -2.6 mm) and rotate it about z to point the cable where it should go.
"""
import cadquery as cq

from fplib import METAL, write_model

LIB = "DropOut_Connector_Amphenol"

COLORS = {                         # catalog p. 7 colour code
    "SLPPA25BSB": (0.10, 0.10, 0.10),  # B black
    "SLPPA25BSR": (0.78, 0.09, 0.09),  # R red
}
SEAL = (0.88, 0.88, 0.86)          # nose seal and cable grommet, light grey as in the photos

# The plug is built in its own frame first: t up from the nose tip, the head on the t axis, the
# back shell along +x, y across. place() turns it into the receptacle's frame.
T_TOP = 22.6                       # drawing: overall height
T_SKIRT = 6.6                      # drawing: nose below the body
R_NOSE = 11.3 / 2                  # drawing
R_HEAD = 9.0                       # STEP: Ø18.0 head (drawing: 18 wide)
R_SKIRT_IN = 8.05                  # STEP: Ø16.1 skirt bore, takes the receptacle's front tube
T_RECESS = T_SKIRT + 8.6           # ESTIMATE: GrabCAD recess floor 8.6 above the skirt; the
                                   # receptacle's mating face seats here
R_NOSE_IN = 3.85                   # STEP: Ø7.7 nose bore
T_SOCKET = 3.4                     # ESTIMATE: GrabCAD socket entry 3.3-3.5 inside the nose tip
T_SOCKET_END = 19.0                # ESTIMATE: GrabCAD socket end
R_SOCKET_IN, R_SOCKET_OUT = 2.95, 3.80   # ESTIMATE: RADSOK 5.7 mm socket around the Ø5.7 pin
SEAL_T0, SEAL_T1 = 2.0, 4.9        # ESTIMATE: drawing, ribbed seal band (3 ribs) at 29.5 px/mm
R_SEAL_ROOT, R_SEAL_RIB = 5.25, 5.85     # STEP: Ø11.62 over the ribs; root ESTIMATE
X_BODY = 20.0                      # drawing: 30 - 10.0 (head back incl. ribs) = 20.0 axis to back shell
HALF_W = 9.0                       # drawing: 18 wide
T_BELLY = 4.6                      # STEP: elbow bottom 2.0 below the skirt
X_BELLY0, X_BELLY1 = 8.3, 13.1     # ESTIMATE: drawing, belly curve from the skirt to the flat
# STEP: the top along the centre line, domed over the head and dipping in a saddle before the back shell.
TOP = [(-R_HEAD - 0.5, 21.7), (-7.5, 22.2), (-5.0, 22.45), (-2.5, 22.58), (0.0, 22.6), (4.0, 22.0),
       (8.0, 21.3), (10.0, 21.1), (12.0, 21.15), (14.0, 21.6), (16.0, 22.2), (18.0, 22.45), (20.0, 22.6)]
CORNER = (3.9, 4.6, 4.7)           # ESTIMATE: drawing and STEP bottom view, facets on the two bottom corners
                                   # at the back-shell end (x, y, t legs)
T_SLEEVE = 13.6                    # STEP: back-shell axis 13.6 above the nose tip
R_COLLAR, R_BARREL, HEX_FLAT = 8.0, 8.75, 8.0   # STEP: Ø16.0 collars, Ø17.5 barrel, flats 16.0 across
X_END = 45.1                       # drawing: 55.1 - 10.0 (head back incl. ribs)
# Back-shell profile (x, r), STEP sections: collar, cone up to the barrel, barrel, cone down, end collar.
SLEEVE = [(X_BODY, R_COLLAR), (X_BODY + 2.0, R_COLLAR), (X_BODY + 4.0, R_BARREL), (X_BODY + 19.0, R_BARREL),
          (X_BODY + 22.0, 8.24), (X_BODY + 24.0, R_COLLAR), (X_END - 0.4, R_COLLAR), (X_END, R_COLLAR - 0.4)]
R_CABLE = 5.1                      # STEP: Ø10.2 cable bore (25 mm² cable Ø10.0-10.4)
X_BORE_END = 30.0                  # ESTIMATE: cable bore depth, crimp barrel inside
R_GROMMET_IN, R_GROMMET_OUT = 4.9, 5.65  # STEP: Ø11.3 grommet lip at the end; ESTIMATE wall
R_BARREL_IN, R_BARREL_OUT = 3.6, 4.4     # ESTIMATE: GrabCAD crimp barrel, 25 mm² conductor Ø~6.5 crimped
KEY_X, KEY_T, KEY_R = 13.8, 10.8, 5.0    # ESTIMATE: drawing, keyhole release button circle
KEY_X0, KEY_W = 2.4, 5.1                 # ESTIMATE: drawing, keyhole tongue end and width
KEY_PROUD = 0.2                          # STEP
RIBS_T = (11.0, 14.05, 16.9)             # ESTIMATE: drawing, back ribs at 29.5 px/mm
RIB_H, RIB_PROUD, RIB_ANGLE = 1.2, 1.0, 50.0   # ESTIMATE: drawing; proud 1.0 from the STEP


def revolve_t(points):
    """Solid of revolution about the t axis (local Z) from (r, t) points."""
    return cq.Workplane("XZ").polyline(points).close().revolve(360, (0, 0, 0), (0, 1, 0))


def revolve_x(points):
    """Solid of revolution about the back-shell axis (parallel to x at t = T_SLEEVE) from (x, r)."""
    pts = [(x, T_SLEEVE + r) for x, r in points]
    return (cq.Workplane("XZ").polyline(pts).close()
            .revolve(360, (0, T_SLEEVE, 0), (1, T_SLEEVE, 0)))


def elbow():
    """The body between the head and the back shell: side profile extruded across the width."""
    prof = (cq.Workplane("XZ", origin=(0, HALF_W, 0))
            .moveTo(0, T_SKIRT)
            .lineTo(X_BELLY0, T_SKIRT)
            .threePointArc(((X_BELLY0 + X_BELLY1) / 2 + 0.6, (T_SKIRT + T_BELLY) / 2 - 0.3),
                           (X_BELLY1, T_BELLY))
            .lineTo(X_BODY, T_BELLY)
            .lineTo(X_BODY, T_TOP + 1.0)
            .lineTo(0, T_TOP + 1.0)
            .close()
            .extrude(2 * HALF_W))
    for side in (1, -1):
        prof = prof.cut(corner(side))
    return prof


def corner(side):
    """Tetrahedron cutting the bottom corner at the back-shell end (x = X_BODY, y = side * HALF_W)."""
    a, b, c = CORNER
    y = side * HALF_W
    tri = [cq.Vector(X_BODY - a, y, T_BELLY), cq.Vector(X_BODY, y - side * b, T_BELLY),
           cq.Vector(X_BODY, y, T_BELLY + c)]
    ctr = sum(tri, cq.Vector()) * (1 / 3)
    tri = [ctr + (v - ctr) * 1.5 for v in tri]          # grown in its own plane, so the cut is clean
    apex = cq.Vector(X_BODY + 2, y + side * 2, T_BELLY - 2)
    faces = [cq.Face.makeFromWires(cq.Wire.makePolygon(f, close=True))
             for f in ([tri[0], tri[1], tri[2]], [apex, tri[0], tri[1]], [apex, tri[1], tri[2]], [apex, tri[2], tri[0]])]
    return cq.Workplane().add(cq.Solid.makeSolid(cq.Shell.makeShell(faces)).fix())


def top_cut():
    """Everything above the top line, across the full width."""
    return (cq.Workplane("XZ", origin=(0, HALF_W + 2, 0))
            .moveTo(TOP[0][0], TOP[0][1])
            .spline(TOP[1:], includeCurrent=True)
            .lineTo(X_BODY + 1, TOP[-1][1])
            .lineTo(X_BODY + 1, T_TOP + 5)
            .lineTo(TOP[0][0], T_TOP + 5)
            .close()
            .extrude(2 * HALF_W + 4))


def head():
    h = cq.Workplane("XY").workplane(offset=T_SKIRT).circle(R_HEAD).extrude(T_TOP + 1.0 - T_SKIRT)
    # Back ribs: circumferential arcs around the head's back (-x), RIB_ANGLE either side.
    for t in RIBS_T:
        rib = (cq.Workplane("XY").workplane(offset=t - RIB_H / 2)
               .circle(R_HEAD + RIB_PROUD).circle(R_HEAD - 0.5).extrude(RIB_H)
               .edges().fillet(0.3))
        wedge = (cq.Workplane("XY").workplane(offset=t - RIB_H)
                 .polyline([(0, 0), (-20, -20 * 1.1918), (-20, 20 * 1.1918)]).close()  # tan 50°
                 .extrude(2 * RIB_H))
        h = h.union(rib.intersect(wedge))
    return h


def keyhole(side):
    """Release button, KEY_PROUD proud of the side face at y = side * HALF_W."""
    y0 = side * HALF_W
    sk = (cq.Workplane("XZ", origin=(0, y0, 0))
          .center(KEY_X, KEY_T).circle(KEY_R).extrude(-side * KEY_PROUD))
    tongue = (cq.Workplane("XZ", origin=(0, y0, 0))
              .center((KEY_X0 + KEY_X) / 2, KEY_T).rect(KEY_X - KEY_X0, KEY_W).extrude(-side * KEY_PROUD)
              .edges("|Y").fillet(0.5))
    return sk.union(tongue)


def sleeve():
    s = revolve_x([(X_BODY - 0.5, 0)] + SLEEVE + [(X_END, 0)])
    hex_ = (cq.Workplane("YZ", origin=(X_BODY - 1.0, 0, T_SLEEVE))
            .polygon(6, 2 * HEX_FLAT / 0.8660254).extrude(X_END - X_BODY + 2.0))  # flats on top and bottom
    s = s.intersect(hex_)
    bore = revolve_x([(X_BORE_END, 0), (X_BORE_END, R_CABLE), (X_END + 1, R_CABLE), (X_END + 1, 0)])
    return s.cut(bore)


def housing():
    h = head().union(elbow()).cut(top_cut()).union(sleeve())
    h = h.union(keyhole(1)).union(keyhole(-1))
    h = h.cut(revolve_t([(R_NOSE_IN, T_SKIRT - 0.1), (R_SKIRT_IN, T_SKIRT - 0.1),
                         (R_SKIRT_IN, T_RECESS), (R_NOSE_IN, T_RECESS)]))
    nose = revolve_t([(R_NOSE_IN, 0), (R_NOSE - 0.3, 0), (R_NOSE, 0.3), (R_NOSE, SEAL_T0),
                      (R_SEAL_ROOT, SEAL_T0), (R_SEAL_ROOT, SEAL_T1), (R_NOSE, SEAL_T1),
                      (R_NOSE, T_RECESS), (R_NOSE_IN, T_RECESS)])
    h = h.union(nose)
    return h.cut(revolve_t([(0, -1), (R_NOSE_IN, -1), (R_NOSE_IN, T_SOCKET_END), (0, T_SOCKET_END)]))


def seal():
    """Ribbed nose seal: three ribs over the seal band."""
    pitch = (SEAL_T1 - SEAL_T0) / 3
    pts = [(R_SEAL_ROOT, SEAL_T0), (R_NOSE, SEAL_T0)]
    for i in range(3):
        t = SEAL_T0 + i * pitch
        pts += [(R_SEAL_RIB, t + pitch / 2), (R_NOSE, t + pitch)]
    pts += [(R_SEAL_ROOT, SEAL_T1)]
    return revolve_t(pts)


def socket():
    """RADSOK socket: a sleeve with the hyperbolic louvre band drawn as two grooves."""
    s = revolve_t([(R_SOCKET_IN + 0.3, T_SOCKET), (R_SOCKET_OUT, T_SOCKET), (R_SOCKET_OUT, T_SOCKET_END),
                   (R_SOCKET_IN, T_SOCKET_END), (R_SOCKET_IN, T_SOCKET + 0.3)])
    for t in (T_SOCKET + 1.5, T_SOCKET_END - 4.0):
        s = s.cut(revolve_t([(R_SOCKET_IN - 0.1, t), (R_SOCKET_IN + 0.25, t),
                             (R_SOCKET_IN + 0.25, t + 0.6), (R_SOCKET_IN - 0.1, t + 0.6)]))
    return s


def grommet():
    return revolve_x([(X_END - 3.0, R_GROMMET_IN), (X_END - 3.0, R_CABLE + 0.01),
                      (X_END - 0.1, R_CABLE + 0.01), (X_END + 0.1, R_GROMMET_OUT),
                      (X_END + 0.1, R_GROMMET_IN)])


def crimp_barrel():
    return revolve_x([(X_BORE_END - 0.5, R_BARREL_IN), (X_BORE_END - 0.5, R_BARREL_OUT),
                      (X_BORE_END + 3.0, R_BARREL_OUT), (X_BORE_END + 3.0, R_BARREL_IN)])


def place(w):
    """Plug frame -> receptacle frame: t = 0 (nose tip) at z = -12.6, head toward -z, back shell +x."""
    return w.rotate((0, 0, 0), (1, 0, 0), 180).translate((0, 0, -27.8 + T_RECESS))


if __name__ == "__main__":
    common = [(place(seal()), SEAL), (place(grommet()), SEAL),
              (place(socket()), METAL), (place(crimp_barrel()), METAL)]
    body = place(housing())
    for mpn, color in COLORS.items():
        print("3D model  ", write_model(LIB, f"Amphenol_SurLok-Plus_{mpn}", [(body, color), *common]))
