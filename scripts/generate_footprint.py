#!/usr/bin/env python3
"""Generate footprints and 3D models with kicad-library-tools from a DropOut spec file.

Usage (with the tools Python from scripts/setup_tools.sh, which has CadQuery):
  ~/.cache/dropout/klt-venv/bin/python scripts/generate_footprint.py \
      generators/package/grid_array/DropOut_NXP.yaml --lib DropOut_Package_BGA [-p 'NXP_LFBGA-257*']

The spec lives in this repo under generators/<generator>/, mirroring kicad-library-tools'
data/<generator>/ folder, in that generator's YAML format. This script:
  1. makes a throwaway git worktree of kicad-library-tools at KLT_REF (scripts/klc_check.py),
  2. adds the spec to the worktree's data folder,
  3. runs its generate.py with PYTHONPATH pointing at the worktree (otherwise an installed
     copy of the generators is imported and the spec is silently ignored),
  4. copies the results into footprints/<lib>.pretty/ and 3dmodels/<lib>.3dshapes/, with the
     model path rewritten to ${KIPRJMOD}/lib/dropout-kicad-library/3dmodels/<lib>.3dshapes/.

Generated names encode the real pad count (e.g. LFBGA-257): check them against the datasheet.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from klc_check import KLT_REF, REPO, tools_dir  # noqa: E402

MODEL_RE = re.compile(r'\(model "\$\{KICAD\d+_3DMODEL_DIR\}/[^"/]+\.3dshapes/')


def spec_parts(spec):
    # Top-level keys of the spec YAML are the part names
    return re.findall(r"^([A-Za-z0-9_][^\s:#]*):\s*$", spec.read_text(), re.M)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", help="generators/<generator>/<file>.yaml")
    ap.add_argument("--lib", required=True, help="DropOut footprint library, e.g. DropOut_Package_BGA")
    ap.add_argument("-p", "--part", action="append", help="part name glob(s) in the spec (default: all)")
    ap.add_argument("--no-3d", action="store_true", help="footprints only")
    args = ap.parse_args()

    spec = Path(args.spec).resolve()
    try:
        generator = spec.parent.relative_to(REPO / "generators").as_posix()
    except ValueError:
        sys.exit("generate_footprint: the spec must be under generators/<generator>/")
    if not args.lib.startswith("DropOut_"):
        sys.exit("generate_footprint: --lib must be a DropOut_ library")
    if not args.no_3d:
        try:
            import cadquery  # noqa: F401
        except ImportError:
            sys.exit("generate_footprint: CadQuery not found; run with ~/.cache/dropout/klt-venv/bin/python "
                     "(scripts/setup_tools.sh), or pass --no-3d")

    klt = tools_dir()
    with tempfile.TemporaryDirectory(prefix="dropout-fpgen-") as td:
        wt, out = Path(td) / "klt", Path(td) / "out"
        subprocess.run(["git", "-C", str(klt), "worktree", "add", "--quiet", "--detach", str(wt), KLT_REF], check=True)
        try:
            shutil.copyfile(spec, wt / "data" / generator / f"dropout_{spec.name}")
            # generate.py makes models only when given -m
            cmd = [sys.executable, "src/generators/generate.py", "-g", generator, "-f", str(out / "fp")]
            if not args.no_3d:
                cmd += ["-m", str(out / "3d")]
            # Default: only the parts in our spec, never the generator's stock parts
            for p in args.part or spec_parts(spec):
                cmd += ["-p", p]
            env = {**os.environ, "PYTHONPATH": f"{wt / 'src'}:{wt}"}
            proc = subprocess.run(cmd, cwd=wt, env=env, capture_output=True, text=True)
            print(proc.stdout[-1500:])
            if proc.returncode != 0:
                print(proc.stderr[-3000:], file=sys.stderr)
                sys.exit("generate_footprint: generator failed")

            fps = sorted(out.glob("fp/*.pretty/*.kicad_mod"))
            if not fps:
                sys.exit("generate_footprint: nothing generated - check the part names and the spec")
            fp_dir = REPO / "footprints" / f"{args.lib}.pretty"
            md_dir = REPO / "3dmodels" / f"{args.lib}.3dshapes"
            fp_dir.mkdir(parents=True, exist_ok=True)
            for f in fps:
                text = MODEL_RE.sub(f'(model "${{KIPRJMOD}}/lib/dropout-kicad-library/3dmodels/{args.lib}.3dshapes/',
                                    f.read_text())
                (fp_dir / f.name).write_text(text)
                print(f"footprint  {fp_dir.relative_to(REPO) / f.name}")
            for m in sorted(out.glob("3d/*.3dshapes/*.step")):
                md_dir.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(m, md_dir / m.name)
                print(f"3D model   {md_dir.relative_to(REPO) / m.name}")
        finally:
            subprocess.run(["git", "-C", str(klt), "worktree", "remove", "--force", str(wt)], check=False)


if __name__ == "__main__":
    main()
