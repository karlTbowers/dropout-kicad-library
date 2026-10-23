#!/usr/bin/env python3
"""Run the official KLC checkers (kicad-library-tools) and apply DropOut's approved exceptions.

Usage:
  python3 scripts/klc_check.py                     # check every library in the repo
  python3 scripts/klc_check.py symbols/DropOut_Power.kicad_sym footprints/DropOut_Power.pretty/X.kicad_mod
  python3 scripts/klc_check.py --raw ...           # also print the checker's full output

Each violation is reported as:
  FAIL    the checker raised an error (fails CI)
  WARN    the checker raised only warnings, which KLC allows where the manufacturer's data
          requires it (the checker itself exits 2, "allowed failure"); reviewers look at these
  WAIVED  covered by klc-exceptions.yml

Exit code 0 when there is no FAIL, 1 otherwise, 2 on setup errors.

The checker comes from https://gitlab.com/kicad/libraries/kicad-library-tools at the commit in
KLT_REF below. Set KICAD_LIBRARY_TOOLS=/path/to/checkout to use an existing clone; otherwise it is
cloned to ~/.cache/dropout/kicad-library-tools.
"""
import argparse
import fnmatch
import os
import re
import subprocess
import sys
from pathlib import Path

# Pin the checker version. TODO(first run on the Mac): set the default below to the commit hash
# of a known-good kicad-library-tools revision, and keep CI's KLT_REF in sync.
KLT_REF = os.environ.get("KLT_REF", "a903a695bf4e69905e9e56548f44dd46cdc1130e")  # kicad-library-tools main @ 2026-10-21
KLT_URL = "https://gitlab.com/kicad/libraries/kicad-library-tools.git"

REPO = Path(__file__).resolve().parent.parent
# Checker output format (verified against kicad-library-tools a903a69, `-vv`):
#   Checking footprint 'SOT-23':                                       <- symbols: Checking component 'Lib:Name':
#     Violating F9.3 - https://klc.kicad.org/footprint/f9/f9.3/      <- header (printed twice)
#     Violating F9.3 - https://klc.kicad.org/footprint/f9/f9.3/
#       Footprint 3D model requirements - F9.3 - https://...           <- title echo, ignored
#       Model path should start with '${KICAD10_3DMODEL_DIR}/'        <- detail lines
#         - 3D model path: ...
# Detail lines carry the severity as their colour: warnings brown (0;33), errors red (0;31)
# (library_utils/common/rulebase.py). A message continues on uncoloured lines until the next code.
ITEM_RE = re.compile(r"^Checking\s+(?:symbol|footprint|component)\s+'(?:[^':]+:)?([^']+)'")
HEADER_RE = re.compile(r"^(?:Violating|Warning|Error)\b.*?\b([GSFM]\d+\.\d+)\b")
# The title echo may wrap: "<title> - S5.1 -" on one line, then the bare KLC URL on the next.
TITLE_ECHO_RE = re.compile(r"\s-\s[GSFM]\d+\.\d+\s-(?:\s+https?://\S+)?$|^https?://klc\.kicad\.org/\S+$")
COLOR_RE = re.compile(r"\x1b\[([0-9;]*)m")
ERROR_COLOR = "0;31"


def load_exceptions():
    try:
        import yaml  # PyYAML
    except ImportError:
        sys.exit("klc_check: PyYAML is required (pip3 install pyyaml)")
    data = yaml.safe_load((REPO / "klc-exceptions.yml").read_text()) or {}
    return data.get("exceptions", [])


def tools_dir():
    env = os.environ.get("KICAD_LIBRARY_TOOLS")
    if env:
        return Path(env)
    d = Path.home() / ".cache" / "dropout" / "kicad-library-tools"
    if not (d / ".git").exists():
        d.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "--quiet", KLT_URL, str(d)], check=True)
    if KLT_REF:
        subprocess.run(["git", "-C", str(d), "fetch", "--quiet", "origin", KLT_REF], check=False)
        subprocess.run(["git", "-C", str(d), "checkout", "--quiet", KLT_REF], check=True)
    return d


def find_checker(root, name):
    hits = sorted(root.rglob(name))
    if not hits:
        sys.exit(f"klc_check: {name} not found under {root} - kicad-library-tools layout changed?")
    return hits[0]


def covered(rule, library, item, header, details, exceptions):
    """Return the exception id that waives this violation, or None.

    If an exception has a `match` regex, it covers only the detail lines (or the header, when
    the checker printed no details) that match it. The violation is waived when every line is
    covered by some exception that applies to this rule and item, so two narrow exceptions can
    together waive one violation (the checker reports all S6.2 findings of a symbol as one).
    A violation that mixes a waived problem with any other problem is NOT waived.
    """
    key = f"{library}:{item}"
    lines = details or [header]
    uncovered, used = set(range(len(lines))), []
    for ex in exceptions:
        rules = [str(r) for r in ex.get("rules", [])]
        if not any(rule == r or rule.startswith(r + ".") for r in rules):
            continue
        patterns = ex.get("applies", ["*"])
        if isinstance(patterns, str):
            patterns = [patterns]
        if not any(fnmatch.fnmatchcase(key, p) for p in patterns):
            continue
        m = ex.get("match")
        if not m:
            return ex["id"]
        hit = {i for i in uncovered if re.search(m, lines[i])}
        if hit:
            uncovered -= hit
            used.append(ex["id"])
        if not uncovered:
            return ", ".join(used)
    return None


def run(checker, target, raw, extra=()):
    proc = subprocess.run([sys.executable, str(checker), "-vv", *extra, str(target)],
                          capture_output=True, text=True)
    if raw:
        print(proc.stdout)
    if proc.stderr.strip() and (raw or not proc.stdout.strip()):
        print(proc.stderr, file=sys.stderr)
    if proc.returncode != 0 and not proc.stdout.strip():
        sys.exit(f"klc_check: {checker.name} crashed on {target} (exit {proc.returncode})")
    return proc.stdout  # parse stdout only, so stray warnings never count as violation details


def parse(output, library, default_item):
    """Yield (item, rule, header, details, is_error) for each violation in checker output.

    A violation is a line naming a rule ID, followed by its indented detail lines. It is an
    error if any detail line was printed in the checker's error colour.
    """
    item = default_item
    current = None
    color = None
    for line in output.splitlines():
        codes = COLOR_RE.findall(line)
        if codes and line.lstrip().startswith("\x1b"):
            color = codes[0]
        text = COLOR_RE.sub("", line).strip()
        if not text:
            continue
        m = ITEM_RE.search(text)
        h = HEADER_RE.search(text)
        if m:
            if current:
                yield current
                current = None
            item = m.group(1)
        elif h:
            # The checker prints each header twice; merge an identical header with no details yet.
            if current and current[2] == text and not current[3]:
                continue
            if current:
                yield current
            current = [item, h.group(1), text, [], False]
        elif current and not TITLE_ECHO_RE.search(text):
            current[3].append(text)
            current[4] = current[4] or color == ERROR_COLOR
        if codes and codes[-1] in ("0", ""):
            color = None  # reset code closes the coloured message
    if current:
        yield current


def targets(paths):
    if not paths:
        paths = [str(p) for p in sorted((REPO / "symbols").glob("*.kicad_sym"))]
        paths += [str(p) for p in sorted((REPO / "footprints").glob("*.pretty/*.kicad_mod"))]
    for p in map(Path, paths):
        if p.is_dir() and p.suffix == ".pretty":
            yield from sorted(p.glob("*.kicad_mod"))
        elif p.is_dir():  # e.g. symbols/ or footprints/: everything inside
            yield from sorted(p.glob("*.kicad_sym"))
            yield from sorted(p.glob("*.pretty/*.kicad_mod"))
        else:
            yield p


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--raw", action="store_true", help="print full checker output")
    args = ap.parse_args()

    files = list(targets(args.paths))
    if not files:
        print("klc_check: no symbols or footprints yet - nothing to check.")
        return 0

    exceptions = load_exceptions()
    root = tools_dir()
    sym_checker = find_checker(root, "check_symbol.py")
    fp_checker = find_checker(root, "check_footprint.py")

    failures, warnings, waived = [], [], []
    for f in files:
        extra = ()
        if f.suffix == ".kicad_sym":
            library, default_item, checker = f.stem, "?", sym_checker
            # S5.1: resolve "DropOut_X:Name" footprint links against this repo's footprints
            # (test fixtures keep their .pretty next to the symbol file)
            fp_root = REPO / "footprints" if f.parent.resolve() == (REPO / "symbols") else f.parent
            extra = ("--footprints", str(fp_root))
        elif f.suffix == ".kicad_mod":
            library, default_item, checker = f.parent.stem, f.stem, fp_checker
        else:
            failures.append((str(f), "-", f"not a .kicad_sym or .kicad_mod file: {f}", [], None))
            continue
        output = run(checker, f, args.raw, extra)
        # A file the checker never reports on (missing, unreadable, rejected) must not pass silently
        if not any(ITEM_RE.search(COLOR_RE.sub("", ln).strip()) for ln in output.splitlines()):
            first = next((COLOR_RE.sub("", ln).strip() for ln in output.splitlines() if ln.strip()), "no output")
            failures.append((f"{library}:{default_item}", "-", f"checker did not check {f}: {first}", [], None))
            continue
        for item, rule, header, details, is_error in parse(output, library, default_item):
            ex = covered(rule, library, item, header, details, exceptions)
            entry = (f"{library}:{item}", rule, header, details, ex)
            (waived if ex else failures if is_error else warnings).append(entry)

    for key, rule, header, details, ex in waived:
        print(f"WAIVED  {key}  {rule}  [{ex}]")
    for label, group in (("WARN", warnings), ("FAIL", failures)):
        for key, rule, header, details, _ in group:
            print(f"{label:<8}{key}  {rule}  {header}")
            for d in details:
                print(f"          {d}")
    print(f"\nKLC: {len(files)} file(s), {len(failures)} error(s), {len(warnings)} warning(s), "
          f"{len(waived)} waived by klc-exceptions.yml")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
