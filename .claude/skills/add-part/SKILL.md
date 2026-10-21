---
name: add-part
description: Add a new part (symbol, footprint, 3D model) to the DropOut KiCad library following KLC plus DropOut's approved exceptions. Use whenever asked to add, create, import, or fix a library part.
---

# Add a part to the DropOut library

The goal is a part that a DropOut engineer can drop into a schematic and order without a second look. Every value in the part must trace to the manufacturer's datasheet or a distributor API response, never to memory.

**Rules authority, in order:**
1. `klc-exceptions.yml`: DropOut's approved deviations from KLC.
2. **KLC** (https://klc.kicad.org/): everything not excepted. Follow it fully.
3. `docs/CONTRIBUTING.md`: DropOut additions (distributor fields, atomic parts, PR flow).

Never deviate from KLC on your own. If a rule seems wrong for DropOut, stop and propose a new `klc-exceptions.yml` entry to the user, with the rule ID and reason. It goes in its own PR, not bundled with a part.

## 0. Preconditions (check once per session)

- Distributor keys present: `DIGIKEY_CLIENT_ID`, `MOUSER_SEARCH_API_KEY`, `NEWARK_SEARCH_API_KEY` are set (from `scripts/vendor-env.sh`). If not, tell the user and stop.
- KLC checker works: `python3 scripts/klc_check.py` runs (clones kicad-library-tools on first use).
- Start from an up-to-date `main` and create a branch: `git switch -c add/<MPN>`.

## 1. Identify the exact part

- Get the **orderable MPN including packaging suffix** (e.g. `TPS2HCS08AQPWPRQ1`, not `TPS2HCS08-Q1`).
- Look it up with the kicad-happy `digikey`, `mouser`, and `element14` skills. Record: manufacturer name, DigiKey PN, Mouser PN, lifecycle status, the manufacturer datasheet URL.
- If the part isn't stocked at a distributor, its PN field is `-`. If the part is obsolete or NRND, tell the user before continuing.
- Download the datasheet PDF to a scratch location **outside the repo** and read it. Never commit PDFs.

## 2. Decide symbol, footprint, and model names

- **Library:** pick the existing `DropOut_<Category>` that fits (see README). A new category needs the user's OK.
- **Symbol name:** per KLC S2.1/S2.2: the manufacturer part number, with non-functional variations (packaging, temperature grade letters that don't change function) handled per S2.2. Separate symbol per footprint option (S2.3).
- **Footprint name:** per KLC F2/F3 naming for that package type. **Reuse** an existing DropOut footprint if the land pattern is identical.
- **3D model name:** identical to the footprint name, `.step`, in `3dmodels/<FootprintLibrary>.3dshapes/`.

## 3. Footprint

- Prefer the **kicad-library-tools footprint generators** for standard packages (SOIC, SSOP/TSSOP/HTSSOP, QFN/VQFN, BGA, SOT, chip passives). Feed them dimensions from the datasheet's **recommended land pattern**, not the package drawing alone (KLC F4.1 datasheet priority). Generated `.kicad_mod` files are committed; the generator config used should be noted in the PR.
- Hand-draw only non-standard packages, following KLC F4 to F7.
- Exposed/thermal pads: follow the datasheet's paste pattern and thermal-via recommendation (KLC F4.4).
- Footprint description must cite the datasheet: document name, revision, page/figure of the land pattern.
- 3D model reference: `${KIPRJMOD}/lib/dropout-kicad-library/3dmodels/<Lib>.3dshapes/<Footprint>.step` (approved exception `model-path-kiprjmod`). Scale 1:1:1, offset and rotation 0 (KLC F9.3).

## 4. 3D model

- Prefer the **kicad-library-tools 3D model generators** (CadQuery). They give accurate standard packages and satisfy KLC M1.3 (source supplied) and M1.1 (right to share).
- Manufacturer STEP only if its license clearly allows redistribution in a public repo; record the source and license in the PR. If unsure, generate instead.
- Never commit SnapMagic, Ultra Librarian, or SamacSys models.

## 5. Symbol

- Build it **from the datasheet pin table**, programmatically when the part has more than ~20 pins, so each pin number and name is copied, not retyped. For large BGAs use the manufacturer's pinout spreadsheet.
- Layout per KLC S3/S4: pins grouped by function, power on top/bottom, inputs left, outputs right, 100 mil grid, correct electrical types, active-low naming (S4.7), hidden/stacked pins only as KLC allows.
- **Fields:** KLC S6.2 fields (Reference, Value, Footprint, Datasheet, Description, keywords) **plus** DropOut fields `Manufacturer`, `MPN`, `DigiKey_PN`, `Mouser_PN`. Only Reference and Value visible.
- Footprint field links to the DropOut footprint from step 3 (KLC S5.1); set footprint filters (S5.2).

## 6. Verify (all must pass before opening a PR)

1. `python3 scripts/check_symbol_fields.py symbols`: DropOut fields.
2. `python3 scripts/klc_check.py <changed files>`: KLC with exceptions. Fix every `FAIL`. Never add an exception to get a pass.
3. **Pin cross-check:** compare every pin number and name in the symbol against the datasheet table, and list any mismatch. If a SnapMagic/Ultra Librarian/SamacSys model is available via the user's Chrome sign-in, compare pin maps against it too, as a check only.
4. **Visual check:** export with `kicad-cli sym export svg` and `kicad-cli fp export svg` and look at them. Confirm pin 1 marking, courtyard, fab/silk outlines, and that the 3D model sits on the pads.

## 7. Deliver

- Commit symbol, footprint, model (and model source if generated) together: `Add <MPN>`.
- Push the branch and open a PR filling in `.github/pull_request_template.md`. Include the datasheet citation and the KLC check summary line.
- Do not merge it yourself unless the user says to.

## When the user corrects you

If the user changes how something should be done, and it's a lasting rule rather than a one-off, propose an edit to **this file** (or a new `klc-exceptions.yml` entry if it's a KLC deviation) so the correction applies to every future part.
