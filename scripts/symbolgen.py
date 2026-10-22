#!/usr/bin/env python3
"""Build a DropOut symbol from a part definition and a pin table, and write it into its library.

Usage:
  python3 scripts/symbolgen.py parts/<MPN>/part.yaml            # writes symbols/<Library>.kicad_sym
  python3 scripts/symbolgen.py parts/<MPN>/part.yaml --out x.kicad_sym

part.yaml:
  library: DropOut_MCU
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

Pins with the same unit, side, name and a power type are drawn as one KiCad 10 native pin
stack (number "[A1,B2,...]", KLC S4.3). Bodies are sized from pin-name lengths and centred on
the origin (KLC S3.1); pins are 200 mil long on a 100 mil grid with 20 mil name offset (S3.6).
The result is normalised with `kicad-cli sym upgrade` when kicad-cli is available.
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
from collections import OrderedDict, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_symbol_fields import top_level_symbols  # noqa: E402

G = 2.54          # 100 mil grid
PIN_LEN = 5.08    # 200 mil pins, as KiCad's stock MCU symbols
TB_PITCH = 5.08   # top/bottom pins 200 mil apart, room for vertical names
CHAR_W = 1.27     # conservative pin-name glyph width at 1.27 mm text
STACK_LABEL_W = 1.8  # room per number in a native stack's drawn number list
STACKABLE = {"power_in", "power_out"}
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


def ball_key(n):
    m = re.match(r"([A-Z]*)(\d+)$", n)
    return (m.group(1), int(m.group(2))) if m else (n, 0)


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


def place_side(pins, pitch):
    """Group stackable pins and assign slots. Returns list of (slot, [pins]).

    KiCad draws a native stack's pin numbers as a list beside the pin, extending towards
    lower slots (left on top/bottom edges, up on left/right edges), so a stack reserves
    enough slots before its pin for that list.
    """
    groups = OrderedDict()
    for p in pins:
        key = (p["name"], p["type"]) if p["type"] in STACKABLE else ("#", p["number"])
        groups.setdefault(key, []).append(p)
    placed, used = [], set()
    for g in groups.values():
        span = max(1, math.ceil(len(g) * STACK_LABEL_W / pitch)) if len(g) > 1 else 1
        slot = g[0]["slot"]
        if slot is None:
            start = next(i for i in range(len(used) + span + 1)
                         if not used & set(range(i, i + span)))
            slot = start + span - 1
        elif used & set(range(slot - span + 1, slot + 1)):
            sys.exit(f"symbolgen: slot {slot} on one side is taken ({g[0]['name']})")
        used |= set(range(slot - span + 1, slot + 1))
        placed.append((slot, g))
    return placed


def pin_sexpr(group, x, y, rot):
    p = group[0]
    nums = sorted((q["number"] for q in group), key=ball_key)
    number = nums[0] if len(nums) == 1 else "[" + ",".join(nums) + "]"
    s = [f'\t\t\t(pin {p["type"]} line', f"\t\t\t\t(at {fmt(x)} {fmt(y)} {rot})",
         f"\t\t\t\t(length {fmt(PIN_LEN)})",
         f'\t\t\t\t(name "{esc(p["name"])}" (effects (font (size 1.27 1.27))))',
         f'\t\t\t\t(number "{esc(number)}" (effects (font (size 1.27 1.27))))']
    s += [f'\t\t\t\t(alternate "{esc(a)}" {t} line)' for a, t in p["alts"]]
    s.append("\t\t\t)")
    return "\n".join(s)


def build_unit(pins):
    sides = {s: place_side([p for p in pins if p["side"] == s], G if s in "LR" else TB_PITCH)
             for s in "LRTB"}
    rows = max([slot + 1 for s in "LR" for slot, _ in sides[s]] or [1])
    cols = max([slot + 1 for s in "TB" for slot, _ in sides[s]] or [0])
    width = lambda s: max((text_w(g[0]["name"]) for _, g in sides[s]), default=0)
    # half width: names on both sides plus a gap, and room for the top/bottom pin row
    hw = snap_up(max((width("L") + width("R") + 2 * G) / 2, ((cols - 1) * TB_PITCH + 2 * G) / 2, 2 * G))
    top = G * math.ceil((rows - 1) / 2)  # y of the first L/R row; rows centred on the origin
    hh = max(top + G, snap_up((width("T") + width("B") + 2 * G) / 2), 2 * G)
    out = [f"\t\t\t(rectangle (start {fmt(-hw)} {fmt(hh)}) (end {fmt(hw)} {fmt(-hh)})\n"
           f"\t\t\t\t(stroke (width 0.254) (type default)) (fill (type background)))"]
    for slot, g in sides["L"]:
        out.append(pin_sexpr(g, -hw - PIN_LEN, top - slot * G, 0))
    for slot, g in sides["R"]:
        out.append(pin_sexpr(g, hw + PIN_LEN, top - slot * G, 180))
    x0 = -(cols - 1) * TB_PITCH / 2
    for slot, g in sides["T"]:
        out.append(pin_sexpr(g, x0 + slot * TB_PITCH, hh + PIN_LEN, 270))
    for slot, g in sides["B"]:
        out.append(pin_sexpr(g, x0 + slot * TB_PITCH, -hh - PIN_LEN, 90))
    return out, hh


def build_symbol(part, pins):
    name = part["name"]
    order = part.get("units") or list(OrderedDict.fromkeys(p["unit"] for p in pins))
    missing = {p["unit"] for p in pins} - set(order)
    if missing:
        sys.exit(f"symbolgen: units {sorted(missing)} not listed in part.yaml 'units'")
    units = [build_unit([p for p in pins if p["unit"] == u]) for u in order]
    max_hh = max(hh for _, hh in units)
    lines = [f'\t(symbol "{esc(name)}"', "\t\t(pin_names (offset 0.508))", "\t\t(exclude_from_sim no)",
             "\t\t(in_bom yes)", "\t\t(on_board yes)"]
    for k, v in part["fields"].items():
        y = {"Reference": max_hh + G, "Value": -max_hh - G}.get(k, 0)
        hide = "" if k in VISIBLE else "\n\t\t\t(hide yes)"
        lines.append(f'\t\t(property "{esc(k)}" "{esc(str(v))}"\n\t\t\t(at 0 {fmt(y)} 0){hide}\n'
                     f"\t\t\t(effects (font (size 1.27 1.27)))\n\t\t)")
    for i, (body, _) in enumerate(units, start=1):
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
    out = Path(args.out) if args.out else REPO / "symbols" / f"{part['library']}.kicad_sym"
    write_library(out, part["name"], sym)
    units = len(part.get("units") or {p["unit"] for p in pins})
    print(f"{part['library']}:{part['name']}: {len(pins)} pins in {units} unit(s) -> {out}")


if __name__ == "__main__":
    main()
