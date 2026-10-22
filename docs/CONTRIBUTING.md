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

### Every pin is its own pin

Every package pin gets its own visible pin on the symbol, including repeated power and ground pins (an MCU's 18 VSS balls are 18 pins). DropOut never combines pins: no KiCad native pin stacks and no hidden pins stacked under a visible one, even though KLC S4.3 allows stacking. Each pin can then be wired, decoupled, and checked individually. CI enforces this (`scripts/check_pin_pad_match.py`).

### Required symbol fields

All KLC S6.2 fields, plus these DropOut fields, filled in (not blank):

| Field | Example | Notes |
|---|---|---|
| `Manufacturer` | `Texas Instruments` | Full manufacturer name |
| `MPN` | `TPS2HCS08AQPWPRQ1` | Exact orderable part number incl. packaging suffix |
| `DigiKey_PN` | `296-TPS2HCS08AQPWPRQ1CT-ND` | `-` only if not stocked |
| `Mouser_PN` | `595-TPS2HCS08AQPWPRQ1` | `-` only if not stocked |

Optional: `Temperature_Grade` (e.g. `AEC-Q100 Grade 1`), `Notes`, `Reference_Manual` (link to a manufacturer document the part was built from that isn't the datasheet, e.g. a sign-in-gated reference manual holding the ball map; never commit the document itself). `scripts/check_symbol_fields.py` enforces these in CI.

The `Datasheet` field must be the **manufacturer's** URL, never a distributor copy. Datasheet PDFs are never committed.

### Library names

`DropOut_<Category>`, where `<Category>` follows KLC functional naming (see README for the list). New categories need approval.

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

`scripts/setup_tools.sh` sets up everything on a Mac. Symbols are generated from `parts/<MPN>/part.yaml` and `pins.csv` by `scripts/symbolgen.py`; footprints and 3D models from specs in `generators/` by `scripts/generate_footprint.py`; `scripts/check_pin_pad_match.py` (also in CI) checks that every symbol's pins match its footprint's pads. Vendor source documents live in the private `dropout-vendor-docs` repo, never here.
