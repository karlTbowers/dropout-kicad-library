# DropOut Library Rules

## The standard: KLC, plus a short list of exceptions

DropOut follows the **KiCad Library Conventions** (https://klc.kicad.org/) in full: naming, symbol layout, pin types, footprint layers, land patterns, 3D models, all of it.

The only deviations are the ones listed in [`klc-exceptions.yml`](../klc-exceptions.yml), each with a reason and approval date. CI runs the official KLC checker from [kicad-library-tools](https://gitlab.com/kicad/libraries/kicad-library-tools) through `scripts/klc_check.py`, which waives exactly those exceptions and fails on anything else.

```bash
python3 scripts/klc_check.py                 # check the whole library
python3 scripts/klc_check.py --raw <files>   # also show the checker's full output
```

Results are `FAIL` (a checker error: fix it, CI fails), `WARN` (a checker warning: KLC allows these where the manufacturer's data requires it, e.g. a BGA's specified mask and paste margins; explain each one in the PR), or `WAIVED` (covered by `klc-exceptions.yml`).

### Adding an exception

1. Open a PR that adds **one** entry to `klc-exceptions.yml`: the rule ID(s), what it applies to, an optional `match` regex that narrows it to the specific message, the reason, and the date.
2. Keep each exception as narrow as possible. A `match` regex must match every detail line of a violation, so an unrelated problem under the same rule still fails.
3. Never add an exception just to make one part pass. Fix the part.

## DropOut additions to KLC

These are stricter than KLC or add things KLC doesn't cover.

### Fully specified (atomic) parts only

One symbol = one orderable part, named by MPN, with its footprint linked (KLC G2.1 "fully specified" symbols). DropOut does **not** use generic symbols. Passives are fully specified too: a 10 kΩ 0603 1% resistor and a 10 kΩ 0402 1% resistor are two symbols.

### Resistors and capacitors

Chip resistors and MLCCs show the short value (`10k`, `100nF`, handbook rule D-45) as Value, a row with their ratings and case size, and the MPN in smaller text (`klc-exceptions.yml`: `passive-short-value`, `passive-small-mpn`). The symbol name and `MPN` field keep the exact orderable code. They are generated from `parts/passives.yaml` by `scripts/passivegen.py`.

### Part numbers containing "/"

KiCad symbol names can't contain `/`, and KLC S6.2 requires Value to equal the symbol name. For an MPN like `XLD8A24CAHM3_A/I` the symbol name and Value use `_` (`XLD8A24CAHM3_A_I`) and the `MPN` field keeps the exact orderable code, which BOMs use.

### Every pin is its own pin

Every package pin gets its own visible pin on the symbol, including repeated power and ground pins (an MCU's 18 VSS balls are 18 pins) and no-connect pins. NC pins (and pads the datasheet says to leave floating) are visible pins of type `no_connect`, so ERC flags a wire to them; the `visible-nc-pins` exception waives KLC S4.6, which prefers them hidden. DropOut never combines pins: no KiCad native pin stacks and no hidden pins stacked under a visible one, even though KLC S4.3 allows stacking. Each pin can then be wired, decoupled, and checked individually. CI enforces this (`scripts/check_pin_pad_match.py`). One exception (user's decision 2026-10-26): a single-contact power terminal whose many press-fit or solder pins the manufacturer does not number separately (Würth REDCUBE) is one terminal, not many package pins: the symbol has one pin `1` and every pin pad in the footprint is numbered `1`, as in KiCad's stock REDCUBE footprints.

No text on a symbol overprints other text (handbook rule D-47): a box symbol is sized from its pin-name text, not its pin count, so no pin name runs into another (including a top or bottom pin's vertical name against the side pins' names), and no pin number or visible field runs into anything. Grow the body downward first so existing pins keep their positions. `scripts/check_symbol_text.py` checks every symbol in CI (each character counted as wide as the font size, a conservative KiCad 10 estimate), and `scripts/symbolgen.py` refuses to write a symbol that fails it.

### Required symbol fields

All KLC S6.2 fields, plus these DropOut fields, filled in (not blank):

| Field | Example | Notes |
|---|---|---|
| `Manufacturer` | `Texas Instruments` | Full manufacturer name |
| `MPN` | `TPS2HCS08AQPWPRQ1` | Exact orderable part number incl. packaging suffix |
| `DigiKey_PN` | `296-TPS2HCS08AQPWPRQ1CT-ND` | `-` only if not stocked |
| `Mouser_PN` | `595-TPS2HCS08AQPWPRQ1` | `-` only if not stocked |

Optional: `Temperature_Grade` (e.g. `AEC-Q100 Grade 1`), the rating fields of handbook rule D-45 (`Voltage`, `Tolerance`, `Dielectric`, `Power`) and `Case` (EIA case size, passives), `Notes`, `Reference_Manual` (link to a manufacturer document the part was built from that isn't the datasheet, e.g. a sign-in-gated reference manual holding the ball map; never commit the document itself). `scripts/check_symbol_fields.py` enforces these in CI.

The `Datasheet` field must be the **manufacturer's** URL, never a distributor copy. Datasheet PDFs are never committed.

### Parts with nothing to buy

(Adopted 2026-10-22.) Some library parts are features of the board itself, e.g. a bare copper test pad: there is no MPN and nothing to order or place. They still carry every required field, filled in like this:

| Field | Value |
|---|---|
| Symbol name, `Value`, `MPN` | A KLC-style name for the feature, e.g. `TestPoint_Pad_D1.0mm` (usually the footprint name) |
| `Manufacturer` | `DropOut` |
| `DigiKey_PN`, `Mouser_PN` | `-` |
| `Datasheet` | The generator or document that defines the feature (e.g. a link to the footprint script) |
| `Notes` | "PCB copper only; nothing to order." |

The symbol is marked `(in_bom no)` and `(in_pos_files no)` (`in_bom: false`, `in_pos_files: false` in `part.yaml`), and the footprint has the attributes `exclude_from_bom exclude_from_pos_files`. Then BOM and placement exports leave it out, and `Manufacturer: DropOut` never reaches a purchasing list. This applies only to parts that are pure PCB features; anything with a physical part to buy uses the real MPN.

### Parts not placed on the PCB

(Adopted 2026-10-28.) Some parts are bought for a board but never placed on it, e.g. a panel-mount power connector (Amphenol SurLok Plus `SLPRATPSB`) whose M6 stud screws into a board terminal (Würth REDCUBE `74660016`) that is placed as its own part. Such a part has a symbol and a 3D model but **no footprint**:

- The symbol is marked `(on_board no)` and `(in_pos_files no)` (`on_board: false`, `in_pos_files: false` in `part.yaml`). It stays in the schematic and the BOM but is never sent to the PCB. `Footprint` is empty and there is no `ki_fp_filters`; `scripts/check_symbol_fields.py` accepts a blank `Footprint` only on such symbols.
- Every other required field is filled in as usual (real MPN, distributor PNs).
- The 3D model lives in `3dmodels/DropOut_Connector_<Vendor>.3dshapes/`, named `<Vendor>_<Series>_<MPN>` when variants differ only in colour. `Notes` gives its path and how to add it to the board terminal's footprint (offset).
- The KLC symbol checker warns S5.2 ("No footprint filters defined") on these symbols; that warning is expected.

### Library names

`DropOut_<Category>`, where `<Category>` follows KLC functional naming (see README for the list). New categories need approval.

Microcontrollers are split by vendor: `DropOut_MCU_<Vendor>` (`DropOut_MCU_NXP`, `DropOut_MCU_Microchip`, `DropOut_MCU_ST`, …), with the vendor named as in KiCad's stock `MCU_<Vendor>_*` libraries. A new vendor's library needs no separate approval.

### 3D models

- Prefer models generated with kicad-library-tools (source supplied, license-clean for a public repo).
- Manufacturer STEP files only when their license allows redistribution; note source and license in the PR.
- Never commit SnapMagic, Ultra Librarian, or SamacSys models.

### Changing released parts

Projects pin this library as a submodule, so a change reaches a board only when that project updates. Even so:
- **Never silently change a land pattern** that existing boards use. Create a new footprint name or call the change out clearly in the PR and release notes.
- Field corrections (typos, updated distributor PNs) may be edited in place.

## Workflow

1. Branch from `main` (`add/<MPN>`).
2. Add symbol + footprint + 3D model in one PR titled `Add <MPN>`.
3. Run `check_symbol_fields.py` and `klc_check.py` locally; CI runs both again.
4. Complete the PR checklist, including the pin-by-pin datasheet check, which the scripts can't do.

Claude Code follows this process through the `add-part` skill in `.claude/skills/add-part/SKILL.md`.

## Tools

`scripts/setup_tools.sh` sets up everything on a Mac. Symbols are generated from `parts/<MPN>/part.yaml` and `pins.csv` by `scripts/symbolgen.py`; chip resistors and MLCCs get those files from one table, `parts/passives.yaml`, through `scripts/passivegen.py`; footprints and 3D models from specs in `generators/` by `scripts/generate_footprint.py`; `scripts/check_pin_pad_match.py` (also in CI) checks that every symbol's pins match its footprint's pads. Vendor source documents live in the private `dropout-vendor-docs` repo, never here.
