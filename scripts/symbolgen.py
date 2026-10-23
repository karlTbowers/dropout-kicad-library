#!/usr/bin/env python3
"""Build a DropOut symbol from a part definition and a pin table, and write it into its library.

Usage:
  python3 scripts/symbolgen.py parts/<MPN>/part.yaml            # writes symbols/<Library>.kicad_sym
  python3 scripts/symbolgen.py parts/<MPN>/part.yaml --out x.kicad_sym

part.yaml:
  library: DropOut_MCU_NXP
  name: S32K344EHT1MMMST                 # symbol name = MPN (KLC S2, DropOut atomic parts)
  pins: pins.csv                         # relative to part.yaml
  fields:                                # in order; Reference and Value are shown, the rest hidden
    Reference: U
    Value: S32K344EHT1MMMST
    Footprint: DropOut_Package_BGA:...
    Datasheet: https://...
    Description: ...
    ki_keywords: ...
    ki_fp_filters: ...
    Manufacturer: ...
    MPN: ...
    DigiKey_PN: ...
    Mouser_PN: ...
    # optional: Temperature_Grade, Notes, Reference_Manual
  units: [Power, PTA, ...]               # optional unit order; default: order of first use in the CSV
  style: testpoint                       # optional graphic style for small parts (see STYLES)
  in_bom: false                          # optional, default true: false for a part with nothing to
  in_pos_files: false                    #   buy or place (a bare-copper test pad)

pins.csv columns (header row required):
  number      pin/ball number as on the footprint
  name        pin name; active-low as ~{NAME} (KLC S4.7)
  type        KiCad electrical type: input, output, bidirectional, tri_state, passive, free,
              unspecified, power_in, power_out, open_collector, open_emitter, no_connect
  unit        unit label (one unit per distinct label)
  side        L, R, T or B (inputs left, outputs right, power top, ground bottom: KLC S3/S4)
  slot        optional position on that side, 0 = top (L/R) or left (T/B); gaps are kept.
              Default: next free slot in file order.
  alternates  optional, ";"-separated NAME or NAME:type (KiCad alternate pin functions)

Every package pin gets its own visible pin: DropOut never combines pins (no native pin stacks,
no hidden pins stacked under a visible one), even where KLC S4.3 would allow it. Bodies are
sized from pin-name lengths and centred on the origin (KLC S3.1); pins are 200 mil long on a
100 mil grid with 20 mil name offset (S3.6). No text may overprint other text (handbook D-47):
symbolgen refuses to write a symbol that check_symbol_text.py would reject. The result is normalised with `kicad-cli sym upgrade` when kicad-cli is available.
"""
import argparse
import csv
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import OrderedDict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_symbol_fields import top_level_symbols  # noqa: E402
from check_symbol_text import check_symbol, parse  # noqa: E402

G = 2.54          # 100 mil grid
PIN_LEN = 5.08    # 200 mil pins, as KiCad's stock MCU symbols
TB_PITCH = 2.54   # top/bottom pins 100 mil apart, as KiCad's stock MCU symbols
CHAR_W = 1.27     # conservative pin-name glyph width at 1.27 mm text
TYPES = {"input", "output", "bidirectional", "tri_state", "passive", "free", "unspecified",
         "power_in", "power_out", "open_collector", "open_emitter", "no_connect"}
VISIBLE = {"Reference", "Value"}


def fmt(v):
    v = round(v, 4)
    return str(int(v)) if v == int(v) else f"{v:.4f}".rstrip("0")


def esc(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


def text_w(name):
    return len(re.sub(r"[~{}]", "", name)) * CHAR_W


def snap_up(v, step=G):
    return math.ceil(v / step - 1e-9) * step


def load_yaml(path):
    try:
        import yaml
    except ImportError:
        sys.exit("symbolgen: PyYAML is required (run scripts/setup_tools.sh, then use its Python)")
    return yaml.safe_load(Path(path).read_text())


def read_pins(path):
    pins = []
    with open(path, newline="") as f:
        for i, row in enumerate(csv.DictReader(f), start=2):
            row = {k: (v or "").strip() for k, v in row.items()}
            if row["type"] not in TYPES:
                sys.exit(f"{path}:{i}: unknown pin type '{row['type']}'")
            if row["side"] not in ("L", "R", "T", "B"):
                sys.exit(f"{path}:{i}: side must be L, R, T or B")
            alts = []
            for a in filter(None, (x.strip() for x in row.get("alternates", "").split(";"))):
                name, _, t = a.partition(":")
                alts.append((name, t or "bidirectional"))
            pins.append({"number": row["number"], "name": row["name"], "type": row["type"],
                         "unit": row["unit"], "side": row["side"],
                         "slot": int(row["slot"]) if row.get("slot") else None, "alts": alts})
    numbers = [p["number"] for p in pins]
    dup = {n for n in numbers if numbers.count(n) > 1}
    if dup:
        sys.exit(f"{path}: duplicate pin numbers {sorted(dup)}")
    return pins


def place_side(pins):
    """Assign each pin a slot on its side: its own `slot`, else the next free one in file order.
    Returns list of (slot, pin)."""
    placed, used = [], set()
    for p in pins:
        slot = p["slot"]
        if slot is None:
            slot = next(i for i in range(len(used) + 1) if i not in used)
        elif slot in used:
            sys.exit(f"symbolgen: slot {slot} on one side is taken ({p['name']} {p['number']})")
        used.add(slot)
        placed.append((slot, p))
    return placed


def pin_sexpr(p, x, y, rot, length=PIN_LEN):
    s = [f'\t\t\t(pin {p["type"]} line', f"\t\t\t\t(at {fmt(x)} {fmt(y)} {rot})",
         f"\t\t\t\t(length {fmt(length)})",
         f'\t\t\t\t(name "{esc(p["name"])}" (effects (font (size 1.27 1.27))))',
         f'\t\t\t\t(number "{esc(p["number"])}" (effects (font (size 1.27 1.27))))']
    s += [f'\t\t\t\t(alternate "{esc(a)}" {t} line)' for a, t in p["alts"]]
    s.append("\t\t\t)")
    return "\n".join(s)


def build_unit(pins):
    sides = {s: place_side([p for p in pins if p["side"] == s]) for s in "LRTB"}
    rows = max([slot + 1 for s in "LR" for slot, _ in sides[s]] or [1])
    cols = max([slot + 1 for s in "TB" for slot, _ in sides[s]] or [0])
    width = lambda s: max((text_w(p["name"]) for _, p in sides[s]), default=0)
    # half width: names on both sides plus a gap, and room for the top/bottom pin row
    hw = snap_up(max((width("L") + width("R") + 2 * G) / 2, ((cols - 1) * TB_PITCH + 2 * G) / 2, 2 * G))
    top = G * math.ceil((rows - 1) / 2)  # y of the first L/R row; rows centred on the origin
    # Top/bottom pin names are drawn vertically inside the body; keep them clear of the
    # left/right pin rows (whose names can reach the middle) with a band above and below.
    band_t = width("T") + G if sides["T"] else 0
    band_b = width("B") + G if sides["B"] else 0
    hh = snap_up(max(top + G + max(band_t, band_b), 2 * G))
    out = [f"\t\t\t(rectangle (start {fmt(-hw)} {fmt(hh)}) (end {fmt(hw)} {fmt(-hh)})\n"
           f"\t\t\t\t(stroke (width 0.254) (type default)) (fill (type background)))"]
    for slot, p in sides["L"]:
        out.append(pin_sexpr(p, -hw - PIN_LEN, top - slot * G, 0))
    for slot, p in sides["R"]:
        out.append(pin_sexpr(p, hw + PIN_LEN, top - slot * G, 180))
    x0 = -snap_up((cols - 1) * TB_PITCH / 2 - 1e-9, G) if cols else 0  # first top/bottom pin, on grid
    for slot, p in sides["T"]:
        out.append(pin_sexpr(p, x0 + slot * TB_PITCH, hh + PIN_LEN, 270))
    for slot, p in sides["B"]:
        out.append(pin_sexpr(p, x0 + slot * TB_PITCH, -hh - PIN_LEN, 90))
    # Field clearance above/below this unit: past the top/bottom pins and their numbers
    top_extent = hh + (PIN_LEN if sides["T"] else 0)
    bottom_extent = hh + (PIN_LEN if sides["B"] else 0)
    return out, top_extent, bottom_extent


def poly(points, fill="none", width=0.254):
    pts = " ".join(f"(xy {fmt(x)} {fmt(y)})" for x, y in points)
    return (f"\t\t\t(polyline (pts {pts})\n"
            f"\t\t\t\t(stroke (width {width}) (type default)) (fill (type {fill})))")


def two_pin(pins, graphic):
    """A horizontal two-terminal symbol: pin '1'-side on the left, the other on the right."""
    left = [p for p in pins if p["side"] == "L"]
    right = [p for p in pins if p["side"] == "R"]
    if len(pins) != 2 or len(left) != 1 or len(right) != 1:
        sys.exit("symbolgen: two-terminal styles need exactly one L and one R pin")
    out = graphic + [pin_sexpr(left[0], -2 * G, 0, 0, length=G), pin_sexpr(right[0], 2 * G, 0, 180, length=G)]
    return out, G + 0.27, G + 0.27


def style_tvs_bidirectional(pins):
    # Two opposing diode triangles and a Z-shaped breakdown bar (as KiCad's Device:D_TVS)
    g = [poly([(-2.54, 1.27), (-2.54, -1.27), (0, 0), (-2.54, 1.27)]),
         poly([(2.54, 1.27), (2.54, -1.27), (0, 0), (2.54, 1.27)]),
         poly([(-0.508, 1.778), (0, 1.27), (0, -1.27), (0.508, -1.778)])]
    return two_pin(pins, g)


def style_crystal_gnd24(pins):
    """Four-pin crystal with a grounded lid (as KiCad's Device:Crystal_GND24), but with both lid
    pins drawn as separate visible pins: crystal pins on L/R, the two lid pins on B."""
    left = [p for p in pins if p["side"] == "L"]
    right = [p for p in pins if p["side"] == "R"]
    bottom = sorted((p for p in pins if p["side"] == "B"), key=lambda p: p["slot"] or 0)
    if len(pins) != 4 or len(left) != 1 or len(right) != 1 or len(bottom) != 2:
        sys.exit("symbolgen: crystal_gnd24 needs one L, one R and two B pins")
    # quartz drawn as a closed polyline: a rectangle would read as the symbol body (KLC S3.3)
    g = [poly([(-1.143, 2.54), (1.143, 2.54), (1.143, -2.54), (-1.143, -2.54), (-1.143, 2.54)], fill="background"),
         poly([(-2.032, -1.27), (-2.032, 1.27)], width=0.508),          # electrodes
         poly([(2.032, -1.27), (2.032, 1.27)], width=0.508),
         poly([(-2.54, 0), (-2.032, 0)]), poly([(2.032, 0), (2.54, 0)]),
         poly([(-2.54, 2.286), (-2.54, 3.556), (2.54, 3.556), (2.54, 2.286)]),     # lid
         poly([(-2.54, -2.286), (-2.54, -5.08), (2.54, -5.08), (2.54, -2.286)])]
    out = g + [pin_sexpr(left[0], -2 * G, 0, 0, length=G), pin_sexpr(right[0], 2 * G, 0, 180, length=G),
               pin_sexpr(bottom[0], -G, -3 * G, 90, length=G), pin_sexpr(bottom[1], G, -3 * G, 90, length=G)]
    return out, 3.556 + 0.27, 3 * G


def arc(start, mid, end, width=0.254):
    return (f"\t\t\t(arc (start {fmt(start[0])} {fmt(start[1])}) (mid {fmt(mid[0])} {fmt(mid[1])}) "
            f"(end {fmt(end[0])} {fmt(end[1])})\n\t\t\t\t(stroke (width {width}) (type default)) (fill (type none)))")


def dot(x, y):
    return (f"\t\t\t(circle (center {fmt(x)} {fmt(y)}) (radius 0.254)\n"
            f"\t\t\t\t(stroke (width 0) (type default)) (fill (type outline)))")


def style_cmc_4pin(pins):
    """Two-line common mode choke, drawn as KiCad's Filter:Choke_CommonMode_FerriteCore_1234: one
    winding on top (L slot 0 to R slot 0), one below (L slot 1 to R slot 1), dashed ferrite core,
    winding-start dots on the left. Pin numbers come from the part's own pins.csv."""
    side = lambda s: sorted((p for p in pins if p["side"] == s), key=lambda p: p["slot"] or 0)
    left, right = side("L"), side("R")
    if len(pins) != 4 or len(left) != 2 or len(right) != 2:
        sys.exit("symbolgen: cmc_4pin needs two L and two R pins (slot 0 top, slot 1 bottom)")
    g = [dot(-2.794, 1.27), dot(-2.794, -1.27),
         poly([(-2.54, 2.032), (-2.54, 2.54)], width=0), poly([(2.54, 2.54), (2.54, 2.032)], width=0),
         poly([(-2.54, -2.032), (-2.54, -2.54)], width=0), poly([(2.54, -2.032), (2.54, -2.54)], width=0)]
    for i in range(5):                                   # five turns per winding
        x0, x1 = -2.54 + i * 1.016, -1.524 + i * 1.016
        g.append(arc((x1, 2.032), ((x0 + x1) / 2, 1.5262), (x0, 2.032)))
        g.append(arc((x0, -2.032), ((x0 + x1) / 2, -1.5262), (x1, -2.032)))
    for i in range(6):                                   # dashed core between the windings
        x = -2.794 + i * 1.016
        g.append(poly([(x, 0.381), (x + 0.508, 0.381)], width=0))
        g.append(poly([(x, -0.381), (x + 0.508, -0.381)], width=0))
    out = g + [pin_sexpr(left[0], -2 * G, G, 0, length=G), pin_sexpr(right[0], 2 * G, G, 180, length=G),
               pin_sexpr(left[1], -2 * G, -G, 0, length=G), pin_sexpr(right[1], 2 * G, -G, 180, length=G)]
    return out, G + 0.27, G + 0.27


def style_thermistor_ntc(pins):
    """NTC thermistor, KiCad's Device:Thermistor_NTC turned horizontal (x, y -> y, -x): resistor
    body (a closed polyline, not a body rectangle, KLC S3.3) with the diagonal, the two opposed
    arrows and the "t°" mark above it."""
    g = [poly([(-2.54, 1.016), (2.54, 1.016), (2.54, -1.016), (-2.54, -1.016), (-2.54, 1.016)], fill="background"),
         poly([(2.54, 1.778), (1.524, 1.778), (-1.524, -1.778), (-2.54, -1.778)]),
         poly([(-3.683, 2.54), (-1.397, 2.54), (-2.159, 2.794), (-2.159, 2.286), (-1.397, 2.54), (-1.651, 2.54)]),
         poly([(-1.397, 1.778), (-3.683, 1.778), (-2.921, 2.032), (-2.921, 1.524), (-3.683, 1.778), (-3.429, 1.778)]),
         poly([(2.159, 2.54), (2.794, 2.54)]),
         arc((2.413, 3.175), (2.3165, 3.0506), (2.159, 3.048)),
         arc((2.794, 3.048), (2.9736, 2.9736), (3.048, 2.794)),
         arc((3.048, 2.794), (2.9736, 2.6144), (2.794, 2.54)),
         arc((2.54, 2.794), (2.6144, 2.9736), (2.794, 3.048)),
         arc((1.905, 2.794), (1.9794, 2.9736), (2.159, 3.048)),
         arc((2.159, 2.54), (1.9794, 2.6144), (1.905, 2.794)),
         arc((2.794, 2.159), (2.5608, 2.434), (2.54, 2.794))]
    out, _, bottom = two_pin(pins, g)
    return out, 3.175 + 0.27, bottom



def style_testpoint(pins):
    """One-pin test point drawn as KiCad's Connector:TestPoint: a circle above a pin pointing down
    to its connection point at the origin."""
    if len(pins) != 1:
        sys.exit("symbolgen: testpoint needs exactly one pin")
    g = [f"\t\t\t(circle (center 0 3.302) (radius 0.762)\n"
         f"\t\t\t\t(stroke (width 0) (type default)) (fill (type none)))"]
    return g + [pin_sexpr(pins[0], 0, 0, 90, length=G)], 4.318, 0


STYLES = {"tvs_bidirectional": style_tvs_bidirectional, "crystal_gnd24": style_crystal_gnd24,
          "cmc_4pin": style_cmc_4pin, "testpoint": style_testpoint,
          "thermistor_ntc": style_thermistor_ntc}
# Reference and Value positions where the default (above and below the body) doesn't fit:
# a test point's connection point is at the bottom, so both go above it, as on KiCad's TestPoint
STYLE_FIELD_Y = {"testpoint": {"Reference": 6.858, "Value": 5.08}}
# Pin numbers are shown where the package has more than two terminals (as KiCad's stock symbols)
STYLE_SHOW_NUMBERS = {"crystal_gnd24", "cmc_4pin"}


def build_symbol(part, pins):
    name = part["name"]
    order = part.get("units") or list(OrderedDict.fromkeys(p["unit"] for p in pins))
    missing = {p["unit"] for p in pins} - set(order)
    if missing:
        sys.exit(f"symbolgen: units {sorted(missing)} not listed in part.yaml 'units'")
    style = part.get("style")
    if style:
        if style not in STYLES:
            sys.exit(f"symbolgen: unknown style '{style}' (have {sorted(STYLES)})")
        units = [STYLES[style](pins)]
        head = "\t\t(pin_names (offset 1.016) (hide yes))"
        if style not in STYLE_SHOW_NUMBERS:
            head = "\t\t(pin_numbers (hide yes))\n" + head
    else:
        units = [build_unit([p for p in pins if p["unit"] == u]) for u in order]
        head = "\t\t(pin_names (offset 0.508))"
    top = max(t for _, t, _ in units)
    bottom = max(b for _, _, b in units)
    yn = lambda key: "yes" if part.get(key, True) else "no"
    lines = [f'\t(symbol "{esc(name)}"', head, "\t\t(exclude_from_sim no)",
             f"\t\t(in_bom {yn('in_bom')})", "\t\t(on_board yes)", f"\t\t(in_pos_files {yn('in_pos_files')})"]
    field_y = {"Reference": top + G, "Value": -bottom - G, **STYLE_FIELD_Y.get(style, {})}
    for k, v in part["fields"].items():
        y = field_y.get(k, 0)
        hide = "" if k in VISIBLE else "\n\t\t\t(hide yes)"
        lines.append(f'\t\t(property "{esc(k)}" "{esc(str(v))}"\n\t\t\t(at 0 {fmt(y)} 0){hide}\n'
                     f"\t\t\t(effects (font (size 1.27 1.27)))\n\t\t)")
    for i, (body, _, _) in enumerate(units, start=1):
        lines.append(f'\t\t(symbol "{esc(name)}_{i}_1"')
        lines.extend(body)
        lines.append("\t\t)")
    lines += ["\t\t(embedded_fonts no)", "\t)"]
    return "\n".join(lines)


def kicad_cli():
    for c in (os.environ.get("KICAD_CLI"), shutil.which("kicad-cli"),
              "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"):
        if c and Path(c).exists():
            return c
    return None


def write_library(lib_path, name, symbol_text):
    header = ('(kicad_symbol_lib\n\t(version 20251024)\n\t(generator "kicad_symbol_editor")\n'
              '\t(generator_version "10.0")\n')
    existing = {}
    if lib_path.exists():
        existing = {n: "\t" + body for n, body in top_level_symbols(lib_path.read_text(encoding="utf-8"))}
    existing[name] = symbol_text
    text = header + "\n".join(existing[n] for n in sorted(existing)) + "\n)\n"
    cli = kicad_cli()
    if not cli:
        lib_path.write_text(text)
        print("symbolgen: kicad-cli not found; library written without normalisation")
        return
    with tempfile.TemporaryDirectory() as td:
        raw, norm = Path(td) / "raw.kicad_sym", Path(td) / "norm.kicad_sym"
        raw.write_text(text)
        subprocess.run([cli, "sym", "upgrade", "--force", str(raw), "-o", str(norm)],
                       check=True, capture_output=True)
        shutil.copyfile(norm, lib_path)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("part_yaml")
    ap.add_argument("--out", help="library file to write (default symbols/<library>.kicad_sym)")
    args = ap.parse_args()

    part_path = Path(args.part_yaml).resolve()
    part = load_yaml(part_path)
    pins = read_pins(part_path.parent / part.get("pins", "pins.csv"))
    sym = build_symbol(part, pins)
    overprints = check_symbol(parse(sym)[0])
    if overprints:
        sys.exit("symbolgen: text overprints (D-47); move pins or fix the layout:\n  " + "\n  ".join(overprints))
    out = Path(args.out) if args.out else REPO / "symbols" / f"{part['library']}.kicad_sym"
    write_library(out, part["name"], sym)
    units = len(part.get("units") or {p["unit"] for p in pins})
    print(f"{part['library']}:{part['name']}: {len(pins)} pins in {units} unit(s) -> {out}")


if __name__ == "__main__":
    main()
