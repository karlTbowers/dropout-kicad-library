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

Do every step below by default, without being asked, including archiving the source documents (step 2). The user has asked not to have to repeat any of it.

`PY` below means `~/.cache/dropout/klt-venv/bin/python` (made by `scripts/setup_tools.sh`).

## 0. Preconditions (once per session)

- `scripts/setup_tools.sh --check` passes. If not, run `scripts/setup_tools.sh` (installs gh, uv, poppler, git-lfs and the Python env with kicad-library-tools and CadQuery). KiCad 10 must already be installed. A brand-new machine: follow the handbook's "Setting up a new Mac" (chapter 07).
- Distributor keys are in the environment: `DIGIKEY_CLIENT_ID`, `MOUSER_SEARCH_API_KEY`, `NEWARK_SEARCH_API_KEY` (from `scripts/vendor-env.sh`). If not, tell the user and stop.
- `~/Dev/dropout-vendor-docs` exists (private; clone with `gh repo clone karlTbowers/dropout-vendor-docs ~/Dev/dropout-vendor-docs`).
- Start from an up-to-date `main` and branch: `git switch -c add/<MPN>`.

## 1. Identify the exact part

- Take the **orderable MPN including packaging suffix** from the board's architecture data (e.g. node60-hw `docs/src/data/parts.yaml`). Never pick or change a locked part yourself.
- `python3 scripts/distributor_lookup.py <MPN>`: manufacturer, DigiKey PN, Mouser PN, Newark SKU, lifecycle, stock, the datasheet URL and package. A distributor PN that genuinely doesn't exist is `-`. Obsolete or NRND: tell the user before continuing.

## 2. Get and archive the manufacturer documents

You need the datasheet, the package drawing with the recommended land pattern, and, for large parts, the pin/ball map (often a spreadsheet attached to a reference manual).

- **Use Claude Code's built-in browser** (`mcp__Claude_Browser__*`) for manufacturer sites. Don't ask the user which browser to use. It keeps a persistent profile already signed in to vendor sites (NXP and others). Scripted downloads (`curl`, the kicad-happy fetchers) are blocked by nxp.com and often by others. Claude in Chrome is only a fallback.
- Navigating the browser to a PDF or download link saves it to `~/Downloads`. If a PDF opens in the viewer instead, save it from the page: `javascript_tool` → `fetch(location.href)` → blob → `<a download>` click.
- If a sign-in form appears, ask the user to sign in in the browser pane. Claude never types passwords, even though they're in the credentials file. The sign-in persists for later sessions.
- Prefer the manufacturer's own copy and **check its revision**: distributor mirrors go stale (Newark served S32K3xx datasheet Rev. 12 when NXP had Rev. 14).
- NXP specifics: datasheet `https://www.nxp.com/docs/en/data-sheet/<name>.pdf`; reference manual `https://www.nxp.com/webapp/Download?colCode=<DOCID>` (sign-in); package code via `https://www.nxp.com/part/<MPN>` → package link `https://www.nxp.com/packages/<SOTxxxx>` → `https://www.nxp.com/docs/en/package-information/<SOTxxxx>.pdf`. The IOMUX/ball-map spreadsheet is a PDF attachment of the reference manual: `pdfdetach -list RM.pdf`, `pdfdetach -save N -o <file>.xlsx RM.pdf`.
- Read PDFs with `pdftotext -layout` (text, tables) and the Read tool with `pages` for figures (land patterns are drawings).
- **Archive every document used** in the private repo `~/Dev/dropout-vendor-docs`, under `<Manufacturer>/<family>/` (package drawings under `<Manufacturer>/packages/`) with the original file name. Add a row to its README index (revision, source URL, sign-in yes/no, date retrieved, first 16 hex digits of `shasum -a 256`, what it was used for), then commit and push. This is the default for every part.
- **Never commit vendor documents to this public repo**, including anything sign-in-gated or marked confidential. The part links to them instead: `Datasheet` field (manufacturer URL), optional `Reference_Manual` field (URL of the gated document), and `Notes` naming the exact attachment/sheet the pin data came from.

## 3. Decide symbol, footprint, and model names

- **Symbol library:** the existing `DropOut_<Category>` that fits (README table). A new category needs the user's OK.
- **Footprint library:** KLC package-type naming with the DropOut prefix, e.g. `DropOut_Package_BGA`. A new one needs the user's OK and a README table row.
- **Symbol name:** the MPN (KLC S2, DropOut atomic parts).
- **Footprint name:** per KLC F2/F3, as kicad-library-tools would name it. Vendor-specific layouts (e.g. a depopulated BGA) get a vendor prefix: `NXP_LFBGA-257_14x14mm_Layout17x17_P0.8mm`. **Reuse** an existing DropOut footprint if the land pattern is identical.
- **3D model:** same name as the footprint, `.step`, in `3dmodels/<FootprintLibrary>.3dshapes/`.

## 4. Footprint and 3D model

- Standard packages (BGA, QFN, SOIC, SOT, chip passives…): add a spec in the kicad-library-tools YAML format to `generators/<generator>/DropOut_<Vendor>.yaml` (mirrors the tools' `data/<generator>/`; copy a similar stock entry from `~/.cache/dropout/kicad-library-tools/data/...`). Take dimensions from the manufacturer's **recommended land pattern**: pad, mask opening, paste opening, stencil. Note the source page/figure in comments.
- Generate: `PY scripts/generate_footprint.py generators/<generator>/<file>.yaml --lib DropOut_<Lib>`. It runs the pinned generator in a throwaway worktree (that's why `PYTHONPATH` matters; the script handles it), writes the footprint and STEP into the library, and rewrites the model path to `${KIPRJMOD}/lib/dropout-kicad-library/3dmodels/<Lib>.3dshapes/<name>.step`.
- **Check the generated name's pad count** against the datasheet (it's computed from the spec: a wrong skip list shows up as `LFBGA-255`).
- BGA gotchas: row letters skip I, O, Q, S, X, Z; `row_skips` needs one entry per row; a range `[5, 14]` excludes the end.
- Hand-draw only non-standard packages, following KLC F4–F7; still cite the datasheet figure in the description.
- 3D models are generated (CadQuery, source in kicad-library-tools). A manufacturer STEP only if its license allows public redistribution (record source and license in the PR). Never SnapMagic, Ultra Librarian or SamacSys models.

## 5. Symbol

- Every symbol is generated: `parts/<MPN>/part.yaml` (fields, unit order) + `parts/<MPN>/pins.csv` (number, name, type, unit, side, slot, alternates). Format: `scripts/symbolgen.py --help`. Example: `parts/S32K344EHT1MMMST/`.
- Make `pins.csv` from the manufacturer's pin table, never by retyping:
  - NXP IOMUX spreadsheets: `PY scripts/pintables/nxp_iomux.py <IOMUX.xlsx> --device <dev> --package <pkg> [--type NAME=TYPE ...] -o parts/<MPN>/pins.csv`.
  - Another vendor's spreadsheet or CSV: write a new adapter in `scripts/pintables/` (same output columns) and commit it.
  - Small parts: build the CSV from the datasheet pin table text (`pdftotext -layout`), then check every row against the PDF.
- Electrical types come from the datasheet, not the pin name: e.g. S32K3 V11/V25 are power **outputs** ("internally regulated", Table 3) on S32K344 but V11 is an input on S32K388. Record the reasoning as a comment in `part.yaml`.
- Layout (`symbolgen` enforces it): inputs left, outputs right, supplies top, grounds bottom; big parts in units (power/clock, then one per port or function); **every package pin is its own visible pin: never combine pins** (no KiCad native pin stacks, no hidden pins stacked under a visible one, even for 18 identical VSS balls; DropOut rule, stricter than KLC S4.3); active-low names as `~{NAME}` (KLC S4.7); pins whose reset default is a special function carry it in the name (`PTA5/~{RESET}`).
- Fields: KLC S6.2 fields plus `Manufacturer`, `MPN`, `DigiKey_PN`, `Mouser_PN`; optional `Temperature_Grade`, `Notes`, `Reference_Manual`. Only Reference and Value visible. Footprint links to the step 4 footprint; set `ki_fp_filters`.
- Generate: `PY scripts/symbolgen.py parts/<MPN>/part.yaml` (writes/replaces the symbol in `symbols/<Library>.kicad_sym`, normalised by `kicad-cli`).

## 6. Verify (all before a PR)

1. `python3 scripts/check_symbol_fields.py symbols`
2. `python3 scripts/check_pin_pad_match.py`: no combined pins, and symbol pins equal footprint pads.
3. `PY scripts/klc_check.py <changed files>`: `FAIL` = checker error, fix it. `WARN` = checker warning, allowed only where the manufacturer's data requires it; explain each one in the PR. `WAIVED` = covered by `klc-exceptions.yml`. Never add an exception to get a pass. Expected warnings so far: F9.2 on generated BGAs (manufacturer mask/paste margins, same as KiCad stock), S4.5 on depopulated BGAs (empty grid positions read as missing pins).
4. **Independent pin cross-check:** compare against a second manufacturer source, e.g. a datasheet figure listing supply balls, or the vendor's own CAD symbol in a hardware design package. If the manufacturer's sources disagree (e.g. a pad-type typo), say which one wins and why in the PR. Aggregator models (SnapMagic, Ultra Librarian, SamacSys) are a check only.
5. **Look at it:** `kicad-cli sym export svg symbols/<Lib>.kicad_sym -o <dir>` and `kicad-cli fp export svg footprints/<Lib>.pretty -o <dir>`, convert with `qlmanage -t -s 1200 -o <dir> <file>.svg`, and Read the PNGs. Check every unit after the final regeneration: pin names and numbers readable and not overlapping, every package pin visible, pin 1 marking, courtyard, fab/silk. 3D model: `PY -c "import cadquery as cq; print(cq.importers.importStep('<file>.step').val().BoundingBox().__dict__)"` matches the body size and sits at z = 0.

## 7. Deliver

- Commit together: symbol library, `parts/<MPN>/`, generator spec, footprint, STEP, README row if a category was added. Message `Add <MPN>`.
- Push and open a PR filling in `.github/pull_request_template.md`: datasheet with revision, the documents used (archived in dropout-vendor-docs), land-pattern figure, KLC summary line with each WARN explained, cross-check results.
- Don't merge unless the user says to. **Stacked PRs:** before deleting a merged PR's branch, retarget the next PR to `main` (`gh pr edit N --base main`). Deleting a base branch with `gh pr merge --delete-branch` *closes* the PRs stacked on it.
- After merge, the board repo picks the part up with a submodule update; set its `library:` field in the board's parts data.

## When the user corrects you

If the user changes how something should be done, and it's a lasting rule rather than a one-off, edit **this file** (or propose a `klc-exceptions.yml` entry if it's a KLC deviation) so the correction applies to every future part. If it's company-wide process, also propose the handbook change (chapter 04 or 07).
