#!/usr/bin/env python3
"""Metal-element current-sense shunt footprints and 3D models with each manufacturer's own land
pattern (the vendors' pads differ from IPC chip-resistor lands, so no kicad-library-tools chip
generator spec fits).

Usage: ~/.cache/dropout/klt-venv/bin/python generators/custom/R_Shunt.py

Sources:
- Stackpole CSS2725 (0.0002-0.003 Ω): SEI-CSS_CSSH data sheet, rev date 8/19/2026. Body
  L 6.81 x W 6.45 x H 0.99 (0.0002-0.0003 Ω row), terminal T 2.16 (p. 5); recommended solder pad
  a 3.18 x b 6.86, gap i 1.32 (p. 10).
- Stackpole HCS2512 ...L250: SEI-HCS data sheet, rev date 8/11/2026. Body L 6.50 x W 3.25, height
  H 1.35, element thickness T 1.00 raised by P 0.35, terminal A 0.90 (p. 2); recommended solder pad
  b 1.80 x c 3.40, gap a 3.80 (p. 6).
- Vishay WSK1216 (4-terminal): data sheet doc 30189, revision 14-Sep-2026, p. 2. Body W 3.1 (across
  the current path) x L 3.81 x H 1.9; solder pads: each terminal has a force land a 2.95 and a sense
  land b 0.61 long with gap c 0.50 between them, lands w 3.60 across both terminals with gap d 0.70
  (so each land is 1.45 wide). Both sense lands sit at the same end of the part. Pads numbered as
  KiCad's Device:R_Shunt: 1 force and 2 sense on one terminal, 3 sense and 4 force on the other.
"""
from fplib import (BODY, CRT_CLR, CRT_W, FAB_W, METAL, SILK_PAD, SILK_W, fab_ref, footprint_text, line,
                   model_ref, rect, smd_pad, text, up, write_footprint, write_model)

LIB = "DropOut_Resistor_SMD"
ELEMENT = (0.45, 0.45, 0.48)    # resistive alloy, darker than the copper/tin terminals


def rr(w, h):
    """KLC F6.3 corner radius: 25 % of the short side, at most 0.25 mm."""
    return round(min(0.25, 0.25 / min(w, h)), 4)


def box(x0, x1, y0, y1, z0, z1):
    import cadquery as cq
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0).translate(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))


def two_terminal(name, pad_w, pad_h, gap, body_l, body_w, descr, tags, model):
    px = gap / 2 + pad_w / 2
    crt_x = up(max(px + pad_w / 2, body_l / 2) + CRT_CLR, 0.05)
    sy = max(pad_h, body_w) / 2 + SILK_PAD + SILK_W / 2
    crt_y = up(max(max(pad_h, body_w) / 2 + CRT_CLR, sy + SILK_W / 2 + 0.05), 0.05)
    body = [
        text("Reference", "REF**", -crt_y - 0.8, "F.SilkS"),
        text("Value", name, crt_y + 0.8, "F.Fab"),
        line(-body_l / 2, -sy, body_l / 2, -sy, "F.SilkS", SILK_W),
        line(-body_l / 2, sy, body_l / 2, sy, "F.SilkS", SILK_W),
        rect(-crt_x, -crt_y, crt_x, crt_y, "F.CrtYd", CRT_W),
        rect(-body_l / 2, -body_w / 2, body_l / 2, body_w / 2, "F.Fab", FAB_W),
        fab_ref(0.8),
        smd_pad(1, -px, 0, pad_w, pad_h, rratio=rr(pad_w, pad_h)),
        smd_pad(2, px, 0, pad_w, pad_h, rratio=rr(pad_w, pad_h)),
        model_ref(LIB, name),
    ]
    return name, footprint_text(name, descr, tags, body), model


def css2725():
    L, W, H, T = 6.81, 6.45, 0.99, 2.16
    def model():
        term = box(-L / 2, -L / 2 + T, -W / 2, W / 2, 0, H).union(box(L / 2 - T, L / 2, -W / 2, W / 2, 0, H))
        return [(term, METAL), (box(-L / 2 + T, L / 2 - T, -W / 2, W / 2, 0, H), ELEMENT)]
    return two_terminal(
        "R_Shunt_Stackpole_CSS2725", 3.18, 6.86, 1.32, L, W,
        "Stackpole CSS2725 metal alloy current sense resistor, 6.81 x 6.45 mm, recommended solder pad "
        "(SEI-CSS_CSSH data sheet rev 8/19/2026 p. 10), https://www.seielect.com/catalog/SEI-CSS_CSSH.PDF",
        "resistor shunt current sense Stackpole CSS2725 2725", model)


def hcs2512():
    L, W, H, T, A, P = 6.50, 3.25, 1.35, 1.00, 0.90, 0.35
    def model():
        feet = box(-L / 2, -L / 2 + A, -W / 2, W / 2, 0, P).union(box(L / 2 - A, L / 2, -W / 2, W / 2, 0, P))
        return [(feet, METAL), (box(-L / 2, L / 2, -W / 2, W / 2, P, P + T), ELEMENT)]
    return two_terminal(
        "R_Shunt_Stackpole_HCS2512", 1.80, 3.40, 3.80, L, W,
        "Stackpole HCS2512 high current metal alloy shunt (raised element), 6.50 x 3.25 mm, recommended "
        "solder pad (SEI-HCS data sheet rev 8/11/2026 p. 6), https://www.seielect.com/catalog/SEI-HCS.pdf",
        "resistor shunt current sense Stackpole HCS2512 2512", model)


def wsk1216():
    name = "R_Shunt_Vishay_WSK1216"
    W, L, H = 3.1, 3.81, 1.9                      # x across the current path, y along the terminals
    lw, d = 1.45, 0.70                            # land width, gap between the two terminals' lands
    a, b, c = 2.95, 0.61, 0.50
    px = d / 2 + lw / 2
    y0 = -(a + c + b) / 2                         # force lands at the top, sense lands below
    fy, sy_ = y0 + a / 2, y0 + a + c + b / 2
    pads = [smd_pad(1, -px, fy, lw, a, rratio=rr(lw, a)), smd_pad(2, -px, sy_, lw, b, rratio=rr(lw, b)),
            smd_pad(3, px, sy_, lw, b, rratio=rr(lw, b)), smd_pad(4, px, fy, lw, a, rratio=rr(lw, a))]
    ext_x, ext_y = max(px + lw / 2, W / 2), max(-y0, L / 2)
    crt_x = up(ext_x + CRT_CLR, 0.05)
    sy = ext_y + SILK_PAD + SILK_W / 2
    crt_y = up(max(ext_y + CRT_CLR, sy + SILK_W / 2 + 0.05), 0.05)
    body = [
        text("Reference", "REF**", -crt_y - 0.8, "F.SilkS"),
        text("Value", name, crt_y + 0.8, "F.Fab"),
        line(-(px + lw / 2), -sy, W / 2, -sy, "F.SilkS", SILK_W),     # longer on the pin 1 side
        line(-W / 2, sy, W / 2, sy, "F.SilkS", SILK_W),
        rect(-crt_x, -crt_y, crt_x, crt_y, "F.CrtYd", CRT_W),
        "\n".join(line(*p0, *p1, "F.Fab", FAB_W) for p0, p1 in zip(
            [(-W / 2 + 0.5, -L / 2), (W / 2, -L / 2), (W / 2, L / 2), (-W / 2, L / 2), (-W / 2, -L / 2 + 0.5)],
            [(W / 2, -L / 2), (W / 2, L / 2), (-W / 2, L / 2), (-W / 2, -L / 2 + 0.5), (-W / 2 + 0.5, -L / 2)])),
        fab_ref(0.6),
        *pads,
        model_ref(LIB, name),
    ]
    descr = ("Vishay WSK1216 4-terminal (Kelvin) Power Metal Strip resistor, 3.1 x 3.81 mm, solder pad "
             "dimensions (data sheet doc 30189 rev 14-Sep-2026 p. 2); pads 1/4 force, 2/3 sense, "
             "https://www.vishay.com/docs/30189/wsk1216.pdf")
    def model():
        e = 0.5                                   # half-width of the element strip between the terminals
        term = box(-W / 2, -e, -L / 2, L / 2, 0, H).union(box(e, W / 2, -L / 2, L / 2, 0, H))
        slot = box(-W / 2, W / 2, y0 + a, y0 + a + c, 0, H - 0.6)     # gap between force and sense prongs
        return [(term.cut(slot), METAL), (box(-e, e, -1.35, 1.35, H - 0.5, H), ELEMENT)]
    return name, footprint_text(name, descr, "resistor shunt current sense Kelvin 4-terminal Vishay WSK1216", body), model


if __name__ == "__main__":
    for name, fp, model in (css2725(), hcs2512(), wsk1216()):
        print("footprint ", write_footprint(LIB, name, fp))
        print("3D model  ", write_model(LIB, name, model()))
