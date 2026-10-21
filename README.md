# DropOut KiCad Library

The shared KiCad 10 symbol, footprint, and 3D model library for all DropOut open-hardware projects.

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

Planned categories (created as the first part in each one is added):

| Category | Contents |
|---|---|
| `DropOut_MCU` | Microcontrollers |
| `DropOut_Interface` | PHYs, transceivers, level shifters |
| `DropOut_Power` | Regulators, ideal-diode/eFuse controllers, supervisors |
| `DropOut_PowerSwitch` | Smart high-side switches, MOSFETs |
| `DropOut_Sensor` | Current/voltage monitors, temperature sensors |
| `DropOut_Memory` | Flash, EEPROM |
| `DropOut_Passive` | Resistors, capacitors, inductors, NTCs, shunts |
| `DropOut_Protection` | TVS, ESD, fuses |
| `DropOut_Timing` | Oscillators, crystals |
| `DropOut_Connector` | Connectors and headers |

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
