#!/usr/bin/env python3
"""Run the official KLC checkers (kicad-library-tools) and apply DropOut's approved exceptions.

Usage:
  python3 scripts/klc_check.py                     # check every library in the repo
  python3 scripts/klc_check.py symbols/DropOut_Power.kicad_sym footprints/DropOut_Power.pretty/X.kicad_mod
  python3 scripts/klc_check.py --raw ...           # also print the checker's full output

Exit code 0 when every violation is covered by klc-exceptions.yml, 1 otherwise, 2 on setup errors.

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

# Pin the checker version. TODO(first run on the Mac): replace "master" with the commit hash
# of a known-good kicad-library-tools revision, and keep CI's KLT_REF in sync.
KLT_REF = os.environ.get("KLT_REF", "master")
KLT_URL = "https://gitlab.com/kicad/libraries/kicad-library-tools.git"

REPO = Path(__file__).resolve().parent.parent
RULE_RE = re.compile(r"\b([GSFM]\d+\.\d+)\b")
ITEM_RE = re.compile(r"(?:Checking|checking)\s+(?:symbol|footprint)\s+['\"]?([^'\":\s]+)")
VIOLATION_RE = re.compile(r"(?i)violat|error|warning")


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
    subprocess.run(["git", "-C", str(d), "fetch", "--quiet", "origin", KLT_REF], check=False)
    subprocess.run(["git", "-C", str(d), "checkout", "--quiet", KLT_REF], check=False)
    return d


def find_checker(root, name):
    hits = sorted(root.rglob(name))
    if not hits:
        sys.exit(f"klc_check: {name} not found under {root} - kicad-library-tools layout changed?")
    return hits[0]


def covered(rule, library, item, header, details, exceptions):
    """Return the exception id that waives this violation, or None.

    If an exception has a `match` regex, every detail line must match it (or the header,
    when the checker printed no details). A violation that mixes a waived problem with any
    other problem is NOT waived.
    """
    key = f"{library}:{item}"
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
        if m:
            lines = details or [header]
            if not all(re.search(m, ln) for ln in lines):
                continue
        return ex["id"]
    return None


def run(checker, target, raw):
    proc = subprocess.run([sys.executable, str(checker), "-vv", str(target)],
                          capture_output=True, text=True)
    if raw:
        print(proc.stdout)
    if proc.stderr.strip() and (raw or not proc.stdout.strip()):
        print(proc.stderr, file=sys.stderr)
    if proc.returncode != 0 and not proc.stdout.strip():
        sys.exit(f"klc_check: {checker.name} crashed on {target} (exit {proc.returncode})")
    return proc.stdout  # parse stdout only, so stray warnings never count as violation details


def parse(output, library, default_item):
    """Yield (item, rule, header, details) for each violation in checker output.

    A violation is a line naming a rule ID, followed by its indented detail lines.
    """
    item = default_item
    current = None
    for line in output.splitlines():
        clean = re.sub(r"\x1b\[[0-9;]*m", "", line).rstrip()
        text = clean.strip()
        m = ITEM_RE.search(text)
        r = RULE_RE.search(text)
        if m or (r and VIOLATION_RE.search(text)):
            if current:
                yield current
                current = None
            if m:
                item = m.group(1)
            if r and VIOLATION_RE.search(text):
                current = (item, r.group(1), text, [])
        elif current and text:
            current[3].append(text)
    if current:
        yield current


def targets(paths):
    if not paths:
        paths = [str(p) for p in sorted((REPO / "symbols").glob("*.kicad_sym"))]
        paths += [str(p) for p in sorted((REPO / "footprints").glob("*.pretty/*.kicad_mod"))]
    for p in map(Path, paths):
        if p.is_dir() and p.suffix == ".pretty":
            yield from sorted(p.glob("*.kicad_mod"))
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

    failures, waived = [], []
    for f in files:
        if f.suffix == ".kicad_sym":
            library, default_item, checker = f.stem, "?", sym_checker
        elif f.suffix == ".kicad_mod":
            library, default_item, checker = f.parent.stem, f.stem, fp_checker
        else:
            continue
        for item, rule, header, details in parse(run(checker, f, args.raw), library, default_item):
            ex = covered(rule, library, item, header, details, exceptions)
            (waived if ex else failures).append((f"{library}:{item}", rule, header, details, ex))

    for key, rule, header, details, ex in waived:
        print(f"WAIVED  {key}  {rule}  [{ex}]")
    for key, rule, header, details, _ in failures:
        print(f"FAIL    {key}  {rule}  {header}")
        for d in details:
            print(f"          {d}")
    print(f"\nKLC: {len(files)} file(s), {len(failures)} violation(s), {len(waived)} waived by klc-exceptions.yml")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
