"""Shared footprint and 3D model builder for DEUTSCH DT-style 2-pin right-angle PCB headers
(TE DT13-2P and its equivalents such as Amphenol Sine AT13-2P-BMxx). Each part's script supplies
its manufacturer's dimensions as a Header and calls footprint() / model().

Frame: origin at pin 1, pin 2 at (+pitch, 0), mating face toward +y (the panel / board edge side).
Three NPTH holes take thread-forming screws from the solder side into the housing bosses: the
centre screw sits on the pin centreline toward the mating face, the outer two behind the pin row.
"""
from dataclasses import dataclass

from fplib import (CRT_W, FAB_W, METAL, SILK_W, footprint_text, line, model_ref, poly,
                   r, text, up)

CRT_CLR = 0.5                   # KLC F5.3: connectors


@dataclass
class Header:
    lib: str
    name: str
    descr: str
    tags: str
    screw_note: str
    pitch: float
    pin_drill: float
    pin_pad: float
    screw_drill: float
    screw_span: float           # outer screws, centre to centre
    screw_back: float           # centre screw to the outer screws' row
    screw_front: float          # pin row to the centre screw
    # Body outline seen from above, rear (-y) to mating face (+y): (y0, y1, half width, height);
    # height None marks the shroud, which spans shroud_z.
    sections: list
    shroud_z: tuple
    tail: float                 # pin tail below the boss faces
    pin_d: float
    boss_hole: float            # screw hole in the housing bosses (3D model)

    @property
    def xc(self):
        return self.pitch / 2

    @property
    def screws(self):
        back = -(self.screw_back - self.screw_front)
        return [(self.xc, self.screw_front), (self.xc - self.screw_span / 2, back),
                (self.xc + self.screw_span / 2, back)]

    @property
    def front(self):
        return self.sections[-1][1]


def stepped(h, offset):
    """Stepped outline grown by offset, corners on the grown contour."""
    ys = [s[0] for s in h.sections] + [h.sections[-1][1]]
    hws = [s[2] for s in h.sections]
    right = [(h.xc + hws[0] + offset, ys[0] - offset)]
    for i in range(len(hws) - 1):
        a, b = hws[i], hws[i + 1]
        yb = ys[i + 1] - offset if b > a else ys[i + 1] + offset
        right += [(h.xc + a + offset, yb), (h.xc + b + offset, yb)]
    right.append((h.xc + hws[-1] + offset, ys[-1] + offset))
    left = [(2 * h.xc - x, y) for x, y in right]
    return right + left[::-1] + [right[0]]


def polyline(pts, layer, w):
    return "\n".join(line(*pts[i], *pts[i + 1], layer, w) for i in range(len(pts) - 1))


def tht_pad(h, num, x, y, shape):
    extra = " (roundrect_rratio 0.25)" if shape == "roundrect" else ""
    return (f'\t(pad "{num}" thru_hole {shape} (at {r(x)} {r(y)}) (size {h.pin_pad} {h.pin_pad}) '
            f'(drill {h.pin_drill})\n\t\t(layers "*.Cu" "*.Mask"){extra})')


def npth(h, x, y):
    return (f'\t(pad "" np_thru_hole circle (at {r(x)} {r(y)}) (size {h.screw_drill} {h.screw_drill}) '
            f'(drill {h.screw_drill})\n\t\t(layers "*.Cu" "*.Mask"))')


def footprint(h):
    xc, s0 = h.xc, h.sections[0][0]
    flange = max(h.sections, key=lambda s: s[2])        # widest section ends at the flange seal face
    fab = stepped(h, 0)
    silk_off = FAB_W / 2 + SILK_W / 2 + 0.04          # 0.15 outside the body line
    silk = stepped(h, silk_off)
    # courtyard on a 0.01 grid, rounded away from the body centre (xc, 12.0)
    crt = [(xc + up(x - xc, 0.01), 12.0 + up(y - 12.0, 0.01)) for x, y in stepped(h, CRT_CLR)]
    top = s0 - silk_off
    # pin 1 marker: silk triangle on the rear edge above pin 1, fab triangle inside the body edge
    tri = [(0, top - 0.05), (-0.45, top - 0.45), (0.45, top - 0.45), (0, top - 0.05)]
    ftri = [(-0.8, s0), (0, s0 + 0.8), (0.8, s0)]
    body = [
        text("Reference", "REF**", s0 - CRT_CLR - 1.0, "F.SilkS"),
        text("Value", h.name, h.front + CRT_CLR + 1.0, "F.Fab"),
        polyline(silk, "F.SilkS", SILK_W),
        poly(tri, "F.SilkS", SILK_W),
        polyline(fab, "F.Fab", FAB_W),
        polyline(ftri, "F.Fab", FAB_W),
        polyline(crt, "F.CrtYd", CRT_W),
        line(xc - flange[2], flange[1], xc + flange[2], flange[1], "Cmts.User", FAB_W),
        f'\t(fp_text user "panel / flange seal face" (at {r(xc)} {r(flange[1] - 1.0)} 0) (layer "Cmts.User")\n'
        f'\t\t(effects (font (size 1 1) (thickness 0.15))))',
        f'\t(fp_text user "{h.screw_note}" (at {r(xc)} {r(h.front + CRT_CLR + 2.6)} 0) (layer "Cmts.User")\n'
        f'\t\t(effects (font (size 0.8 0.8) (thickness 0.12))))',
        f'\t(fp_text user "${{REFERENCE}}" (at {r(xc)} 10.5 0) (layer "F.Fab")\n'
        f'\t\t(effects (font (size 1 1) (thickness 0.15))))',
        tht_pad(h, 1, 0, 0, "roundrect"), tht_pad(h, 2, h.pitch, 0, "circle"),
        *[npth(h, x, y) for x, y in h.screws],
        model_ref(h.lib, h.name),
    ]
    return footprint_text(h.name, h.descr, h.tags, body, attr="through_hole")


def model(h):
    import cadquery as cq
    box = lambda x0, x1, y0, y1, z0, z1: cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0) \
        .translate(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    xc = h.xc
    housing = None
    for y0, y1, hw, ht in h.sections:
        z0, z1 = (0, ht) if ht else h.shroud_z
        b = box(xc - hw, xc + hw, y0, y1, z0, z1)
        housing = b if housing is None else housing.union(b)
    zc = sum(h.shroud_z) / 2
    housing = housing.cut(box(xc - 7.3, xc + 7.3, h.front - 13.0, h.front + 1, zc - 7.2, zc + 7.2))
    for x, y in h.screws:                               # screw holes in the bosses
        housing = housing.cut(cq.Workplane("XY").circle(h.boss_hole / 2).extrude(6).translate((x, y, -1)))
    metal = None
    for x in (0, h.pitch):
        tail = cq.Workplane("XY").circle(h.pin_d / 2).extrude(h.tail + 1.0).translate((x, 0, -h.tail))
        mate = cq.Workplane("XZ").circle(h.pin_d / 2).extrude(-11.0) \
            .translate((x, h.front - 13.0, zc))
        part = tail.union(mate)
        metal = part if metal is None else metal.union(part)
    # Built in footprint coordinates (y toward the mating face); KiCad's model frame has
    # Y = -footprint y, so mirror before export or the shroud ends up behind the pins.
    return [(housing.mirror("XZ"), (0.55, 0.56, 0.58)), (metal.mirror("XZ"), METAL)]
