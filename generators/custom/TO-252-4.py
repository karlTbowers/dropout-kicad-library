#!/usr/bin/env python3
"""TO-252-4 (DPAK, 5 leads at 1.14 mm pitch with the centre lead cut; tab = pad 3) footprint and
3D model.

Usage: ~/.cache/dropout/klt-venv/bin/python generators/custom/TO-252-4.py

For TI's KVU package (TPS7B8133QKVURQ1): mechanical drawing MPSF019, KVU (R-PSFM-G5), 4205521-3/D
02/2009, JEDEC TO-252 variation AD. Lead 3 is cut short and "in electrical contact with the
exposed thermal tab", so the tab is pad 3. TI publishes no land pattern for KVU0005A (the
TPS7B81-Q1 datasheet SBVS370F has none and MPSF019 is outline only), so the land is the one
kicad-library-tools' DPAK generator makes for KiCad's stock TO-252-4 (pads 2.2 x 0.8, tab pad
6.4 x 5.8, 10.6 mm span, four 3.05 x 2.75 paste apertures). The stock footprint's origin is
0.84 mm off the centre of its pads (a KLC F6.2 error in our checker), so it is redrawn here with
the origin at the pad centre. Body as the stock model (6.22 x 6.5 x 2.3,
leads 0.6 wide, tab 1.0 out of the body), inside MPSF019's tolerances (body 5.97..6.22 x
6.50..6.70, 9.80..10.41 overall, 2.18..2.39 high, leads 0.51..0.71).
"""
from fplib import (BODY, CRT_CLR, CRT_W, FAB_W, METAL, SILK_PAD, SILK_W, fab_ref, footprint_text, line,
                   model_ref, poly, smd_pad, text, up, write_footprint, write_model)

LIB = "DropOut_Package_TO_SOT_SMD"
NAME = "TO-252-4"
DX = 0.84                          # stock generator coordinates -> pad-centred origin

PITCH = 1.14
LEADS = {1: -2 * PITCH, 2: -PITCH, 4: PITCH, 5: 2 * PITCH}   # lead 3 is cut (tab = pad 3)
PAD = (2.2, 0.8)
PAD_X = -5.04 + DX                 # -4.2
TAB = (6.4, 5.8)
TAB_X = 1.26 + DX                  # 2.1
PASTE = (3.05, 2.75)
PASTE_DX, PASTE_Y = 1.675, 1.525   # four apertures at TAB_X +/- PASTE_DX, +/- PASTE_Y

BODY_X0, BODY_X1, BODY_W, BODY_H = -3.11 + DX, 3.11 + DX, 6.5, 2.3
TAB_X1, TAB_W, TAB_T = 4.11 + DX, 5.4, 0.5
LEAD_X0, LEAD_W, LEAD_T = -5.81 + DX, 0.6, 0.5


def footprint():
    pad_x0, pad_x1 = PAD_X - PAD[0] / 2, TAB_X + TAB[0] / 2
    assert abs(pad_x0 + pad_x1) < 1e-9
    crt_x = up(pad_x1 + CRT_CLR, 0.05)
    crt_y = up(max(TAB[1], BODY_W) / 2 + CRT_CLR, 0.05)
    # Silk: body outline between the leads and the tab pad, open at the tab pad
    sy = BODY_W / 2 + SILK_W / 2 + 0.05
    sx0 = BODY_X0 - SILK_W / 2 - 0.05
    sx1 = TAB_X - TAB[0] / 2 - SILK_PAD - SILK_W / 2
    lead_clear = 2 * PITCH + PAD[1] / 2 + SILK_PAD + SILK_W / 2
    body = [
        text("Reference", "REF**", -crt_y - 0.8, "F.SilkS"),
        text("Value", NAME, crt_y + 0.8, "F.Fab"),
        line(sx0, -sy, sx1, -sy, "F.SilkS", SILK_W), line(sx0, sy, sx1, sy, "F.SilkS", SILK_W),
        line(sx0, -sy, sx0, -lead_clear, "F.SilkS", SILK_W), line(sx0, sy, sx0, lead_clear, "F.SilkS", SILK_W),
        poly([(PAD_X, -2 * PITCH - PAD[1] / 2 - SILK_PAD), (PAD_X - 0.34, -sy + 0.04), (PAD_X + 0.34, -sy + 0.04)],
             "F.SilkS", SILK_W),
        line(-crt_x, -crt_y, crt_x, -crt_y, "F.CrtYd", CRT_W), line(crt_x, -crt_y, crt_x, crt_y, "F.CrtYd", CRT_W),
        line(crt_x, crt_y, -crt_x, crt_y, "F.CrtYd", CRT_W), line(-crt_x, crt_y, -crt_x, -crt_y, "F.CrtYd", CRT_W),
        # body with a chamfered pin 1 corner, exposed tab, leads
        poly([(BODY_X1, -BODY_W / 2), (BODY_X1, BODY_W / 2), (BODY_X0, BODY_W / 2), (BODY_X0, -BODY_W / 2 + 1.0),
              (BODY_X0 + 1.0, -BODY_W / 2), (BODY_X1, -BODY_W / 2)], "F.Fab", FAB_W, fill=False),
        line(BODY_X1, -TAB_W / 2, TAB_X1, -TAB_W / 2, "F.Fab", FAB_W),
        line(TAB_X1, -TAB_W / 2, TAB_X1, TAB_W / 2, "F.Fab", FAB_W),
        line(TAB_X1, TAB_W / 2, BODY_X1, TAB_W / 2, "F.Fab", FAB_W),
        *[ln for y in LEADS.values() for ln in (
            line(BODY_X0, y - LEAD_W / 2, LEAD_X0, y - LEAD_W / 2, "F.Fab", FAB_W),
            line(LEAD_X0, y - LEAD_W / 2, LEAD_X0, y + LEAD_W / 2, "F.Fab", FAB_W),
            line(LEAD_X0, y + LEAD_W / 2, BODY_X0, y + LEAD_W / 2, "F.Fab", FAB_W))],
        fab_ref(),
        *[smd_pad(n, PAD_X, y, *PAD, rratio=0.090909) for n, y in LEADS.items()],
        smd_pad(3, TAB_X, 0, *TAB, rratio=0.043103).replace('"F.Cu" "F.Mask" "F.Paste"', '"F.Cu" "F.Mask"'),
        *[smd_pad("", TAB_X + sx * PASTE_DX, sy_ * PASTE_Y, *PASTE, rratio=0.090909)
          .replace('"F.Cu" "F.Mask" "F.Paste"', '"F.Paste"') for sx in (-1, 1) for sy_ in (-1, 1)],
        model_ref(LIB, NAME),
    ]
    descr = ("TO-252/DPAK SMD package, 5 leads with the centre lead cut, tab = pad 3 (TI KVU / KVU0005A, "
             "mechanical drawing MPSF019; land as KiCad's stock TO-252-4), https://www.ti.com/lit/pdf/MPSF019")
    return footprint_text(NAME, descr, "DPAK TO-252 DPAK-5 TO-252-5 KVU", body)


def model():
    import cadquery as cq
    box = lambda x0, x1, w, z0, z1, y=0: cq.Workplane("XY").box(x1 - x0, w, z1 - z0) \
        .translate(((x0 + x1) / 2, y, (z0 + z1) / 2))
    body = box(BODY_X0, BODY_X1, BODY_W, 0.1, BODY_H)
    metal = box(BODY_X1 - 4.24, TAB_X1, TAB_W, 0.0, TAB_T)     # tab: 5.24 long, 1.0 out of the body
    for y in LEADS.values():                                    # gull-wing: foot, riser, upper arm
        metal = metal.union(box(LEAD_X0, LEAD_X0 + 1.2, LEAD_W, 0.0, LEAD_T, y)) \
            .union(box(LEAD_X0 + 1.0, LEAD_X0 + 1.5, LEAD_W, 0.0, 0.9 + LEAD_T, y)) \
            .union(box(LEAD_X0 + 1.0, BODY_X0 + 0.1, LEAD_W, 0.9, 0.9 + LEAD_T, y))
    return [(body, BODY), (metal, METAL)]


if __name__ == "__main__":
    print("footprint ", write_footprint(LIB, NAME, footprint()))
    print("3D model  ", write_model(LIB, NAME, model()))
