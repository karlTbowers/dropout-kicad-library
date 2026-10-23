#!/usr/bin/env python3
"""0603 (1608 metric) chip NTC thermistor footprints with the manufacturers' recommended reflow
land patterns. kicad-library-tools' chip generator (SMD_2terminal_chip_molded) only computes
IPC-7351 lands from the body, so the vendor lands are drawn here. Names follow KiCad's own
"R_0603_1608Metric_Pad<w>x<h>mm" scheme for non-IPC lands; both share the 3D model
R_0603_1608Metric.step (KLC F9.3: the pad suffix does not change the model).

Usage: ~/.cache/dropout/klt-venv/bin/python generators/custom/R_0603_1608Metric_NTC.py

Sources (archived in dropout-vendor-docs):
- Murata NCU18 (NCU18XH103F6SRB): catalog R44E (Mar. 6, 2020) p. 13 "Standard Land Pattern
  Dimensions", NCU18 reflow: gap a 0.6-1.2, land length b 0.6-0.7, land width c 0.6-0.8.
  Body 1.6 x 0.8 x 0.8 (each +/-0.15), terminations 0.2-0.6 (R44E p. 12).
- TDK NTCG 1608 (NTCG163JF103FTDS/FT1S/FT1H): automotive NTCG catalog (20260731) p. 13
  "Set of land dimensions", 1608: gap A 0.60-0.80, land length B 0.60-0.80, land width C
  0.60-0.80; TDK's product pages give 0.7 +/-0.1 for all three. Body 1.6 x 0.8 x 0.8 (+/-0.1),
  terminations 0.2 min (catalog p. 10, data sheets).
  One land, 0.7 x 0.7 pads with a 0.7 gap, is inside both Murata's and TDK's ranges, so the two
  share R_0603_1608Metric_Pad0.7x0.7mm.
- Vishay NTCS0603E3 (NTCS0603E3103FMT): data sheet doc 29056 (rev. 29-Sep-2026) p. 2
  "Recommended solder land pattern dimensions": 0.8 (x) x 1.0 (y) pads, 2.4 outer span, so a
  0.8 gap. Body 1.6 x 0.8 x 0.8 (+/-0.15), terminations 0.2 min (L2, L3).
"""
import math

from fplib import (BODY, CRT_CLR, CRT_W, FAB_W, METAL, SILK_PAD, SILK_W, fab_ref, footprint_text, line,
                   model_ref, rect, smd_pad, text, up, write_footprint, write_model)

LIB = "DropOut_Resistor_SMD"
BODY_L, BODY_W, BODY_H, TERM = 1.6, 0.8, 0.8, 0.3
MODEL = "R_0603_1608Metric"

# name: (pad length x, pad width y, gap between pads, description, tags)
PARTS = {
    "R_0603_1608Metric_Pad0.7x0.7mm": (0.7, 0.7, 0.7,
        "Chip NTC thermistor 0603 (1608 Metric), manufacturer reflow land 0.7x0.7mm pads, 0.7mm gap, "
        "inside the recommendations for Murata NCU18 (catalog R44E p. 13) and TDK NTCG 1608 "
        "(automotive NTCG catalog p. 13), https://product.tdk.com/system/files/dam/doc/product/sensor/"
        "ntc/chip-ntc-thermistor/catalog/tpd_automotive_ntc-thermistor_ntcg_en.pdf",
        "resistor thermistor NTC 0603 1608 Murata NCU18 TDK NTCG163"),
    "R_0603_1608Metric_Pad0.8x1.0mm": (0.8, 1.0, 0.8,
        "Chip NTC thermistor 0603 (1608 Metric), Vishay NTCS0603E3 recommended solder land 0.8x1.0mm "
        "pads, 2.4mm outer span (data sheet doc 29056 p. 2), https://www.vishay.com/docs/29056/ntcs0603e3t.pdf",
        "resistor thermistor NTC 0603 1608 Vishay NTCS0603E3"),
}


def footprint(name, pad_l, pad_w, gap):
    cx = (gap + pad_l) / 2                      # pad centre
    xi, xo = gap / 2, gap / 2 + pad_l           # pad inner and outer edge
    crt_x = up(max(xo, BODY_L / 2) + CRT_CLR, 0.05)
    crt_y = up(max(pad_w, BODY_W) / 2 + CRT_CLR, 0.05)
    # Silk: a line above and below the body between the pads, as KiCad's stock chip footprints,
    # kept SILK_PAD from the pad corners.
    sy = max(BODY_W, pad_w) / 2 + SILK_W
    dy = sy - pad_w / 2
    need = SILK_PAD + SILK_W / 2
    sx = BODY_L / 2 if dy >= need else xi - math.sqrt(need ** 2 - dy ** 2)
    return [
        text("Reference", "REF**", -crt_y - 0.68, "F.SilkS"),
        text("Value", name, crt_y + 0.68, "F.Fab"),
        line(-sx, -sy, sx, -sy, "F.SilkS", SILK_W), line(-sx, sy, sx, sy, "F.SilkS", SILK_W),
        rect(-crt_x, -crt_y, crt_x, crt_y, "F.CrtYd", CRT_W),
        rect(-BODY_L / 2, -BODY_W / 2, BODY_L / 2, BODY_W / 2, "F.Fab", FAB_W),
        fab_ref(0.5),
        smd_pad(1, -cx, 0, pad_l, pad_w),
        smd_pad(2, cx, 0, pad_l, pad_w),
        model_ref(LIB, MODEL),
    ]


def model():
    import cadquery as cq
    box = lambda x0, x1, w, z0, z1: cq.Workplane("XY").box(x1 - x0, w, z1 - z0) \
        .translate(((x0 + x1) / 2, 0, (z0 + z1) / 2))
    body = box(-BODY_L / 2 + TERM, BODY_L / 2 - TERM, BODY_W - 0.02, 0.01, BODY_H - 0.01)
    terms = box(-BODY_L / 2, -BODY_L / 2 + TERM, BODY_W, 0.0, BODY_H) \
        .union(box(BODY_L / 2 - TERM, BODY_L / 2, BODY_W, 0.0, BODY_H))
    return [(body, BODY), (terms, METAL)]


if __name__ == "__main__":
    for name, (pad_l, pad_w, gap, descr, tags) in PARTS.items():
        print("footprint ", write_footprint(LIB, name, footprint_text(name, descr, tags, footprint(name, pad_l, pad_w, gap))))
    print("3D model  ", write_model(LIB, MODEL, model()))
