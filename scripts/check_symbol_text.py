#!/usr/bin/env python3
"""Check that no text in a symbol overprints other text (handbook rule D-47).

Usage: python3 scripts/check_symbol_text.py [symbols_dir_or_file ...]

For every symbol and unit, builds a box for each visible pin name, pin number and visible field
(Reference, Value) as KiCad 10 draws them, and reports any two boxes that overlap. A unit is
checked together with the symbol's common graphics (unit 0) and its fields.

Text geometry (conservative, as the handbook and symbolgen.py assume): each character is as
wide as the font size (1.27 mm text: 1.27 mm per character; overbar markup ~{...} not counted),
and a line is as tall as the font size. Pin names sit `pin_names offset` past the pin's inner
end (inside the body) when the offset is above 0, otherwise centred above the pin line; pin
numbers are centred on the pin, NUM_GAP clear of the line. Exit 1 on any overlap.
"""
import re
import sys
from pathlib import Path

NUM_GAP = 0.254   # pin number / outside-name clearance from the pin line
EPS = 1e-6


def parse(text):
    """Minimal s-expression parser: lists of atoms; quoted strings keep their quotes stripped."""
    tokens = re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+', text)
    stack, cur = [], []
    for t in tokens:
        if t == "(":
            stack.append(cur)
            cur = []
        elif t == ")":
            done, cur = cur, stack.pop()
            cur.append(done)
        else:
            cur.append(t[1:-1].replace('\\"', '"').replace("\\\\", "\\") if t.startswith('"') else t)
    return cur


def find(node, key):
    return next((c for c in node if isinstance(c, list) and c and c[0] == key), None)


def find_all(node, key):
    return [c for c in node if isinstance(c, list) and c and c[0] == key]


def hidden(node):
    """True for (hide yes) / bare hide inside node or its effects."""
    for n in (node, find(node, "effects") or []):
        if "hide" in n[1:]:
            return True
        h = find(n, "hide")
        if h is not None and (len(h) == 1 or h[1] == "yes"):
            return True
    return False


def font_size(node):
    eff = find(node, "effects")
    font = find(eff, "font") if eff else None
    size = find(font, "size") if font else None
    return (float(size[1]), float(size[2])) if size else (1.27, 1.27)


def text_len(s, char_w):
    return len(re.sub(r"[~{}]", "", s)) * char_w


def box_along(x, y, rot, start, length, h, side_off=0.0):
    """Box for text running from `start` to `start+length` along direction `rot` from (x, y),
    centred `side_off` to the left of that direction (perpendicular), `h` thick."""
    d = {0: (1, 0), 90: (0, 1), 180: (-1, 0), 270: (0, -1)}[rot]
    n = (-d[1], d[0])  # left normal
    pts = []
    for a in (start, start + length):
        for b in (side_off - h / 2, side_off + h / 2):
            pts.append((x + d[0] * a + n[0] * b, y + d[1] * a + n[1] * b))
    xs, ys = zip(*pts)
    return (min(xs), min(ys), max(xs), max(ys))


def pin_boxes(pin, name_off, names_hidden, numbers_hidden):
    at = find(pin, "at")
    x, y, rot = float(at[1]), float(at[2]), int(float(at[3])) if len(at) > 3 else 0
    length = float(find(pin, "length")[1])
    out = []
    name, number = find(pin, "name"), find(pin, "number")
    # KiCad pin "at" is the outer (connection) end; rot is the direction towards the body.
    if name and name[1] not in ("", "~") and not names_hidden and not hidden(name):
        h, w = font_size(name)
        tl = text_len(name[1], w)
        if name_off > 0:
            out.append(("name " + name[1], box_along(x, y, rot, length + name_off, tl, h)))
        else:  # outside: centred above the pin line (left of direction for horizontal pins)
            side = h / 2 + NUM_GAP
            out.append(("name " + name[1],
                        box_along(x, y, rot, length / 2 - tl / 2, tl, h, side if rot in (0, 180) else -side)))
    if number and number[1] != "" and not numbers_hidden and not hidden(number):
        h, w = font_size(number)
        tl = text_len(number[1], w)
        side = h / 2 + NUM_GAP
        # numbers sit above horizontal pins and left of vertical pins
        side = side if rot == 0 else -side if rot == 180 else side if rot == 90 else -side
        out.append(("number " + number[1], box_along(x, y, rot, length / 2 - tl / 2, tl, h, side)))
    return out


def field_box(prop):
    at = find(prop, "at")
    x, y = float(at[1]), float(at[2])
    rot = int(float(at[3])) if len(at) > 3 else 0
    h, w = font_size(prop)
    tl = text_len(prop[2], w)
    if rot in (90, 270):
        return (x - h / 2, y - tl / 2, x + h / 2, y + tl / 2)
    j = find(find(prop, "effects") or [], "justify") or []
    if "left" in j:
        return (x, y - h / 2, x + tl, y + h / 2)
    if "right" in j:
        return (x - tl, y - h / 2, x, y + h / 2)
    return (x - tl / 2, y - h / 2, x + tl / 2, y + h / 2)


def overlap(a, b):
    return a[0] < b[2] - EPS and b[0] < a[2] - EPS and a[1] < b[3] - EPS and b[1] < a[3] - EPS


def check_symbol(sym):
    name = sym[1]
    pn = find(sym, "pin_names")
    name_off = float(find(pn, "offset")[1]) if pn and find(pn, "offset") else 0.508
    names_hidden = bool(pn) and hidden(pn)
    pnum = find(sym, "pin_numbers")
    numbers_hidden = bool(pnum) and hidden(pnum)
    fields = [(f"field {p[1]}", field_box(p)) for p in find_all(sym, "property")
              if not hidden(p) and p[2] != ""]
    units = {}
    for sub in find_all(sym, "symbol"):
        m = re.match(r".*_(\d+)_(\d+)$", sub[1])
        if m:
            units.setdefault(int(m.group(1)), []).extend(
                b for pin in find_all(sub, "pin") if not hidden(pin)
                for b in pin_boxes(pin, name_off, names_hidden, numbers_hidden))
    common = units.pop(0, [])
    problems = []
    for u in sorted(units) or [0]:
        boxes = fields + common + units.get(u, [])
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                if overlap(boxes[i][1], boxes[j][1]):
                    problems.append(f"{name} unit {u}: {boxes[i][0]} overprints {boxes[j][0]}")
    return problems


def main():
    args = sys.argv[1:] or ["symbols"]
    files = []
    for a in map(Path, args):
        files += sorted(a.glob("*.kicad_sym")) if a.is_dir() else [a]
    problems, count = [], 0
    for f in files:
        lib = parse(f.read_text())[0]
        for sym in find_all(lib, "symbol"):
            if find(sym, "extends"):
                continue
            count += 1
            problems += [f"{f.stem}:{p}" for p in check_symbol(sym)]
    for p in problems:
        print(f"OVERPRINT {p}")
    print(f"Symbol text: checked {count} symbol(s): " + ("OK" if not problems else f"{len(problems)} overprint(s)"))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
