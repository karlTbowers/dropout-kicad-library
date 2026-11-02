#!/usr/bin/env python3
"""3D models and dimensioned drawings for DropOut's copper flat-bar busbars: C110 copper flat bar, cut
to length and drilled in house, one Ø6.5 M6 clearance hole near each end.

Usage: ~/.cache/dropout/klt-venv/bin/python generators/custom/Busbar_Cu_FlatBar.py

Each bar has a parts/<name>/part.yaml with its fields, its model and its drawing, so the library
catalog lists it. Until 2026-11-02 both were model-only parts (docs/CONTRIBUTING.md "Model-only
parts"); now both are net-tie parts: a two-pin symbol and a footprint, so the schematic shows the bar
and it has a BOM line. The VBAT_IN bar first (node60-hw placement decision D02, option A): the
schematic joins VBAT_IN (J910) to the pass-through net (J901) through it on purpose, since a KiCad net
tie between two pads of one net joins nothing (tested on Node60: VBAT_IN had 17 unconnected items with
and without tie pads). Then the GND bar, the same way for consistency (user, 2026-11-02), with both
pins on GND: the GND plane joins its terminals as well. Footprint (net_tie() below): F.CrtYd = the bar outline with the REDCUBE spigot holes cut out, so
DRC keeps top-side parts from under the bar (as Node60's board-only BB901 did); F.Fab outline and
holes; two B.Cu net-tie pads, one inside each REDCUBE 74660016R terminal's pad 1 ring (the terminals
sit on the bottom side, the bar on top, and the stud joins them). A pad sits on the ring's anchor,
5.7 mm east (+x) of each spigot centre (Wuerth_REDCUBE_SMT.py), so the terminals must be placed with
their pad anchors toward +x, as Node60's are; the ring is round, so any point on it would do.

Sources (node60-hw, enclosure version 15, DEC-025, 2026-11-01):
- Stock: 1/8" x 3/4" C110 copper flat bar, 3.175 x 19.05 mm.
- Holes: Ø6.5, M6 clearance (place_connectors.py BUSBAR_HOLE), on the bar's centre line.
- Ends run half a bar width past each hole centre (place_connectors.py busbar_outline), so the
  length is the hole pitch + 19.05.
- Hole pitches: VBAT_IN J910-J901 106.0 mm, GND J911-J902 157.0 mm (terminal positions, version 15).
Estimated (marked ESTIMATE; DEC-025 gives no finish or edge detail): the stock's edge radius, the
deburring chamfer on the saw-cut ends and on the holes.

Frame: origin at the bar's centre, on its bottom face; the bar runs along x, holes at x = ±pitch/2;
z up. The model is symmetric about the XZ and YZ planes, so KiCad's mirrored model Y needs no
correction. The footprint uses the same frame, its model at zero offset (KLC F9.3). On a board the
bar rests on the REDCUBE spigots, which stand proud of the top face by the spigot length less the
board thickness (Node60, 2.0 mm board: 0.6 mm), so the board raises the placed model by that much.
"""
from pathlib import Path

import cadquery as cq

from fplib import CRT_W, FAB_W, REPO, footprint_text, model_ref, r, text, up, write_footprint, write_model
from Wuerth_REDCUBE_SMT import PARTS as REDCUBE_SMT

REDCUBE = REDCUBE_SMT["Wuerth_REDCUBE-SMT_WP-SMRT_74660016"]
SPIGOT_HOLE = REDCUBE["hole"]                          # Ø9.3 NPTH in the board
RING_X = (REDCUBE["pad"][0] + REDCUBE["pad"][1]) / 4   # pad 1 anchor, +x of the spigot centre (5.7)
TIE_PAD = (REDCUBE["pad"][1] - REDCUBE["pad"][0]) / 2  # the ring's width (1.6): pad inside the ring
HOLE_CUT = SPIGOT_HOLE / 2 + 0.1                       # courtyard cut-out radius (Node60 placer: drill/2 + 0.1)

LIB = "DropOut_Busbar"
COPPER = (0.80, 0.46, 0.27)

WIDTH, THICK = 19.05, 3.175        # 3/4" x 1/8" stock (DEC-025)
HOLE_D = 6.5                       # M6 clearance (place_connectors.py BUSBAR_HOLE)
EDGE_R = 0.4                       # ESTIMATE: rounded long edges of drawn C110 bar stock (ASTM B187 allows rounded corners)
END_CHAMFER = 0.3                  # ESTIMATE: deburred saw-cut ends
HOLE_CHAMFER = 0.3                 # ESTIMATE: deburred holes, both faces

STOCK = '1/8" x 3/4" C110 copper flat bar'
BARS = {                           # name -> (hole pitch, what it is), DEC-025 / place_connectors.py v15
    106.0: "Node60 VBAT_IN busbar (BB901, J910-J901)",
    157.0: "Node60 GND busbar (BB902, J911-J902)",
}
NET_TIE = {106.0, 157.0}           # bars that are net-tie parts with a footprint (the others are model-only)


def length(pitch):
    return pitch + WIDTH           # half a width past each hole centre


def name(pitch):
    return f"Busbar_Cu_{WIDTH:g}x{THICK:g}mm_L{length(pitch):g}mm_2xD{HOLE_D:g}mm_P{pitch:g}mm"


def bar(pitch):
    L = length(pitch)
    b = cq.Workplane("XY").box(L, WIDTH, THICK, centered=(True, True, False))
    b = b.edges("|X").fillet(EDGE_R)                       # long edges: rounded stock
    b = b.faces("<X or >X").edges().chamfer(END_CHAMFER)    # saw-cut ends, deburred
    for x in (-pitch / 2, pitch / 2):
        b = b.cut(cq.Workplane("XY").center(x, 0).circle(HOLE_D / 2).extrude(THICK))
    b = b.faces(">Z or <Z").edges("%CIRCLE").chamfer(HOLE_CHAMFER)
    return b


# ---- net-tie footprint ------------------------------------------------------------------------

def _rect(x1, y1, x2, y2, layer, w):
    return (f'\t(fp_rect (start {r(x1)} {r(y1)}) (end {r(x2)} {r(y2)}) (stroke (width {w}) (type solid))'
            f' (fill no) (layer "{layer}"))')


def _circle(cx, rad, layer, w):
    return (f'\t(fp_circle (center {r(cx)} 0) (end {r(cx + rad)} 0) (stroke (width {w}) (type solid))'
            f' (fill no) (layer "{layer}"))')


def net_tie(pitch):
    """Footprint text for a bar whose two holes sit on REDCUBE 74660016R terminals: pad 1 on the -x
    terminal, pad 2 on the +x terminal."""
    n, hl, hw = name(pitch), length(pitch) / 2, WIDTH / 2
    ch, cw = up(hl, 0.01), up(hw, 0.01)                    # courtyard: the bar outline on the 0.01 grid (KLC F5.3)
    holes = (-pitch / 2, pitch / 2)
    pads = [f'\t(pad "{i}" smd circle (at {r(x + RING_X)} 0) (size {r(TIE_PAD)} {r(TIE_PAD)})\n'
            f'\t\t(layers "B.Cu"))' for i, x in enumerate(holes, start=1)]
    # Reference silk inside the bar outline: nothing else may sit there, and next to the bar it overprints
    # the parts packed along it (Node60: C501, C503, C504 beside BB902)
    body = [text("Reference", "REF**", -hw / 2, "F.SilkS"), text("Value", n, hw + 1.5, "F.Fab"),
            '\t(net_tie_pad_groups "1, 2")',
            _rect(-ch, -cw, ch, cw, "F.CrtYd", CRT_W), *[_circle(x, HOLE_CUT, "F.CrtYd", CRT_W) for x in holes],
            _rect(-hl, -hw, hl, hw, "F.Fab", FAB_W), *[_circle(x, HOLE_D / 2, "F.Fab", FAB_W) for x in holes],
            f'\t(fp_text user "${{REFERENCE}}" (at 0 0 0) (layer "F.Fab")\n'
            f'\t\t(effects (font (size 1 1) (thickness 0.15))))',
            *pads, model_ref(LIB, n)]
    descr = (f"Busbar, 1/8 x 3/4 in C110 copper flat bar ({THICK:g} x {WIDTH:g} mm), {length(pitch):g} mm long, 2 x Ø{HOLE_D:g} M6 clearance "
             f"holes at {pitch:g} mm on Würth REDCUBE 74660016R terminals; net tie: one B.Cu pad in each "
             f"terminal's pad 1 ring, {RING_X:g} mm +x of its spigot; courtyard = bar outline, "
             f"https://github.com/karlTbowers/dropout-kicad-library/blob/main/drawings/{LIB}/{n}.svg")
    return footprint_text(n, descr, "busbar net tie copper flat bar C110 REDCUBE M6", body,
                          attr="exclude_from_pos_files")   # fitted by hand, so no smd type (KLC F6.1)


# ---- drawing ----------------------------------------------------------------------------------
# A plain SVG in mm: top view with the plan dimensions, side view with the thickness, and a title
# block. Black on white (it is a shop drawing; the catalog shows it on a paper-coloured panel).

FONT = 'font-family="Helvetica, Arial, sans-serif"'


def _t(x, y, s, size=3.0, anchor="middle", rot=None, weight="normal"):
    tr = f' transform="rotate({rot} {x:.3f} {y:.3f})"' if rot is not None else ""
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace('"', "&quot;")
    return (f'<text x="{x:.3f}" y="{y:.3f}" font-size="{size}" text-anchor="{anchor}" '
            f'font-weight="{weight}" stroke="none" fill="#000"{tr}>{s}</text>')


def _l(x1, y1, x2, y2, w=0.25, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}" stroke-width="{w}"{d}/>'


def _arrow(x, y, dx, dy):
    """Filled arrowhead with its tip at (x, y), pointing along (dx, dy) (unit vector)."""
    a, b = 2.2, 0.7
    px, py = -dy, dx
    pts = [(x, y), (x - a * dx + b * px, y - a * dy + b * py), (x - a * dx - b * px, y - a * dy - b * py)]
    return '<polygon points="' + " ".join(f"{u:.3f},{v:.3f}" for u, v in pts) + '" stroke="none" fill="#000"/>'


def hdim(x1, x2, y_feat, y_dim, label):
    """Horizontal dimension between x1 and x2, features at y_feat, dimension line at y_dim."""
    s = 1 if y_dim > y_feat else -1
    out = [_l(x1, y_feat + s * 1.0, x1, y_dim + s * 1.5, 0.18), _l(x2, y_feat + s * 1.0, x2, y_dim + s * 1.5, 0.18),
           _l(x1, y_dim, x2, y_dim, 0.18), _arrow(x1, y_dim, -1, 0), _arrow(x2, y_dim, 1, 0)]
    xt, anchor = (x1 + x2) / 2, "middle"
    if abs(x2 - x1) < 3.2 * len(label):        # no room between the arrows: label outside, left
        xt, anchor = min(x1, x2) - 2.5, "end"
    out.append(_t(xt, y_dim - 1.0, label, anchor=anchor))
    return out


def vdim(y1, y2, x_feat, x_dim, label):
    """Vertical dimension between y1 and y2, features at x_feat, dimension line at x_dim."""
    s = 1 if x_dim > x_feat else -1
    out = [_l(x_feat + s * 1.0, y1, x_dim + s * 1.5, y1, 0.18), _l(x_feat + s * 1.0, y2, x_dim + s * 1.5, y2, 0.18),
           _l(x_dim, y1, x_dim, y2, 0.18)]
    if abs(y2 - y1) < 5.0:                     # too short for arrows inside: outside, pointing in
        out += [_l(x_dim, y1 - 3.5, x_dim, y1, 0.18), _l(x_dim, y2, x_dim, y2 + 3.5, 0.18),
                _arrow(x_dim, y1, 0, 1), _arrow(x_dim, y2, 0, -1)]
    else:
        out += [_arrow(x_dim, y1, 0, -1), _arrow(x_dim, y2, 0, 1)]
    if abs(y2 - y1) < 2.0 * len(label):       # short span: label upright beside the dimension line
        out.append(_t(x_dim + s * 1.5, (y1 + y2) / 2 + 1.0, label, anchor="start" if s > 0 else "end"))
    else:                                      # rotated, reading upwards, outside the dimension line
        out.append(_t(x_dim + (3.4 if s > 0 else -1.2), (y1 + y2) / 2, label, rot=-90))
    return out


def drawing(pitch):
    L, W, T = length(pitch), WIDTH, THICK
    m = 18.0                                   # margin left/right
    top_y = 22.0                               # top edge of the plan view
    x0 = m                                     # bar's left end
    xc = x0 + L / 2
    hx = (xc - pitch / 2, xc + pitch / 2)
    yc = top_y + W / 2
    side_y = top_y + W + 26.0                  # top of the side view
    sec_y = side_y + T + 22.0                  # top of section A-A
    k = 3.0                                    # section scale
    tb_y = sec_y + T * k + 16.0                # title block top
    vw, vh = L + 2 * m, tb_y + 26.0
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {vw:.3f} {vh:.3f}" '
         f'width="{vw * 4:.0f}" height="{vh * 4:.0f}">',
         f'<rect x="0" y="0" width="{vw:.3f}" height="{vh:.3f}" fill="#fff"/>',
         '<defs><pattern id="hatch" width="1.6" height="1.6" patternUnits="userSpaceOnUse" '
         'patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="1.6" stroke="#000" stroke-width="0.15"/>'
         '</pattern></defs>',
         f'<g stroke="#000" fill="none" stroke-linecap="round" {FONT}>']
    # plan view
    o.append(f'<rect x="{x0:.3f}" y="{top_y:.3f}" width="{L:.3f}" height="{W:.3f}" stroke-width="0.4"/>')
    for x in hx:
        o.append(f'<circle cx="{x:.3f}" cy="{yc:.3f}" r="{HOLE_D / 2:.3f}" stroke-width="0.4"/>')
        o += [_l(x - 5.5, yc, x + 5.5, yc, 0.15, "3 1 0.6 1"), _l(x, yc - 5.5, x, yc + 5.5, 0.15, "3 1 0.6 1")]
    o.append(_l(x0 - 3, yc, x0 + L + 3, yc, 0.15, "6 1.5 1 1.5"))     # centre line
    o += hdim(x0, x0 + L, top_y, top_y - 9.0, f"{L:g}")
    o += hdim(hx[0], hx[1], top_y + W, top_y + W + 8.0, f"{pitch:g}")
    o += hdim(x0, hx[0], top_y + W, top_y + W + 8.0, f"{W / 2:g}")
    o += vdim(top_y, top_y + W, x0 + L, x0 + L + 7.0, f"{W:g}")
    # hole callout: leader from the right hole up and left into the gap above the bar
    hx1 = hx[1]
    lx, ly = hx1 - HOLE_D / 2 * 0.7071, yc - HOLE_D / 2 * 0.7071
    kx, ky = hx1 - 9.0, top_y - 4.0
    o += [_l(lx, ly, kx, ky, 0.18), _l(kx, ky, kx - 3, ky, 0.18), _arrow(lx, ly, 0.7071, 0.7071)]
    o.append(_t(kx - 3.5, ky + 1.0, f"2 × Ø{HOLE_D:g} THRU (M6 clearance)", anchor="end"))
    o.append(_t(xc, top_y - 15.5, "TOP", 3.2, weight="bold"))
    # side view
    o.append(f'<rect x="{x0:.3f}" y="{side_y:.3f}" width="{L:.3f}" height="{T:.3f}" stroke-width="0.4"/>')
    for x in hx:
        o += [_l(x - HOLE_D / 2, side_y, x - HOLE_D / 2, side_y + T, 0.18, "1.2 0.8"),
              _l(x + HOLE_D / 2, side_y, x + HOLE_D / 2, side_y + T, 0.18, "1.2 0.8")]
    o += vdim(side_y, side_y + T, x0 + L, x0 + L + 7.0, f"{T:g}")
    o.append(_t(xc, side_y - 3.0, "SIDE", 3.2, weight="bold"))
    # section A-A through a hole, 3:1: rounded stock edges and hole chamfers
    o += [_l(hx[1], top_y - 3, hx[1], top_y - 0.5, 0.35), _l(hx[1], top_y + W + 0.5, hx[1], top_y + W + 3, 0.35),
          _t(hx[1] + 1.2, top_y - 3.2, "A", 3.0, anchor="start"), _t(hx[1] + 1.2, top_y + W + 5.6, "A", 3.0, anchor="start")]
    sx = x0 + 10.0                             # left edge of the section
    r, c, hr = EDGE_R * k, HOLE_CHAMFER * k, HOLE_D / 2 * k
    sw, st, mid = W * k, T * k, x0 + 10.0 + W * k / 2
    for side in (-1, 1):                       # each half: outer edge to the hole wall, hatched
        xo, xh = (sx, mid - hr) if side < 0 else (sx + sw, mid + hr)
        xi = xh + (-c if side < 0 else c)      # chamfer start on the faces
        d = (f"M {xi:.3f} {sec_y:.3f} L {xo - side * r:.3f} {sec_y:.3f} "
             f"Q {xo:.3f} {sec_y:.3f} {xo:.3f} {sec_y + r:.3f} L {xo:.3f} {sec_y + st - r:.3f} "
             f"Q {xo:.3f} {sec_y + st:.3f} {xo - side * r:.3f} {sec_y + st:.3f} L {xi:.3f} {sec_y + st:.3f} "
             f"L {xh:.3f} {sec_y + st - c:.3f} L {xh:.3f} {sec_y + c:.3f} Z")
        o.append(f'<path d="{d}" stroke-width="0.4" fill="url(#hatch)"/>')
    o.append(_l(mid, sec_y - 3, mid, sec_y + st + 3, 0.15, "3 1 0.6 1"))
    o += hdim(sx, sx + sw, sec_y + st, sec_y + st + 7.0, f"{W:g}")
    o += hdim(mid - hr, mid + hr, sec_y, sec_y - 5.0, f"Ø{HOLE_D:g}")
    o += vdim(sec_y, sec_y + st, sx + sw, sx + sw + 7.0, f"{T:g}")
    o.append(_t(sx + sw + 26, sec_y + 3.0, "SECTION A-A  3:1", 3.2, anchor="start", weight="bold"))
    o.append(_t(sx + sw + 26, sec_y + 7.5, f"Edges R{EDGE_R:g}; ends, holes {END_CHAMFER:g} × 45°",
                2.6, anchor="start"))
    o.append(_t(sx + sw + 26, sec_y + 11.5, "(edge radius and deburr: estimates, not set by DEC-025)", 2.2, anchor="start"))
    # title block
    o.append(f'<rect x="{x0:.3f}" y="{tb_y:.3f}" width="{L:.3f}" height="22" stroke-width="0.3"/>')
    o.append(_l(x0, tb_y + 8, x0 + L, tb_y + 8, 0.2))
    o.append(_t(x0 + 2, tb_y + 5.6, name(pitch), 3.4, anchor="start", weight="bold"))
    o.append(_t(x0 + 2, tb_y + 12.5, f"Material: {STOCK} (3.175 × 19.05 mm), cut to length, drill, deburr",
                2.6, anchor="start"))
    o.append(_t(x0 + 2, tb_y + 17.0, f"{BARS[pitch]}. Dimensions in mm. Break sharp edges.",
                2.6, anchor="start"))
    o.append(_t(x0 + 2, tb_y + 21.0, "DropOut. Source: generators/custom/Busbar_Cu_FlatBar.py (node60-hw DEC-025)",
                2.0, anchor="start"))
    o.append("</g></svg>")
    path = REPO / "drawings" / LIB / f"{name(pitch)}.svg"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(o) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    for pitch in BARS:
        print("3D model  ", write_model(LIB, name(pitch), [(bar(pitch), COPPER)]))
        print("drawing   ", drawing(pitch))
        if pitch in NET_TIE:
            print("footprint ", write_footprint(LIB, name(pitch), net_tie(pitch)))
