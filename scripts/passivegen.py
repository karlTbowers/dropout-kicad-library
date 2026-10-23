#!/usr/bin/env python3
"""Generate the part definitions of chip resistors and MLCCs from one table, then their symbols.

Usage:
  python3 scripts/passivegen.py                 # parts/passives.yaml -> parts/<MPN>/, symbols
  python3 scripts/passivegen.py --no-symbols    # write parts/<MPN>/ only
  python3 scripts/passivegen.py --mpn GCM155R71C104KA55D

parts/passives.yaml holds `families` (what an ordering code family has in common: library,
manufacturer, datasheet, construction, temperature range, ...) and `parts` (one row per orderable
MPN: family, value, size and its ratings, distributor PNs and a dated price/stock observation).
Each row becomes an ordinary parts/<MPN>/part.yaml + pins.csv (as every other DropOut part, so
symbolgen.py, the catalog and reviewers see nothing special), and symbolgen.py builds the symbol.
Edit the table, never the generated part.yaml files.

Layout (LAYOUT below, or --layout): "mpn" keeps Value = MPN as KLC S6.2 requires. "d45" shows the
short value (`10k`, `100nF`, handbook rule D-45), a row with the ratings and case size, and the
MPN in smaller text; it needs KLC exceptions (S6.2, S3.2) first. `--out DIR` writes a preview
(parts and libraries) outside the repo.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TABLE = REPO / "parts" / "passives.yaml"
# Symbol layout. "mpn": Value = MPN, only Reference and Value shown (KLC as it stands).
# "d45": Value = short value (10k, 100nF) with the ratings and case size on a row below it and the
# MPN under that in smaller text. It needs KLC exceptions first: S6.2 (Value is not the symbol
# name; the rating and Case fields) and S3.2 (MPN text smaller than 50 mil).
LAYOUT = "mpn"
ROWS = {"Reference": 2.858, "Value": 0.953, "ratings": -0.953, "MPN": -2.794}  # y of each row, mm
X0 = 2.54            # rows start right of the body (Device:C plates end at 2.032)
CHAR = 1.27          # advance per character, as scripts/check_symbol_text.py measures text
MPN_SIZE = 1.0       # MPN text height, mm
RATING_ROW = {"R": ["Tolerance", "Voltage", "Case"], "C": ["Voltage", "Dielectric", "Tolerance", "Case"]}

SIZES = {"0402": "1005", "0603": "1608", "0805": "2012", "1206": "3216", "1210": "3225"}
KIND = {
    "R": {"library": "DropOut_Resistor", "fp_lib": "DropOut_Resistor_SMD", "style": "resistor",
          "rating_fields": ["Tolerance", "Power", "Voltage"]},
    "C": {"library": "DropOut_Capacitor", "fp_lib": "DropOut_Capacitor_SMD", "style": "capacitor",
          "rating_fields": ["Voltage", "Tolerance", "Dielectric"]},
}
UNIT_WORDS = {"R": "Ω", "k": "kΩ", "M": "MΩ"}


def load_yaml(path):
    import yaml
    return yaml.safe_load(Path(path).read_text())


def pretty_value(kind, value):
    """'4.7k' -> '4.7 kΩ', '49.9R' -> '49.9 Ω', '100nF' -> '100 nF', '4.7uF' -> '4.7 µF'."""
    if kind == "R":
        if value == "0R":
            return "0 Ω jumper"
        num, unit = value[:-1], value[-1]
        return f"{num} {UNIT_WORDS[unit]}"
    num, unit = value[:-2], value[-2:]
    return f"{num} {unit.replace('uF', 'µF')}"


def description(row, fam):
    kind, size = fam["kind"], row["size"]
    pkg = f"{size} ({SIZES[size]} metric)"
    if kind == "R":
        if row["value"] == "0R":
            body = f"{fam['construction']} chip jumper, 0 Ω, {row['current']} rated"
        else:
            body = f"{fam['construction']} chip resistor, {pretty_value('R', row['value'])} {row['tolerance']}, " \
                   f"{row['power']}, {row['voltage']}, {row['tcr']}"
    else:
        body = f"{fam['construction']}, {pretty_value('C', row['value'])} {row['tolerance']}, {row['voltage']}, {row['dielectric']}"
    return f"{fam['manufacturer']} {fam['series']} {body}, {fam['grade']}, {fam['temperature']}, {pkg}"


def compact(v):
    """'50 V' -> '50V', '1/16 W' -> '1/16W': ratings as written on a schematic (D-45 style)."""
    return str(v).replace(" ", "")


def field_layout(fields, kind):
    """Rows beside the body: Reference, Value, the ratings and case size, then the MPN (small)."""
    lay = {"Reference": {"at": [X0, ROWS["Reference"]]}, "Value": {"at": [X0, ROWS["Value"]]},
           "MPN": {"at": [X0, ROWS["MPN"]], "size": MPN_SIZE, "show": True}}
    x = X0
    for f in RATING_ROW[kind]:
        if f in fields:
            lay[f] = {"at": [round(x, 3), ROWS["ratings"]], "show": True}
            x += (len(str(fields[f])) + 1) * CHAR
    return lay


def build_part(row, fam, layout):
    kind = KIND[fam["kind"]]
    size = row["size"]
    fp = f"{fam['kind']}_{size}_{SIZES[size]}Metric"
    fields = {
        "Reference": fam["kind"],
        "Value": row["mpn"] if layout == "mpn" else row["value"],
        "Footprint": f"{kind['fp_lib']}:{fp}",
        "Datasheet": row.get("datasheet", fam["datasheet"]),
        "Description": description(row, fam),
        "ki_keywords": fam["keywords"],
        "ki_fp_filters": fp.replace("_", "?") + "*",  # KLC S5.2: escape "_" in filters
        "Manufacturer": fam["manufacturer"],
        "MPN": row["mpn"],
        "DigiKey_PN": row["digikey"],
        "Mouser_PN": row["mouser"],
        "Temperature_Grade": f"{fam['grade']}, {fam['temperature']}",
    }
    # Rating fields (handbook rule D-45); a jumper has none (its current rating is in Description)
    if row["value"] != "0R":
        for f in kind["rating_fields"]:
            fields[f] = compact(row[f.lower()])
    if layout == "d45":
        fields["Case"] = row["size"]
    notes = " ".join(n for n in (row.get("notes"), fam.get("notes")) if n)
    if notes:
        fields["Notes"] = notes
    return fields


def write_part(row, fam, layout, out_dir):
    d = out_dir / row["mpn"]
    d.mkdir(parents=True, exist_ok=True)
    kind = KIND[fam["kind"]]
    obs = row["observed"]
    lines = [
        "# Generated by scripts/passivegen.py from parts/passives.yaml: edit the table, not this file.",
        f"# Regenerate with: python3 scripts/passivegen.py --mpn {row['mpn']}",
        f"# Source: {fam['source']}",
    ]
    if row.get("line"):
        lines.append(f"# Part-search line: {row['line']}")
    lines.append(f"# Observed: DigiKey {obs['digikey']}; Mouser {obs['mouser']}.")
    lines += [f"library: {kind['library']}", f"name: {row['mpn']}", f"style: {kind['style']}",
              "pins: pins.csv", "fields:"]
    fields = build_part(row, fam, layout)
    for k, v in fields.items():
        lines.append(f"  {k}: {json.dumps(str(v), ensure_ascii=False)}")  # JSON strings are valid YAML
    if layout == "d45":
        lines.append("field_layout:")
        for k, v in field_layout(fields, fam["kind"]).items():
            lines.append(f"  {k}: {json.dumps(v)}")
    (d / "part.yaml").write_text("\n".join(lines) + "\n")
    # Pin 1 on top, pin 2 below (as KiCad's Device:R and Device:C); both passive
    (d / "pins.csv").write_text("number,name,type,unit,side,slot,alternates\n"
                                "1,~,passive,1,T,,\n2,~,passive,1,B,,\n")
    return d / "part.yaml"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--table", default=str(TABLE))
    ap.add_argument("--mpn", action="append", help="only these MPNs")
    ap.add_argument("--no-symbols", action="store_true")
    ap.add_argument("--layout", choices=["mpn", "d45"], default=LAYOUT, help=f"symbol layout (default {LAYOUT})")
    ap.add_argument("--out", help="preview: write parts and symbol libraries under this folder, not the repo")
    args = ap.parse_args()
    t = load_yaml(args.table)
    fams = t["families"]
    rows = [r for r in t["parts"] if not args.mpn or r["mpn"] in args.mpn]
    if args.mpn and len(rows) != len(set(args.mpn)):
        sys.exit(f"passivegen: not in the table: {sorted(set(args.mpn) - {r['mpn'] for r in rows})}")
    seen = set()
    for r in rows:
        if r["mpn"] in seen:
            sys.exit(f"passivegen: {r['mpn']} is in the table twice")
        seen.add(r["mpn"])
        if r["family"] not in fams:
            sys.exit(f"passivegen: {r['mpn']}: unknown family {r['family']}")
        if r["size"] not in SIZES:
            sys.exit(f"passivegen: {r['mpn']}: unknown size {r['size']}")
        out = Path(args.out) if args.out else REPO / "parts"
        path = write_part(r, fams[r["family"]], args.layout, out)
        if not args.no_symbols:
            lib = ["--out", str(out / f"{KIND[fams[r['family']]['kind']]['library']}.kicad_sym")] if args.out else []
            subprocess.run([sys.executable, str(REPO / "scripts" / "symbolgen.py"), str(path), *lib], check=True)
    print(f"passivegen: {len(rows)} part(s)")


if __name__ == "__main__":
    main()
