#!/usr/bin/env python3
"""Check that every symbol in DropOut .kicad_sym libraries carries the required fields.

Usage: python3 scripts/check_symbol_fields.py [symbols_dir]
Exit code 1 if any symbol is missing a required field or has it blank.
"""
import re
import sys
from pathlib import Path

REQUIRED = [
    "Reference", "Value", "Footprint", "Datasheet", "Description",
    "Manufacturer", "MPN", "DigiKey_PN", "Mouser_PN",
]
# Fields where a placeholder is not acceptable (distributor PNs may be "-")
NO_PLACEHOLDER = {"Footprint", "Datasheet", "Description", "Manufacturer", "MPN"}
PLACEHOLDERS = {"", "~", "-"}


def off_board(body):
    """(on_board no): a part bought but never placed on the PCB, e.g. a panel connector; it has no
    footprint (user's decision 2026-10-28, SurLok Plus SLPRATPSx)."""
    return re.search(r"^\s*\(on_board no\)", body, re.M) is not None


def top_level_symbols(text):
    """Yield (name, body) for each top-level (symbol "...") block, skipping unit sub-symbols."""
    depth = 0
    i = 0
    n = len(text)
    while i < n:
        c = text[i]
        if c == '"':
            # skip quoted strings (may contain parentheses)
            i += 1
            while i < n and text[i] != '"':
                if text[i] == "\\":
                    i += 1
                i += 1
        elif c == "(":
            if depth == 1 and text.startswith("(symbol ", i):
                start = i
                d = 0
                j = i
                while j < n:
                    if text[j] == '"':
                        j += 1
                        while j < n and text[j] != '"':
                            if text[j] == "\\":
                                j += 1
                            j += 1
                    elif text[j] == "(":
                        d += 1
                    elif text[j] == ")":
                        d -= 1
                        if d == 0:
                            break
                    j += 1
                body = text[start:j + 1]
                m = re.match(r'\(symbol\s+"([^"]*)"', body)
                yield (m.group(1) if m else "?"), body
                i = j + 1
                continue
            depth += 1
        elif c == ")":
            depth -= 1
        i += 1


def properties(body):
    return {k: v for k, v in re.findall(r'\(property\s+"([^"]*)"\s+"((?:[^"\\]|\\.)*)"', body)}


def is_alias(body):
    return re.search(r"\(extends\s+\"", body) is not None


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "symbols")
    files = sorted(root.glob("*.kicad_sym"))
    if not files:
        print(f"No .kicad_sym files under {root}/ yet - nothing to check.")
        return 0
    errors = 0
    count = 0
    for f in files:
        if not f.name.startswith("DropOut_"):
            print(f"{f}: library name must start with 'DropOut_'")
            errors += 1
        for name, body in top_level_symbols(f.read_text(encoding="utf-8")):
            count += 1
            props = properties(body)
            for field in REQUIRED:
                if field not in props:
                    print(f"{f.name}:{name}: missing field '{field}'")
                    errors += 1
                    continue
                val = props[field].strip()
                if val in PLACEHOLDERS and (field in NO_PLACEHOLDER or val in {"", "~"}):
                    if field == "Footprint" and (is_alias(body) or off_board(body)):
                        continue
                    print(f"{f.name}:{name}: field '{field}' is blank")
                    errors += 1
            fp = props.get("Footprint", "")
            if fp and fp not in PLACEHOLDERS and not fp.startswith("DropOut_"):
                print(f"{f.name}:{name}: Footprint '{fp}' is not in a DropOut_ library")
                errors += 1
    print(f"Checked {count} symbol(s) in {len(files)} librar{'y' if len(files) == 1 else 'ies'}: "
          f"{'OK' if not errors else str(errors) + ' problem(s)'}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
