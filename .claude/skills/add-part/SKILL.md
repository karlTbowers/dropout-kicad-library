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
- **Check the code against the manufacturer's ordering guide** (the datasheet's "ordering information" / "product identification" / "device comparison" table), not distributor flags. Board BOMs and distributors are often wrong: Node60 listed LMQ66430**QMC5**RXBRQ1 (doesn't exist), XLD8A24CA (family only; the plain `HM3/I` code was obsolete), and distributors called LAN8670D0T-E/LMX AEC-Q100 when Microchip reserves "automotive" for the `…VAO` code. When the code is wrong, ambiguous or not orderable, show the user the real options (with the ordering-guide facts) and let them choose; then fix the board's parts data in a separate PR.
- **Several versions fit? Build them all.** When a BOM line has more than one orderable version that meets its requirement (package, window/tolerance, automotive vs. stocked code, packaging), make every one as its own atomic part, sharing `pins.csv` and footprints where identical; don't ask the user to pick (their standing rule, 2026-10-22). Only versions that meet the line's requirement: the right voltage and grade, not the whole family. Examples: `parts/LAN8670D0-E_LMXVAO` + `LAN8670D0T-E_LMX`, TMP175-Q1 in VSSOP-8 and SOIC-8, TPS3702-Q1 AX33 and CX33. Still ask when the BOM's code is wrong and no version is clearly meant.
- **Part search candidates: build every one.** After a part search (handbook `find-part`), add every candidate in the comparison table to the library, not only the selected one, including alternates and second sources (user's standing rule, 2026-10-22: "we might change these parts in the future"). A candidate that failed the requirement is built too; its `part.yaml` comment says why it was rejected. A candidate not stocked anywhere gets `-` for both distributor PNs. Example: Node60 10BASE-T1S CMC/ESD search (DEC-012), seven parts.

## 2. Get and archive the manufacturer documents

You need the datasheet, the package drawing with the recommended land pattern, and, for large parts, the pin/ball map (often a spreadsheet attached to a reference manual).

- **Use Claude Code's built-in browser** (`mcp__Claude_Browser__*`) for manufacturer sites. Don't ask the user which browser to use. It keeps a persistent profile already signed in to vendor sites (NXP and others). Scripted downloads (`curl`, the kicad-happy fetchers) are blocked by nxp.com. Public datasheet PDFs from TI (`https://www.ti.com/lit/ds/symlink/<part>.pdf`), Microchip, ISSI, Vishay and ECS download fine with `curl -sSL -A "Mozilla/5.0 …"`; check the result with `file` (an HTML error page means use the browser). Claude in Chrome is only a fallback.
- Navigating the browser to a PDF or download link saves it to `~/Downloads`. If a PDF opens in the viewer instead, save it from the page: `javascript_tool` → `fetch(location.href)` → blob → `<a download>` click.
- If a sign-in form appears, ask the user to sign in in the browser pane. Claude never types passwords, even though they're in the credentials file. The sign-in persists for later sessions.
- Prefer the manufacturer's own copy and **check its revision**: distributor mirrors go stale (Newark served S32K3xx datasheet Rev. 12 when NXP had Rev. 14).
- NXP specifics: datasheet `https://www.nxp.com/docs/en/data-sheet/<name>.pdf`; reference manual `https://www.nxp.com/webapp/Download?colCode=<DOCID>` (sign-in); package code via `https://www.nxp.com/part/<MPN>` → package link `https://www.nxp.com/packages/<SOTxxxx>` → `https://www.nxp.com/docs/en/package-information/<SOTxxxx>.pdf`. The IOMUX/ball-map spreadsheet is a PDF attachment of the reference manual: `pdfdetach -list RM.pdf`, `pdfdetach -save N -o <file>.xlsx RM.pdf`.
- Read PDFs with `pdftotext -layout` (text, tables) and the Read tool with `pages` for figures (land patterns are drawings).
- **Archive every document used** in the private repo `~/Dev/dropout-vendor-docs`, under `<Manufacturer>/<family>/` (package drawings under `<Manufacturer>/packages/`) with the original file name. Add a row to its README index (revision, source URL, sign-in yes/no, date retrieved, first 16 hex digits of `shasum -a 256`, what it was used for), then commit and push. This is the default for every part.
- **Never commit vendor documents to this public repo**, including anything sign-in-gated or marked confidential. The part links to them instead: `Datasheet` field (manufacturer URL), optional `Reference_Manual` field (URL of the gated document), and `Notes` naming the exact attachment/sheet the pin data came from.

## 3. Decide symbol, footprint, and model names

- **Symbol library:** the existing `DropOut_<Category>` that fits (README table). A new category needs the user's OK. Microcontrollers go in `DropOut_MCU_<Vendor>` (vendor named as in KiCad's stock `MCU_<Vendor>_*` libraries, e.g. `DropOut_MCU_NXP`, `DropOut_MCU_ST`); a new vendor library is pre-approved.
- **Footprint library:** KLC package-type naming with the DropOut prefix, e.g. `DropOut_Package_BGA`. A new one needs the user's OK and a README table row.
- **Symbol name:** the MPN (KLC S2, DropOut atomic parts).
- **Footprint name:** per KLC F2/F3, as kicad-library-tools would name it. Vendor-specific layouts (e.g. a depopulated BGA) get a vendor prefix: `NXP_LFBGA-257_14x14mm_Layout17x17_P0.8mm`. **Reuse** an existing DropOut footprint if the land pattern is identical.
- **3D model:** same name as the footprint, `.step`, in `3dmodels/<FootprintLibrary>.3dshapes/`. KLC F9.3 drops name fields that don't change the body: footprints such as `R_0603_1608Metric_Pad0.7x0.7mm` and `..._Pad0.8x1.0mm` share `R_0603_1608Metric.step`.

## 4. Footprint and 3D model

- Standard packages (BGA, QFN, SOIC, SOT, chip passives…): add a spec in the kicad-library-tools YAML format to `generators/<generator>/DropOut_<Vendor>.yaml` (mirrors the tools' `data/<generator>/`; copy a similar stock entry from `~/.cache/dropout/kicad-library-tools/data/...`). Take dimensions from the manufacturer's **recommended land pattern**: pad, mask opening, paste opening, stencil. Note the source page/figure in comments.
- Generate: `PY scripts/generate_footprint.py generators/<generator>/<file>.yaml --lib DropOut_<Lib>`. It runs the pinned generator in a throwaway worktree (that's why `PYTHONPATH` matters; the script handles it), writes the footprint and STEP into the library, and rewrites the model path to `${KIPRJMOD}/lib/dropout-kicad-library/3dmodels/<Lib>.3dshapes/<name>.step`.
- **Legacy generators** (e.g. `crystal_resonator_oscillator`) read 3D-model specs only from their stock `cq_parameters.yaml`: put ours in `<spec stem>.cq_parameters.yaml` next to the spec and `generate_footprint.py` merges it (`generators/crystal_resonator_oscillator/`). A generator with no model generator at all (e.g. `connector/pin_header_socket`) gets its STEP from a model-only script in `generators/custom/` (`Samtec_FTSH-105-01-x-DV.py`).
- **Check the generated name's pad count** against the datasheet (it's computed from the spec: a wrong skip list shows up as `LFBGA-255`).
- BGA gotchas: row letters skip I, O, Q, S, X, Z; `row_skips` needs one entry per row; a range `[5, 14]` excludes the end.
- **Stock names:** when our part has the same name as a stock spec (e.g. `SOIC-8_3.9x4.9mm_P1.27mm`), `generate_footprint.py` removes the stock entry (and entries inheriting from it) in its worktree, so ours wins. Don't work around this.
- Useful generator knobs (copy from a similar stock entry): gullwing `pad_to_pad_min_x_overwrite` / `pad_to_pad_max_x_overwrite` / `pad_size_y_overwrite` (manufacturer pads), `EP_size_x_overwrite` + `EP_mask_x` (PowerPAD copper vs. solder-mask-defined opening); no_lead `pad_length` / `pad_width` / `pad_center_to_center_x|y` (manufacturer pads), `EP_paste_coverage` + `EP_num_paste_pads`. The gullwing generator needs `default_parameters: library_Suffix` and consistent heights (`body_height` max + `body_pcb_gap` max = `overall_height` max).
- **Pad 1 orientation:** compare the generated pad numbering with the datasheet's *top view*. The generator numbers counter-clockwise from a fixed corner; a part whose drawing has pins on other edges may need the spec rotated 90° (see `generators/package/no_lead/DropOut_ECS.yaml`). A mirrored footprint passes every check, including pin/pad match.
- Exposed/thermal pads get the manufacturer's number if it has one (TI: 15, 25, 17…), else N+1.
- **Non-standard packages** (L-shaped pads, asymmetric pads like DO-218, anything no generator covers): a script in `generators/custom/` using `generators/custom/fplib.py` (pads, custom pads, silk/fab/courtyard, text, `kicad-cli` normalisation, coloured CadQuery STEP). Examples: `Texas_RXB0014A.py`, `D_DO-218AC.py`. Follow KLC F4–F7 and KiCad's stock conventions (silk 0.12, fab 0.10, courtyard 0.05 lines at ≥ 0.25 clearance, silk ≥ 0.2 from copper); cite the datasheet figure in the description.
- Expected KLC warnings: F6.3 on thermal pads with split paste or separate mask/paste apertures; F9.2 on BGAs with manufacturer mask/paste margins. Explain them in the PR.
- 3D models are generated (CadQuery, source in kicad-library-tools). A manufacturer STEP only if its license allows public redistribution (record source and license in the PR). Never SnapMagic, Ultra Librarian or SamacSys models.

## 5. Symbol

- Every symbol is generated: `parts/<MPN>/part.yaml` (fields, unit order) + `parts/<MPN>/pins.csv` (number, name, type, unit, side, slot, alternates). Format: `scripts/symbolgen.py --help`. Example: `parts/S32K344EHT1MMMST/`.
- Make `pins.csv` from the manufacturer's pin table, never by retyping:
  - NXP IOMUX spreadsheets: `PY scripts/pintables/nxp_iomux.py <IOMUX.xlsx> --device <dev> --package <pkg> [--type NAME=TYPE ...] -o parts/<MPN>/pins.csv`.
  - Another vendor's spreadsheet or CSV: write a new adapter in `scripts/pintables/` (same output columns) and commit it.
  - Small parts: build the CSV from the datasheet pin table text (`pdftotext -layout`), then check every row against the PDF.
- **Two-terminal parts** (TVS, diodes, passives) and crystals use a graphic style instead of a box: `style: tvs_bidirectional`, `style: crystal_gnd24` (4-pin crystal, lid pins drawn as two visible bottom pins, not KiCad's stacked pair), `style: cmc_4pin` (two-line common mode choke as KiCad's `Filter:Choke_CommonMode_FerriteCore_1234`, Reference `FL`; pins L/R slot 0 = top winding, slot 1 = bottom winding, numbered per the vendor: TDK ACT1210E 1-4/2-3, Murata DLW32MH 1-2/4-3) in `part.yaml` (add new styles to `STYLES` in `symbolgen.py`), pins A1/A2 or 1/2 on sides L/R, names and numbers hidden as in KiCad's stock `Device` symbols. `style: thermistor_ntc` draws KiCad's `Device:Thermistor_NTC` horizontally (pins named `~`); thermistors take Reference `RT` (the KLC checker's list has no `TH`).
- **Part numbers with `/`** (`XLD8A24CAHM3_A/I`, `LAN8670D0T-E/LMX`): the symbol name and Value replace `/` with `_` (KiCad names can't contain `/`, KLC S6.2 needs Value = name); the `MPN` field keeps the exact code. The `parts/` folder uses the symbol name.
- KLC type rules the checker enforces (errors): pins named like `VCC`/`VDD`/`VIN`/`GND` must be `power_in` (S4.4), even an internal-LDO "VCC" output (note in `part.yaml` that its net needs a PWR_FLAG); on a symbol with both power inputs and outputs (regulators, switches), power inputs go on the **left** (S4.2); `ki_keywords` must not contain filler words such as "or" (S6.2: write "ORing", not "OR-ing"); reference designators come from KLC's list (oscillators `Y`, not `X`). NC pins are visible pins of type `no_connect` (the user's decision 2026-10-22; KLC S4.6's "should be invisible" is waived by `visible-nc-pins`, but a wrong pin type still fails); pads the datasheet says to leave floating are `no_connect` too, so ERC flags a wire (LM74910H RTN).
- Electrical types come from the datasheet, not the pin name: e.g. S32K3 V11/V25 are power **outputs** ("internally regulated", Table 3) on S32K344 but V11 is an input on S32K388. Record the reasoning as a comment in `part.yaml`.
- Layout (`symbolgen` enforces it): inputs left, outputs right, supplies top, grounds bottom; big parts in units (power/clock, then one per port or function); **every package pin is its own visible pin: never combine pins** (no KiCad native pin stacks, no hidden pins stacked under a visible one, even for 18 identical VSS balls; DropOut rule, stricter than KLC S4.3); active-low names as `~{NAME}` (KLC S4.7); pins whose reset default is a special function carry it in the name (`PTA5/~{RESET}`).
- Fields: KLC S6.2 fields plus `Manufacturer`, `MPN`, `DigiKey_PN`, `Mouser_PN`; optional `Temperature_Grade`, `Notes`, `Reference_Manual`. Only Reference and Value visible. Footprint links to the step 4 footprint; set `ki_fp_filters`.
- Generate: `PY scripts/symbolgen.py parts/<MPN>/part.yaml` (writes/replaces the symbol in `symbols/<Library>.kicad_sym`, normalised by `kicad-cli`).

## 6. Verify (all before a PR)

1. `python3 scripts/check_symbol_fields.py symbols`
2. `python3 scripts/check_pin_pad_match.py`: no combined pins, and symbol pins equal footprint pads.
3. `PY scripts/klc_check.py <changed files>`: `FAIL` = checker error, fix it. `WARN` = checker warning, allowed only where the manufacturer's data requires it; explain each one in the PR. `WAIVED` = covered by `klc-exceptions.yml`. Never add an exception to get a pass. Expected warnings so far: F9.2 on generated BGAs (manufacturer mask/paste margins, same as KiCad stock), S4.5 on depopulated BGAs (empty grid positions read as missing pins).
4. **Independent pin cross-check:** compare against a second manufacturer source, e.g. a datasheet figure listing supply balls, or the vendor's own CAD symbol in a hardware design package. If the manufacturer's sources disagree (e.g. a pad-type typo), say which one wins and why in the PR. Aggregator models (SnapMagic, Ultra Librarian, SamacSys) are a check only.
5. **Look at it:** `PY scripts/render_part.py <Library>:<Symbol>` writes a PNG per symbol unit and of the footprint and prints the STEP bounding box; Read the PNGs (for a small footprint, render with `--size 6000` and crop with `sips -c H W --cropOffset Y X`). Check every unit after the final regeneration: pin names and numbers readable and not overlapping, every package pin visible, pin 1 marking, courtyard, fab/silk. The 3D bounding box matches the body size and sits at z = 0.

## 7. Deliver

- Commit together: symbol library, `parts/<MPN>/`, generator spec, footprint, STEP, README row if a category was added. Message `Add <MPN>`.
- Push and open a PR filling in `.github/pull_request_template.md`: datasheet with revision, the documents used (archived in dropout-vendor-docs), land-pattern figure, KLC summary line with each WARN explained, cross-check results.
- Don't merge unless the user says to. **Stacked PRs:** before deleting a merged PR's branch, retarget the next PR to `main` (`gh pr edit N --base main`). Deleting a base branch with `gh pr merge --delete-branch` *closes* the PRs stacked on it.
- After merge, the board repo picks the part up with a submodule update; set its `library:` field in the board's parts data.

## When the user corrects you

If the user changes how something should be done, and it's a lasting rule rather than a one-off, edit **this file** (or propose a `klc-exceptions.yml` entry if it's a KLC deviation) so the correction applies to every future part. If it's company-wide process, also propose the handbook change (chapter 04 or 07).
