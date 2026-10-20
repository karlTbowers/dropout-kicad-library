# DropOut Library Rules

These rules keep the library trustworthy as it grows. CI enforces the symbol-field rules; reviewers check the rest.

## 1. Atomic parts

One symbol represents one orderable part. Do not create generic "R" or "C" symbols with values filled in later. A 10 kΩ 0603 1% resistor and a 10 kΩ 0402 1% resistor are two symbols.

## 2. Required symbol fields

Every symbol must have these fields, filled in (not blank):

| Field | Example | Notes |
|---|---|---|
| `Reference` | `U` | Standard KiCad prefix |
| `Value` | `TPS2HCS08A-Q1` | What prints on the schematic |
| `Footprint` | `DropOut_PowerSwitch:HTSSOP-16-1EP_4.4x5mm_P0.65mm` | Must point at a DropOut footprint |
| `Datasheet` | `https://www.ti.com/lit/gpn/TPS2HCS08-Q1` | Manufacturer URL, not a distributor copy |
| `Description` | `Dual-channel smart high-side switch, 8.9 mΩ, SPI, AEC-Q100 Grade 1` | One line |
| `Manufacturer` | `Texas Instruments` | Full manufacturer name |
| `MPN` | `TPS2HCS08AQPWPRQ1` | Exact orderable part number incl. packaging suffix |
| `DigiKey_PN` | `296-TPS2HCS08AQPWPRQ1CT-ND` | Use `-` if not stocked |
| `Mouser_PN` | `595-TPS2HCS08AQPWPRQ1` | Use `-` if not stocked |

Optional fields: `Temperature_Grade` (e.g. `AEC-Q100 Grade 1`), `Notes`.

Field names are case-sensitive. Only `Reference` and `Value` are visible on the schematic by default.

## 3. Naming

- **Libraries**: `DropOut_<Category>` (see README for the category list). Never put DropOut parts in KiCad's stock libraries.
- **Symbols**: the MPN without packaging suffix, e.g. `LM74910H-Q1`, `INA228A-Q1`. Passives: `R_10k_0603_1%`, `C_100n_0603_50V_X7R`.
- **Footprints**: IPC-7351-style descriptive names, e.g. `SOIC-8_3.9x4.9mm_P1.27mm`, `VQFN-24-1EP_4x4mm_P0.5mm`. Reuse an existing footprint when the land pattern is identical.
- **3D models**: same name as the footprint, `.step` format, in the matching `.3dshapes` folder.

## 4. Footprint rules

- Land pattern from the **manufacturer's recommended layout** in the datasheet; record the datasheet page/figure in the footprint description.
- Pin 1 marked on silkscreen and fab layer.
- Courtyard on `F.CrtYd`, 0.25 mm clearance from body/pads (0.5 mm for connectors).
- Exposed pads: include the manufacturer's paste-aperture pattern and thermal vias where recommended.
- 3D model path uses `${KIPRJMOD}/lib/dropout-kicad-library/3dmodels/...` and is aligned (check in the 3D viewer).

## 5. Symbol rules

- Pin numbers match the datasheet package exactly; double-check exposed pad numbering.
- Pins grouped by function (power on top/bottom, inputs left, outputs right), not by package order.
- Pin electrical types set correctly so ERC is meaningful (power input, power output, open drain, passive, etc.).
- 100 mil (2.54 mm) pin grid.

## 6. Changing released parts

Projects pin this library, so a change reaches a board only when that project updates its submodule. Even so:

- **Never silently change a land pattern** that existing boards use. Create a new footprint name (e.g. `..._Rev2`) or document the change clearly in the PR and release notes.
- Field corrections (typos, updated distributor PNs) are fine to edit in place.

## 7. Workflow

1. Open a **Part request** issue (or go straight to a PR).
2. Add symbol + footprint + 3D model in one PR, titled `Add <MPN>`.
3. CI checks required fields. Fix anything it flags.
4. Complete the PR checklist (datasheet verification) before merging.
