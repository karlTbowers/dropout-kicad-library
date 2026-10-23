#!/usr/bin/env python3
"""TOLL-family (8 flat leads at 1.2 mm pitch + drain tab, ~9.9 x 11.7 mm) power MOSFET footprints and
3D models, one per manufacturer land pattern. No kicad-library-tools generator covers these land
patterns (notched tab copper or mask, comb source lands, round paste apertures).

Usage: ~/.cache/dropout/klt-venv/bin/python generators/custom/TOLL.py

Orientation as KiCad's stock Infineon_PG-HSOF-8-x: leads on the left, pin 1 at the top, tab on the
right; the vendors' top-view drawings (leads at the bottom, pin 1 on the left) turned 90° clockwise.
The origin is the centre of the land pattern's lead-to-tab span. The tab is pad 9 (the vendors do not
number it). Every lead is its own pad: where a vendor joins the source leads in copper (Infineon,
AOS comb), the source pads stay separate and the board's source copper joins them (DropOut never
combines pins).

Sources:
- Infineon PG-HSOF-8-2: IAUTN08S5N012L data sheet Rev. 1.0 (2024-02-28) p. 12, package outline and
  footprint. Lead lands 0.8 x 2.5 at 5.435 mm from the footprint reference; tab copper 10.1 x 8.0
  (1.385 mm past the reference toward the leads) with a solder-mask-defined opening, notched to
  8.7 mm for 2.8 mm and 9.7 mm for the 3.7 mm next to the leads; stencil 0.7 x 2.35 per lead
  (centre 5.41 mm) and 42 round Ø1.0 apertures on the tab.
- AOS TOLLA: AOS package outline PO-00272 version F, "Land pattern recommendations": 13.18 mm span,
  tab 10.20 x 7.45 notched to 8.90 mm wide for 2.95 mm, lead lands 2.61 long, gate land 1.0 wide,
  source comb (pins 2-8) split by 0.20 mm slots. AOS gives no stencil; paste is DropOut's default.
- Taiwan Semiconductor TOLL_A: TSM018NM08TL data sheet version A2505 p. 6, "Suggested pad layout":
  tab 10.20 x 8.10, 2.40 gap, leads 0.80 x 2.80 at 1.20 pitch, 13.30 span. No stencil given;
  paste is DropOut's default.
"""
from fplib import (BODY, CRT_CLR, CRT_W, FAB_W, METAL, SILK_PAD, SILK_W, fab_ref, footprint_text, line,
                   model_ref, r, rect, text, up, write_footprint, write_model)

LIB = "DropOut_Package_TO_SOT_SMD"
PITCH = 1.2
LEAD_Y = [-4.2 + i * PITCH for i in range(8)]          # pin 1 at the top


def pad(num, x, y, w, h, layers, shape="rect"):
    """Copper pads are rounded rectangles (KLC F6.3: 25 %, at most 0.25 mm); paste apertures keep
    the vendor's shape."""
    lay = " ".join(f'"{l}"' for l in layers)
    extra = ""
    if shape == "rect" and "F.Cu" in layers:
        shape, extra = "roundrect", f" (roundrect_rratio {r(min(0.25, 0.25 / min(w, h)))})"
    return f'\t(pad "{num}" smd {shape} (at {r(x)} {r(y)}) (size {r(w)} {r(h)})\n\t\t(layers {lay}){extra})'


def poly_pad(num, pts, layers):
    """Custom pad from an absolute polygon; anchor is a small square at the polygon's first point's
    bounding-box centre (inside the shape for the convex-ish outlines used here)."""
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    ax, ay = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    rel = " ".join(f"(xy {r(x - ax)} {r(y - ay)})" for x, y in pts)
    lay = " ".join(f'"{l}"' for l in layers)
    return (f'\t(pad "{num}" smd custom (at {r(ax)} {r(ay)}) (size 1 1)\n\t\t(layers {lay})\n'
            f'\t\t(options (clearance outline) (anchor rect))\n'
            f'\t\t(primitives\n\t\t\t(gr_poly (pts {rel}) (width 0) (fill yes))\n\t\t))')


def notched(x0, x1, segments):
    """Outline of a tab whose half-width changes along x: segments = [(x_from, x_to, half_width), ...]
    from x0 to x1. Returns the polygon, going along the top edge then back along the bottom."""
    top = []
    for a, b, hw in segments:
        top += [(a, -hw), (b, -hw)]
    bottom = [(x, -y) for x, y in reversed(top)]
    return top + bottom


def grid_paste(x0, x1, y0, y1, nx, ny, fill):
    """nx x ny rectangular paste apertures covering `fill` of each cell's width and height."""
    cw, ch = (x1 - x0) / nx, (y1 - y0) / ny
    return [pad("", x0 + (i + 0.5) * cw, y0 + (j + 0.5) * ch, cw * fill, ch * fill, ("F.Paste",))
            for i in range(nx) for j in range(ny)]


# ---------------------------------------------------------------- land patterns

def infineon_hsof_8_2():
    sh = 0.035                                   # datasheet reference -> span centre
    X = lambda dy: -(dy - sh)                    # datasheet "down toward the leads" -> our -x
    out = []
    lx = X(5.435)
    for n, y in enumerate(LEAD_Y, start=1):
        out.append(pad(n, lx, y, 2.5, 0.8, ("F.Cu", "F.Mask")))
        out.append(pad("", X(5.41), y, 2.35, 0.7, ("F.Paste",)))
    # tab: copper 8.0 x 10.1, solder-mask-defined notched opening, 42 round paste apertures
    tx0, tx1 = X(1.385), X(-6.615)
    out.append(pad(9, (tx0 + tx1) / 2, 0, tx1 - tx0, 10.1, ("F.Cu",)))
    out.append(poly_pad("", notched(tx0, tx1, [(tx0, X(-2.315), 4.85), (X(-2.315), X(-5.115), 4.35),
                                               (X(-5.115), tx1, 5.05)]), ("F.Mask",)))
    col = [-4.15 + k * 8.3 / 7 for k in range(8)]
    for j in range(6):
        dy = -j * 5.84 / 5
        for k, dx in enumerate(col):
            if j in (1, 2, 3) and k in (0, 7):   # beside the mask notches
                continue
            out.append(pad("", X(dy), dx, 1.0, 1.0, ("F.Paste",), shape="circle"))
    return out, dict(lead=(lx - 1.25, lx + 1.25), tab=(tx0, tx1), tab_hw=5.05)


def aos_tolla():
    sh = 0.05                                    # (6.64 - 6.54) / 2
    X = lambda yv: yv - sh                       # AOS "up toward the tab" -> our +x
    lx0, lx1 = X(-6.54), X(-6.54 + 2.61)
    out = [pad(1, (lx0 + lx1) / 2, -4.30, lx1 - lx0, 1.00, ("F.Cu", "F.Mask", "F.Paste"))]
    fingers = [(-3.40, -2.50), (-2.30, -1.30), (-1.10, -0.10), (0.10, 1.10), (1.30, 2.30), (2.50, 3.50), (3.70, 4.80)]
    for n, (a, b) in enumerate(fingers, start=2):
        out.append(pad(n, (lx0 + lx1) / 2, (a + b) / 2, lx1 - lx0, b - a, ("F.Cu", "F.Mask", "F.Paste")))
    tx0, tx1 = X(-0.81), X(6.64)
    out.append(poly_pad(9, notched(tx0, tx1, [(tx0, X(2.04), 5.10), (X(2.04), X(4.99), 4.45),
                                              (X(4.99), tx1, 5.10)]), ("F.Cu", "F.Mask")))
    out += grid_paste(tx0, tx1, -4.45, 4.45, 3, 3, 0.8)
    return out, dict(lead=(lx0, lx1), tab=(tx0, tx1), tab_hw=5.10)


def tsc_toll_a():
    lx0, lx1 = -6.65, -6.65 + 2.80
    out = [pad(n, (lx0 + lx1) / 2, y, 2.80, 0.80, ("F.Cu", "F.Mask", "F.Paste"))
           for n, y in enumerate(LEAD_Y, start=1)]
    tx0, tx1 = lx1 + 2.40, 6.65
    out.append(pad(9, (tx0 + tx1) / 2, 0, tx1 - tx0, 10.20, ("F.Cu", "F.Mask")))
    out += grid_paste(tx0, tx1, -5.10, 5.10, 3, 3, 0.75)
    return out, dict(lead=(lx0, lx1), tab=(tx0, tx1), tab_hw=5.10)


# ---------------------------------------------------------------- packages
# body_x/body_y: moulded body; length: body + leads; lead_w: lead width; height: seated height.
PARTS = [
    dict(name="Infineon_PG-HSOF-8-2", lands=infineon_hsof_8_2, body_x=10.375, body_y=9.9, length=11.675,
         lead_w=0.8, height=2.3, tags="mosfet hsof toll PG-HSOF-8-2 dual gate",
         descr="Infineon PG-HSOF-8-2 (TOLL, dual-gate pinout: pins 1-2 gates, 3-8 source, tab drain), "
               "IAUTN08S5N012L data sheet Rev. 1.0 p. 12 footprint; tab = pad 9, every lead its own pad, "
               "https://www.infineon.com/dgdl/Infineon-IAUTN08S5N012L-DataSheet-v01_00-EN.pdf?fileId=8ac78c8c8eeb092c018ef669549208cf"),
    dict(name="AOS_TOLLA", lands=aos_tolla, body_x=10.38, body_y=9.8, length=11.68,
         lead_w=0.7, height=2.3, tags="mosfet toll tolla AOS",
         descr="AOS TOLLA (pin 1 gate, 2-8 source, tab drain), AOS package outline PO-00272 version F "
               "land pattern recommendations; tab = pad 9, every lead its own pad, "
               "https://www.aosmd.com/sites/default/files/res/packaging_information/TOLLA.pdf"),
    dict(name="TSC_TOLL-A", lands=tsc_toll_a, body_x=10.43, body_y=9.8, length=11.68,
         lead_w=0.8, height=2.3, tags="mosfet toll tolla TOLL_A Taiwan Semiconductor",
         descr="Taiwan Semiconductor TOLL_A (pin 1 gate, 2-8 source, tab drain), TSM018NM08TL data sheet "
               "version A2505 p. 6 suggested pad layout; tab = pad 9, "
               "https://www.taiwansemi.com/assets/datasheet/pdf.php?pn=TSM018NM08TL"),
]


def footprint(p):
    pads, ext = p["lands"]()
    lx0, tx1 = ext["lead"][0], ext["tab"][1]
    px0 = -p["length"] / 2                      # lead tips; package centred on the land span
    bx0, bx1 = px0 + p["length"] - p["body_x"], p["length"] / 2
    hb = p["body_y"] / 2
    crt_x0 = up(min(lx0, px0) - CRT_CLR, 0.05)
    crt_x1 = up(max(tx1, bx1) + CRT_CLR, 0.05)
    sy = max(hb, ext["tab_hw"]) + SILK_PAD + SILK_W / 2
    crt_y = up(max(max(hb, ext["tab_hw"]) + CRT_CLR, sy + SILK_W / 2 + 0.05), 0.05)   # silk inside the courtyard
    c = 1.0                                       # fab pin-1 chamfer
    body = [
        text("Reference", "REF**", -crt_y - 0.8, "F.SilkS"),
        text("Value", p["name"], crt_y + 0.8, "F.Fab"),
        line(lx0, -sy, bx1, -sy, "F.SilkS", SILK_W),          # top line runs out to pin 1's toe
        line(bx0, sy, bx1, sy, "F.SilkS", SILK_W),
        rect(crt_x0, -crt_y, crt_x1, crt_y, "F.CrtYd", CRT_W),
        "\n".join(line(*a, *b, "F.Fab", FAB_W) for a, b in zip(
            [(bx0 + c, -hb), (bx1, -hb), (bx1, hb), (bx0, hb), (bx0, -hb + c)],
            [(bx1, -hb), (bx1, hb), (bx0, hb), (bx0, -hb + c), (bx0 + c, -hb)])),
        *["\n".join([line(bx0, y - p["lead_w"] / 2, px0, y - p["lead_w"] / 2, "F.Fab", FAB_W),
                     line(px0, y - p["lead_w"] / 2, px0, y + p["lead_w"] / 2, "F.Fab", FAB_W),
                     line(px0, y + p["lead_w"] / 2, bx0, y + p["lead_w"] / 2, "F.Fab", FAB_W)]) for y in LEAD_Y],
        fab_ref(),
        *pads,
        model_ref(LIB, p["name"]),
    ]
    return footprint_text(p["name"], p["descr"], p["tags"], body)


def model(p):
    import cadquery as cq
    box = lambda x0, x1, y0, y1, z0, z1: cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0) \
        .translate(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    px0 = -p["length"] / 2
    bx0, bx1 = px0 + p["length"] - p["body_x"], p["length"] / 2
    hb = p["body_y"] / 2
    mould = box(bx0, bx1, -hb, hb, 0.1, p["height"]).edges("|Z").fillet(0.2)
    metal = box(bx0 + 1.6, bx1 - 0.2, -hb + 0.3, hb - 0.3, 0.0, 0.1)          # exposed drain tab
    for y in LEAD_Y:
        metal = metal.union(box(px0, bx0 + 0.6, y - p["lead_w"] / 2, y + p["lead_w"] / 2, 0.0, 0.5))
    return [(mould, BODY), (metal, METAL)]


if __name__ == "__main__":
    for p in PARTS:
        print("footprint ", write_footprint(LIB, p["name"], footprint(p)))
        print("3D model  ", write_model(LIB, p["name"], model(p)))
