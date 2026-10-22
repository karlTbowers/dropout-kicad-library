#!/usr/bin/env bash
# Set up (or check) everything the library's part-making scripts need on a Mac.
# Safe to re-run: it installs only what is missing.
#
#   scripts/setup_tools.sh           # install missing pieces
#   scripts/setup_tools.sh --check   # report only, change nothing
#
# Installs/uses:
#   Homebrew formulas  gh (GitHub CLI), uv (Python manager), poppler (pdftotext, pdftoppm,
#                      pdfdetach, pdfinfo), git-lfs (for the private dropout-vendor-docs repo)
#   KiCad 10           checked only (install the app from https://www.kicad.org/download/macos/
#                      or `brew install --cask kicad`); provides kicad-cli
#   kicad-library-tools  cloned to ~/.cache/dropout/kicad-library-tools at KLT_REF (klc_check.py)
#   Python env         ~/.cache/dropout/klt-venv (Python 3.12, via uv): kicad-library-tools with
#                      its 3D extras (CadQuery), pyyaml, openpyxl
set -euo pipefail

CHECK=0
[ "${1:-}" = "--check" ] && CHECK=1
REPO="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$HOME/.cache/dropout/klt-venv"
missing=0

say() { printf '%-22s %s\n' "$1" "$2"; }

if ! command -v brew >/dev/null; then
  say "Homebrew" "MISSING - install from https://brew.sh, then re-run"
  exit 1
fi

for f in gh uv poppler git-lfs; do
  if brew list --formula "$f" >/dev/null 2>&1; then
    say "$f" "ok"
  elif [ $CHECK -eq 1 ]; then
    say "$f" "MISSING (brew install $f)"; missing=1
  else
    say "$f" "installing"; brew install "$f" >/dev/null
  fi
done

if [ $CHECK -eq 0 ]; then
  git lfs install >/dev/null && say "git-lfs hooks" "ok"
fi

CLI=""
for c in "${KICAD_CLI:-}" "$(command -v kicad-cli || true)" /Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli; do
  [ -n "$c" ] && [ -x "$c" ] && CLI="$c" && break
done
if [ -n "$CLI" ]; then
  say "KiCad" "$("$CLI" --version) ($CLI)"
else
  say "KiCad" "MISSING - install KiCad 10 (https://www.kicad.org/download/macos/ or brew install --cask kicad)"
  missing=1
fi

if [ -x "$VENV/bin/python" ] && "$VENV/bin/python" -c "import cadquery, generators, yaml, openpyxl" 2>/dev/null; then
  say "klt-venv" "ok ($VENV)"
elif [ $CHECK -eq 1 ]; then
  say "klt-venv" "MISSING or incomplete ($VENV)"; missing=1
else
  say "klt-venv" "creating (Python 3.12, CadQuery: a few minutes)"
  [ -x "$VENV/bin/python" ] || uv venv -q --python 3.12 "$VENV"
  VIRTUAL_ENV="$VENV" uv pip install -q pyyaml openpyxl
  KLT="$("$VENV/bin/python" -c "import sys; sys.path.insert(0, '$REPO/scripts'); from klc_check import tools_dir; print(tools_dir())")"
  VIRTUAL_ENV="$VENV" uv pip install -q -e "${KLT}[3d]"
  "$VENV/bin/python" -c "import cadquery, generators, yaml, openpyxl" && say "klt-venv" "ok ($VENV)"
fi

if [ $missing -eq 1 ]; then
  echo; echo "Some tools are missing (see above)."; exit 1
fi
echo
echo "Ready. Use $VENV/bin/python for scripts/klc_check.py, generate_footprint.py, symbolgen.py"
echo "and scripts/pintables/*.py."
