# DropOut KiCad Library

The shared KiCad 10 symbol, footprint, and 3D model library for all DropOut open-hardware projects.

**Browse the library:** https://karltbowers.github.io/dropout-library-catalog/ (built from this repo by [dropout-library-catalog](https://github.com/karlTbowers/dropout-library-catalog)).

Every part in this library is an **atomic part**: one symbol = one orderable manufacturer part number (MPN), with its footprint and 3D model already linked. A BOM exported from any DropOut schematic should be purchasable from DigiKey or Mouser as-is.

## Layout

```
symbols/        DropOut_<Category>.kicad_sym        one file per category
footprints/     DropOut_<Category>.pretty/          one folder per category
3dmodels/       DropOut_<Category>.3dshapes/        STEP models, mirroring footprint categories
docs/           CONTRIBUTING.md (library rules: KLC + DropOut additions)
scripts/        check_symbol_fields.py, klc_check.py (run by CI), vendor-env.sh
klc-exceptions.yml   approved deviations from the KiCad Library Conventions
.claude/skills/add-part/   Claude Code procedure for adding parts
```

Planned categories (created as the first part in each one is added). Microcontrollers get one library per vendor, `DropOut_MCU_<Vendor>`, with the vendor named as in KiCad's stock `MCU_<Vendor>_*` libraries:

| Category | Contents |
|---|---|
| `DropOut_MCU_NXP` | NXP microcontrollers |
| `DropOut_MCU_Microchip` | Microchip microcontrollers |
| `DropOut_MCU_ST` | STMicroelectronics microcontrollers |
| `DropOut_Interface` | PHYs, transceivers, level shifters |
| `DropOut_Power` | Regulators, ideal-diode/eFuse controllers, supervisors |
| `DropOut_PowerSwitch` | Smart high-side switches, MOSFETs |
| `DropOut_Sensor` | Current/voltage monitors, temperature sensors |
| `DropOut_Memory` | Flash, EEPROM |
| `DropOut_Resistor` | Resistors, including current-sense shunts |
| `DropOut_Capacitor` | Capacitors |
| `DropOut_Inductor` | Inductors, ferrite beads, and common mode chokes |
| `DropOut_Thermistor` | NTC and PTC thermistors |
| `DropOut_Protection` | TVS, ESD, fuses |
| `DropOut_Timing` | Oscillators, crystals |
| `DropOut_Connector` | Connectors and headers |
| `DropOut_Oscillator` | Footprints and 3D models for oscillators (KLC footprint library naming) |
| `DropOut_Crystal` | Footprints and 3D models for crystals |
| `DropOut_Connector_Samtec` | Footprints and 3D models for Samtec connectors |
| `DropOut_Diode_SMD` | Footprints and 3D models for SMD diode packages (DO-218, DO-214, SOD...) |
| `DropOut_Resistor_SMD` | Footprints and 3D models for chip resistors (one per size code, shared by every DropOut resistor of that size) |
| `DropOut_Capacitor_SMD` | Footprints and 3D models for MLCCs (one per size code, shared by every DropOut MLCC of that size) |
| `DropOut_Inductor_SMD` | Footprints and 3D models for SMD inductors and common mode chokes |
| `DropOut_Package_BGA` | Footprints and 3D models for ball grid array packages (footprint libraries follow KLC package-type naming) |
| `DropOut_Package_DFN_QFN` | Footprints and 3D models for DFN/QFN (no-lead) packages |
| `DropOut_Package_QFP` | Footprints and 3D models for quad flat packages (LQFP, TQFP) |
| `DropOut_Package_SO` | Footprints and 3D models for small-outline packages (SOIC, SSOP, TSSOP, HTSSOP) |
| `DropOut_Package_TO_SOT_SMD` | Footprints and 3D models for SOT/TSOT/TO SMD packages |

## Using it in a project

Add this repository as a git submodule at the **fixed path** `lib/dropout-kicad-library`:

```bash
git submodule add https://github.com/karlTbowers/dropout-kicad-library.git lib/dropout-kicad-library
```

Footprints reference their 3D models as
`${KIPRJMOD}/lib/dropout-kicad-library/3dmodels/<Category>.3dshapes/<name>.step`,
so the submodule path must be exactly the one above. The project's `sym-lib-table` and `fp-lib-table` point into the submodule the same way (see `node60-hw` for a working example).

To pick up library changes in a project:

```bash
cd lib/dropout-kicad-library && git pull origin main && cd ../..
git add lib/dropout-kicad-library && git commit -m "Update DropOut library"
```

Each board revision pins the library commit it was released with, so old revisions keep opening correctly.

## Adding a part

DropOut follows the [KiCad Library Conventions (KLC)](https://klc.kicad.org/), except the approved deviations in [klc-exceptions.yml](klc-exceptions.yml). Read [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md). In short: open a part request issue or a pull request, verify against the datasheet, and let CI run the field and KLC checks.

## License

TBD — to be chosen before the first public release.
