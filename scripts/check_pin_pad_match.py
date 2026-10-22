#!/usr/bin/env python3
"""Check DropOut's symbol pin rules.

Usage: python3 scripts/check_pin_pad_match.py [symbols_dir] [footprints_dir]

1. No combined pins: every package pin is its own pin on the symbol. A KiCad native pin stack
   (number "[A1,B2]") or two pins at the same position in a unit is an error. Stricter than
   KLC S4.3, which allows stacking.
2. Pins match pads: for each symbol whose Footprint field points at a DropOut footprint in this
   repo, the set of pin numbers must equal the set of numbered pads. Unnumbered pads
   (mechanical, thermal-only with an empty name) are ignored.
Exit 1 on any problem.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_symbol_fields import properties, top_level_symbols  # noqa: E402


def pin_numbers(body):
    nums = set()
    for n in re.findall(r'\(pin\s+\w+\s+\w+.*?\(number\s+"([^"]*)"', body, re.S):
        m = re.match(r"^\[(.*)\]$", n)
        nums |= set(x.strip() for x in m.group(1).split(",")) if m else {n}
    return nums


def combined_pins(name, body):
    """Return descriptions of combined pins: native stacks, or several pins at one position."""
    problems = []
    for unit_name, unit_body in re.findall(r'\(symbol\s+"([^"]*_\d+_\d+)"(.*?)(?=\(symbol\s+"[^"]*_\d+_\d+"|\Z)',
                                           body, re.S):
        seen = {}
        for at, number in re.findall(r'\(pin\s+\w+\s+\w+\s*\(at\s+([-\d.]+\s+[-\d.]+).*?\(number\s+"([^"]*)"',
                                     unit_body, re.S):
            if number.startswith("["):
                problems.append(f"pin stack {number} in {unit_name}")
            pos = tuple(float(v) for v in at.split())
            if pos in seen:
                problems.append(f"pins {seen[pos]} and {number} share position {pos} in {unit_name}")
            else:
                seen[pos] = number
    return problems


def pad_numbers(text):
    return {n for n in re.findall(r'\(pad\s+"([^"]*)"', text) if n}


def main():
    sym_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "symbols")
    fp_dir = Path(sys.argv[2] if len(sys.argv) > 2 else "footprints")
    errors = checked = 0
    for lib in sorted(sym_dir.glob("*.kicad_sym")):
        for name, body in top_level_symbols(lib.read_text(encoding="utf-8")):
            for problem in combined_pins(name, body):
                errors += 1
                print(f"{lib.stem}:{name}: combined pins not allowed ({problem})")
            fp = properties(body).get("Footprint", "")
            if ":" not in fp:
                continue
            fp_lib, fp_name = fp.split(":", 1)
            fp_file = fp_dir / f"{fp_lib}.pretty" / f"{fp_name}.kicad_mod"
            if not fp_file.exists():
                continue  # KLC S5.1 reports missing footprints
            checked += 1
            pins, pads = pin_numbers(body), pad_numbers(fp_file.read_text(encoding="utf-8"))
            if pins != pads:
                errors += 1
                print(f"{lib.stem}:{name} vs {fp}:")
                if pins - pads:
                    print(f"  pins with no pad: {sorted(pins - pads)}")
                if pads - pins:
                    print(f"  pads with no pin: {sorted(pads - pins)}")
    print(f"Symbol pins: no combined pins; pin/pad match on {checked} symbol(s): "
          f"{'OK' if not errors else str(errors) + ' problem(s)'}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
