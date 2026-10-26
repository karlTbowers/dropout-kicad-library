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

## 2a. Check trusted KiCad libraries

Before building anything, look for the part in the trusted libraries listed in `docs/trusted-kicad-libraries.md`
(KiCad's official libraries, CERN's, and every manufacturer-supported library listed there), and search for
the **manufacturer's own official KiCad library** (e.g. "<manufacturer> KiCad library" on GitHub/GitLab and the
manufacturer's EDA/CAD download page). A newly found official vendor library goes on that list.

- **Decide case by case** (user's rule, 2026-10-26): a trusted library is a source to compare against, never
  an automatic replacement for our own work. Compare what it has (symbol pin map, land pattern, drills,
  keep-outs, 3D model) with the data sheet, show the user the differences that matter, and decide per part
  what to reuse and what to build. Example: Würth's REDCUBE 3D models were clearly better than our envelopes
  (side-by-side renders), so we use them; we kept our own silk, fab and courtyard (with the 4 mm keep-out
  Würth's footprint lacks).
- Reused items still follow KLC and DropOut rules (fields, never combine pins, model named like the
  footprint at zero offset). Respect the library's license: record source, version/commit and license in
  `part.yaml` and the PR, mark modified models as the license requires, and archive the license in
  `dropout-vendor-docs`.
- Compare 3D models visually: put both on two copies of the footprint and render them side by side with
  `python3 scripts/compare_models.py <Lib>:<footprint> ours.step theirs.step -o <prefix>`.

## 3. Decide symbol, footprint, and model names

**Library names match KiCad's stock libraries** as closely as possible, with the `DropOut_` prefix and DropOut's own additions where KiCad has no equivalent (user's rule, 2026-10-23). Check KiCad's stock library list before naming a new one: `DropOut_Connector_Samtec` ↔ `Connector_Samtec`, `DropOut_Connector_TE-Connectivity` ↔ `Connector_TE-Connectivity`, `DropOut_Package_BGA` ↔ `Package_BGA`.

- **Symbol library:** the existing `DropOut_<Category>` that fits (README table). A new category needs the user's OK. Microcontrollers go in `DropOut_MCU_<Vendor>` (vendor named as in KiCad's stock `MCU_<Vendor>_*` libraries, e.g. `DropOut_MCU_NXP`, `DropOut_MCU_ST`); a new vendor library is pre-approved.
- **Footprint library:** KiCad's stock footprint library name with the DropOut prefix: KLC package-type naming (`DropOut_Package_BGA`) or, for vendor connectors, the stock vendor library (`DropOut_Connector_TE-Connectivity`). A new one needs the user's OK and a README table row.
- **Symbol name:** the MPN (KLC S2, DropOut atomic parts).
- **Footprint name:** per KLC F2/F3, as kicad-library-tools would name it. Vendor-specific layouts (e.g. a depopulated BGA) get a vendor prefix: `NXP_LFBGA-257_14x14mm_Layout17x17_P0.8mm`. **Reuse** an existing DropOut footprint if the land pattern is identical.
- **3D model:** same name as the footprint, `.step`, in `3dmodels/<FootprintLibrary>.3dshapes/`. KLC F9.3 drops name fields that don't change the body: footprints such as `R_NTC_0603_1608Metric_Pad0.7x0.7mm` and `..._Pad0.8x1.0mm` share `R_NTC_0603_1608Metric.step`. A body that differs from the IPC part of the same size (an NTC chip is 0.8 mm thick, a chip resistor 0.45 mm) needs its own base name, or its model would overwrite the IPC part's.

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
- **3D model frame: KiCad's model Y is the footprint's −y** (X = x, Z up from the board). A custom CadQuery model built in footprint coordinates must be mirrored (`.mirror("XZ")`) before export, as `generators/custom/dt_header.py` does; a part that is not symmetric front to back otherwise ends up reversed (DT13-2P's shroud pointed behind the pins until 2026-10-25). Check every asymmetric model with `kicad-cli pcb render --side bottom` and an angled `--side top --rotate "-50,0,30"` view of a board holding the footprint: housings should show through the mounting holes and the mating face should point the right way.
- Expected KLC warnings: F6.3 on thermal pads with split paste or separate mask/paste apertures; F9.2 on BGAs with manufacturer mask/paste margins. Explain them in the PR.
- 3D models are generated (CadQuery, source in kicad-library-tools). A manufacturer STEP only if its license allows public redistribution (record source and license in the PR). Never SnapMagic, Ultra Librarian or SamacSys models.
  - Manufacturer models from a vendor's own CADENAS/PARTcommunity catalog are allowed when the file is CC-licensed or the vendor has agreed to publication; CADENAS's own terms otherwise forbid redistribution. Check the STEP header (`author` field) and record the permission in the PR and the vendor-docs index; archive the original there.
  - KLC F9.3 wants zero model offset and rotation, so a vendor STEP that is not drawn in the footprint frame must be re-placed, never offset in the footprint, and only when the vendor allows modification (CC BY-ND forbids it). Wrap the vendor solid in a placed assembly so geometry and colours stay untouched: `generators/custom/Amphenol_AT13-2P-BMxx_step.py`. Check the model's pins, bosses and outline against the drawing before relying on it.

## 5. Symbol

- Every symbol is generated: `parts/<MPN>/part.yaml` (fields, unit order) + `parts/<MPN>/pins.csv` (number, name, type, unit, side, slot, alternates). Format: `scripts/symbolgen.py --help`. Example: `parts/S32K344EHT1MMMST/`.
- Make `pins.csv` from the manufacturer's pin table, never by retyping:
  - NXP IOMUX spreadsheets: `PY scripts/pintables/nxp_iomux.py <IOMUX.xlsx> --device <dev> --package <pkg> [--type NAME=TYPE|BALL=TYPE ...] -o parts/<MPN>/pins.csv`.
  - Another vendor's spreadsheet or CSV: write a new adapter in `scripts/pintables/` (same output columns) and commit it.
  - Small parts: build the CSV from the datasheet pin table text (`pdftotext -layout`), then check every row against the PDF.
- **Two-terminal parts** (TVS, diodes, passives) and crystals use a graphic style (resistors and MLCCs: see 5a) instead of a box: `style: tvs_bidirectional`, `style: crystal_gnd24` (4-pin crystal, lid pins drawn as two visible bottom pins, not KiCad's stacked pair), `style: cmc_4pin` (two-line common mode choke as KiCad's `Filter:Choke_CommonMode_FerriteCore_1234`, Reference `FL`; pins L/R slot 0 = top winding, slot 1 = bottom winding, numbered per the vendor: TDK ACT1210E 1-4/2-3, Murata DLW32MH 1-2/4-3), `style: testpoint` (one-pin test point as KiCad's `Connector:TestPoint`, Reference `TP`, symbol library `DropOut_Connector`, footprints in `DropOut_TestPoint` from `generators/custom/TestPoint.py`), `style: resistor` (KiCad's `Device:R`, pins 1/2 on T/B), `style: resistor_shunt_4pin` (Kelvin shunt as KiCad's `Device:R_Shunt`: force pins T/B, sense pins R slot 0 next to the top force pin, slot 1 next to the bottom; numbered 1/4 force, 2/3 sense), `style: nmos` (KiCad's `Device:Q_NMOS` drawing with every package pin its own pin: gate L, drain pins T, source pins B on buses; a second gate on R draws two FETs in parallel, e.g. Infineon's dual-gate LINFET/ONFET, `parts/IAUTN08S5N012LATMA1`), `style: inductor` (power inductor drawn as KiCad's `Device:L`, vertical, pins 1/2 on sides T/B, Reference `L`; Reference and Value beside the body) in `part.yaml` (add new styles to `STYLES` in `symbolgen.py`), pins A1/A2 or 1/2 on sides L/R, names and numbers hidden as in KiCad's stock `Device` symbols. `style: thermistor_ntc` draws KiCad's `Device:Thermistor_NTC` horizontally (pins named `~`); thermistors take Reference `RT` (the KLC checker's list has no `TH`).
- **Part numbers with `/`, `=` or a space** (`XLD8A24CAHM3_A/I`, `LAN8670D0T-E/LMX`, Murata `DFE322520FD-1R0M=P2`, `TSM018NM08TL RAG`): the symbol name and Value replace `/`, `=` or the space with `_` (KiCad names can't contain `/`, the KLC checker rejects `=` under G1.1, KLC S6.2 needs Value = name); the `MPN` field keeps the exact code. The `parts/` folder uses the symbol name.
- KLC type rules the checker enforces (errors): pins named like `VCC`/`VDD`/`VIN`/`GND` must be `power_in` (S4.4), even an internal-LDO "VCC" output (note in `part.yaml` that its net needs a PWR_FLAG); on a symbol with both power inputs and outputs (regulators, switches), power inputs go on the **left** (S4.2); `ki_keywords` must not contain filler words such as "or" (S6.2: write "ORing", not "OR-ing"); reference designators come from KLC's list (oscillators `Y`, not `X`). NC pins are visible pins of type `no_connect` (the user's decision 2026-10-22; KLC S4.6's "should be invisible" is waived by `visible-nc-pins`, but a wrong pin type still fails); pads the datasheet says to leave floating are `no_connect` too, so ERC flags a wire (LM74910H RTN).
- Electrical types come from the datasheet, not the pin name: e.g. S32K3 V11/V25 are power **outputs** ("internally regulated", Table 3) on S32K344 but V11 is an input on S32K388. Record the reasoning as a comment in `part.yaml`.
- **Parallel pins of one power output** (TPS2HCS08 VOUT1 on 6/7/8, S32K344 V11 on four balls): the lowest-numbered pin (the first ball for BGAs) is `power_out`, the others `passive`, all visible with the same name, so ERC sees one driver and no power_out–power_out conflicts (the user's decision 2026-10-22). KLC S4.4 warns (not fails) on passive pins named `VOUT*`; accept it. With `nxp_iomux.py`, add `--type <BALL>=passive` per extra ball and record the command in `part.yaml`. A regulator's sense/feedback pin (LMQ66430 VOUT/FB) is `input`, not `power_out`, even when wired to the output; the output net then needs a PWR_FLAG.
- Layout (`symbolgen` enforces it): inputs left, outputs right, supplies top, grounds bottom; big parts in units (power/clock, then one per port or function); **every package pin is its own visible pin: never combine pins** (no KiCad native pin stacks, no hidden pins stacked under a visible one, even for 18 identical VSS balls; DropOut rule, stricter than KLC S4.3; the one exception is a single-contact power terminal whose press-fit pins the manufacturer does not number, e.g. Würth REDCUBE: one symbol pin `1`, every pad `1`, user's decision 2026-10-26, see `generators/custom/Wuerth_REDCUBE_PressFit.py`); active-low names as `~{NAME}` (KLC S4.7); pins whose reset default is a special function carry it in the name (`PTA5/~{RESET}`).
- **Parts with nothing to buy** (a bare copper test pad): `in_bom: false` and `in_pos_files: false` in `part.yaml`, and the footprint attributes `exclude_from_bom exclude_from_pos_files`. Fields (adopted 2026-10-22, `docs/CONTRIBUTING.md` "Parts with nothing to buy"): symbol name = `Value` = `MPN` = a KLC-style feature name, `Manufacturer: DropOut`, distributor PNs `-`, `Datasheet` = the defining generator, `Notes`: "PCB copper only; nothing to order." Example: `parts/TestPoint_Pad_D1.0mm/`.
- Fields: KLC S6.2 fields plus `Manufacturer`, `MPN`, `DigiKey_PN`, `Mouser_PN`; optional `Temperature_Grade`, `Notes`, `Reference_Manual`. Only Reference and Value visible. Footprint links to the step 4 footprint; set `ki_fp_filters`.
- Generate: `PY scripts/symbolgen.py parts/<MPN>/part.yaml` (writes/replaces the symbol in `symbols/<Library>.kicad_sym`, normalised by `kicad-cli`).

## 5a. Chip resistors and MLCCs

- **Don't hand-write their part.yaml.** Add a row to `parts/passives.yaml` (a `families` entry once per ordering-code family: manufacturer, datasheet, construction, temperature range, source document) and run `PY scripts/passivegen.py --mpn <MPN>`. It writes `parts/<MPN>/part.yaml` + `pins.csv` (style `resistor` or `capacitor`, as KiCad's `Device:R`/`Device:C`) and builds the symbol.
- **Symbol layout** (handbook rule D-45, user's decision 2026-10-23; `LAYOUT = "d45"` in `passivegen.py`): beside the body, rows `R1` / short value (`10k`, `100nF`) / ratings and case (resistors `±5%  50V  0402`: `Tolerance`, `Voltage`, `Case`; MLCCs `16V  X7R  ±10%  0402`: `Voltage`, `Dielectric`, `Tolerance`, `Case`) / the `MPN` in 1.0 mm text. Each is its own field, placed per part by `field_layout` in `part.yaml`. `Power` is a hidden field; 0 Ω jumpers have no rating fields (current rating in Description). Ratings are written compact (`50V`, `1/16W`). KLC deviations: `passive-short-value` and `passive-small-mpn`, plus the rating and `Case` fields in `dropout-symbol-fields`. `--layout mpn --out DIR` previews the plain KLC layout.
- **Footprints:** one per size code in `DropOut_Resistor_SMD` / `DropOut_Capacitor_SMD`, generated by `SMD_2terminal_chip_molded` from `generators/SMD_2terminal_chip_molded/DropOut_<Lib>.yaml` (IPC-7351 nominal, as KiCad stock). A new manufacturer on an existing size: widen that size's body envelope to cover its datasheet (comment the figures), regenerate, and say in the PR how the land moved. A new size: add an entry (and its model in the `.cq_parameters.yaml`, height = the tallest part).
- **Finding parts:** DigiKey's keyword search can't filter passives by description. Use its parametric filters: category 52 (chip resistors) or 60 (ceramic capacitors), `Ratings` = AEC-Q200 (ValueId 312105; resistors are often tagged only under `Features` "Automotive AEC-Q200"), `Package / Case`, `Temperature Coefficient`, and the value as text (`"0.1 µF"`, `"32 kOhms"`). Check the code in the manufacturer's ordering table: TDK codes not in its catalog tables, Murata GCM vs GRT/GCJ, packaging codes (Murata D/L = 180 mm reel; TDK A/B = 178 mm reel).
- **Jumper current:** a 0 Ω part's rated current is not its maximum overload current (Yageo AC0603, Panasonic ERJ-3GEY and KOA RK73Z1J are 1 A rated, 2 A overload).
- **Rate limits:** DigiKey (about 1000 calls a day) and Mouser answer 429/403 after bulk searches. Cache responses; refresh prices later rather than looping.

## 6. Verify (all before a PR)

1. `python3 scripts/check_symbol_fields.py symbols`
2. `python3 scripts/check_pin_pad_match.py`: no combined pins, and symbol pins equal footprint pads.
   `python3 scripts/check_symbol_text.py`: no pin name, pin number or visible field overprints another (handbook D-47; the user's decision 2026-10-22: no overlapping text in DropOut symbols). symbolgen already refuses such a layout; for a hand-made or style symbol, fix the geometry, never the check.
3. `PY scripts/klc_check.py <changed files>`: `FAIL` = checker error, fix it. `WARN` = checker warning, allowed only where the manufacturer's data requires it; explain each one in the PR. `WAIVED` = covered by `klc-exceptions.yml`. Never add an exception to get a pass. Expected warnings so far: F9.2 on generated BGAs (manufacturer mask/paste margins, same as KiCad stock), S4.5 on depopulated BGAs (empty grid positions read as missing pins), S4.4 on the passive extra pins of one power output and on sense pins named `VOUT*` typed `input` (see the parallel-pins rule above).
4. **Independent pin cross-check:** compare against a second manufacturer source, e.g. a datasheet figure listing supply balls, or the vendor's own CAD symbol in a hardware design package. If the manufacturer's sources disagree (e.g. a pad-type typo), say which one wins and why in the PR. Aggregator models (SnapMagic, Ultra Librarian, SamacSys) are a check only.
5. **Look at it:** `PY scripts/render_part.py <Library>:<Symbol>` writes a PNG per symbol unit and of the footprint, KiCad 3D renders of the footprint with its model (`<footprint>_3d_top/bottom/iso.png`, the model as a board will show it, vendor STEP or generated), and prints the STEP bounding box; Read the PNGs (for a small footprint, render with `--size 6000` and crop with `sips -c H W --cropOffset Y X`). Check every unit after the final regeneration: pin names and numbers readable and not overlapping, every package pin visible, pin 1 marking, courtyard, fab/silk. The 3D bounding box matches the body size and sits at z = 0; in the 3D renders the model sits on its pads and faces the right way.

## 7. Deliver

- Commit together: symbol library, `parts/<MPN>/`, generator spec, footprint, STEP, README row if a category was added. Message `Add <MPN>`.
- Push and open a PR filling in `.github/pull_request_template.md`: datasheet with revision, the documents used (archived in dropout-vendor-docs), land-pattern figure, KLC summary line with each WARN explained, cross-check results.
- Don't merge unless the user says to. **Stacked PRs:** before deleting a merged PR's branch, retarget the next PR to `main` (`gh pr edit N --base main`). Deleting a base branch with `gh pr merge --delete-branch` *closes* the PRs stacked on it.
- After merge, the board repo picks the part up with a submodule update; set its `library:` field in the board's parts data.

## When the user corrects you

If the user changes how something should be done, and it's a lasting rule rather than a one-off, edit **this file** (or propose a `klc-exceptions.yml` entry if it's a KLC deviation) so the correction applies to every future part. If it's company-wide process, also propose the handbook change (chapter 04 or 07).
