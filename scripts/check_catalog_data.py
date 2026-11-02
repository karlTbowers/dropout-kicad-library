#!/usr/bin/env python3
"""Check the catalog family data: parts/families.yaml and the `catalog:` blocks in parts/*/part.yaml,
and the model-only parts (`kind: model`, docs/CONTRIBUTING.md "Model-only parts").

Usage: python3 scripts/check_catalog_data.py [parts_dir]
Exit code 1 if a part names a family or group that families.yaml doesn't list, an attribute value
is blank or not plain text, or a family lists a group no part uses; or if a model-only part lacks a
required field, its folder or model file isn't named as the part, or its model or drawing is missing.
Needs PyYAML.
"""
import sys
from pathlib import Path

import yaml

KEYS = {"family", "group", "attributes", "mates_with"}
FAMILY_KEYS = {"title", "intro", "groups"}
MODEL_KEYS = {"kind", "library", "name", "model", "drawing", "fields", "catalog"}
MODEL_FIELDS = ["Value", "Datasheet", "Description", "Manufacturer", "MPN", "DigiKey_PN", "Mouser_PN"]


def check_model_part(path, data, root):
    """Errors for a model-only part: a 3D model (and optional drawing) with fields, no symbol or footprint."""
    where = path.relative_to(root)
    errors = []
    if set(data) - MODEL_KEYS:
        errors.append(f"{where}: unknown keys {sorted(set(data) - MODEL_KEYS)} for kind: model")
    name, lib = data.get("name"), data.get("library")
    if name != path.parent.name:
        errors.append(f"{where}: name '{name}' must match its folder")
    fields = data.get("fields") or {}
    for f in MODEL_FIELDS:
        if not isinstance(fields.get(f), str) or not fields[f].strip():
            errors.append(f"{where}: field {f} is required")
    if fields.get("Value") != name:
        errors.append(f"{where}: Value must be the part name")
    if data.get("model") != f"3dmodels/{lib}.3dshapes/{name}.step":
        errors.append(f"{where}: model must be 3dmodels/{lib}.3dshapes/{name}.step")
    for key in ("model", "drawing"):
        if data.get(key) and not (root / data[key]).is_file():
            errors.append(f"{where}: {key} {data[key]} does not exist")
    return errors


def main():
    parts = Path(sys.argv[1] if len(sys.argv) > 1 else "parts")
    errors = []
    families = yaml.safe_load((parts / "families.yaml").read_text(encoding="utf-8")) or {}
    for key, fam in families.items():
        if not isinstance(fam, dict) or not fam.get("title") or not isinstance(fam.get("groups"), list):
            errors.append(f"families.yaml: {key}: needs a title and a list of groups")
        elif set(fam) - FAMILY_KEYS:
            errors.append(f"families.yaml: {key}: unknown keys {sorted(set(fam) - FAMILY_KEYS)}")

    used = set()
    count = 0
    for path in sorted(parts.glob("*/part.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if data.get("kind") == "model":
            errors += check_model_part(path, data, parts.parent)
        cat = data.get("catalog")
        if cat is None:
            continue
        count += 1
        where = path.relative_to(parts.parent)
        if not isinstance(cat, dict) or set(cat) - KEYS:
            errors.append(f"{where}: catalog keys must be {sorted(KEYS)}")
            continue
        fam = families.get(cat.get("family"))
        if not isinstance(fam, dict):
            errors.append(f"{where}: family '{cat.get('family')}' is not in families.yaml")
        elif cat.get("group") not in (fam.get("groups") or []):
            errors.append(f"{where}: group '{cat.get('group')}' is not listed under {cat['family']} in families.yaml")
        else:
            used.add((cat["family"], cat["group"]))
        attrs = cat.get("attributes")
        if not isinstance(attrs, dict) or not attrs:
            errors.append(f"{where}: catalog needs attributes")
        else:
            for k, v in attrs.items():
                if not isinstance(v, str) or not v.strip():
                    errors.append(f"{where}: attribute '{k}' must be non-blank text (quote values such as 'No' or '25')")
        mates = cat.get("mates_with", [])
        if not isinstance(mates, list) or not all(isinstance(m, str) and m for m in mates):
            errors.append(f"{where}: mates_with must be a list of MPNs")

    for key, fam in families.items():
        for g in (fam.get("groups") or []) if isinstance(fam, dict) else []:
            if (key, g) not in used:
                errors.append(f"families.yaml: {key}: group '{g}' has no parts")

    for e in errors:
        print(e)
    print(f"Catalog data: {count} part(s) in {len(families)} famil{'y' if len(families) == 1 else 'ies'}: {'FAIL' if errors else 'OK'}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
