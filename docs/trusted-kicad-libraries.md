# Trusted KiCad libraries

The `add-part` skill (step 2a) checks these libraries, and the manufacturer's own official KiCad library if
it has one, **before** we build a part. Whether we reuse anything from them is decided **case by case**,
per part (user's rule, 2026-10-26): a trusted library is a source to compare against, not a default. Every
reused item is still checked against the manufacturer's data sheet and must pass our checks (KLC, DropOut
fields, never combine pins).

Add a library here only when the user says to trust it, or when it is the manufacturer's own officially
supported library. Record its license: reusing content brings that license's conditions into this repo,
whose own license is still to be chosen (README).

| Library | URL | Maintained by | Contents | License, and what reuse requires | Added |
|---|---|---|---|---|---|
| KiCad official libraries | https://gitlab.com/kicad/libraries (`kicad-symbols`, `kicad-footprints`, `kicad-packages3D`) | KiCad library team | Symbols, footprints, 3D models; installed with KiCad (`/Applications/KiCad/KiCad.app/Contents/SharedSupport/`) | CC-BY-SA 4.0 with a design exception (designs using the libraries are not adaptations). Copying or adapting library items into this repo brings CC-BY-SA terms: attribution and share-alike for those items. | 2026-10-26 |
| CERN KiCad libraries | https://gitlab.com/ohwr/cern-kicad-libs | CERN Electronics Design Office (OHWR); nightly `kicad-cli` conversion of CERN's Altium libraries | Symbols and footprints in a database library (`CERN.kicad_dbl`, needs an SQLite ODBC driver); **no 3D models** | CERN-OHL-P-2.0 (permissive): keep the copyright and license notices. Trusted by the user (2026-10-26). | 2026-10-26 |
| Würth Elektronik (official) | https://github.com/WurthElektronik/KiCad-Library | Würth Elektronik EDA team | Symbols, footprints, 3D models for Würth parts (e.g. `REDCUBE_THT_Wurth`) | Würth license terms (`License_Terms_WE_KiCad_library.pdf`): use, modify, and share **modified** models; modified models must be clearly marked as modified and credit WE eiSos as the original provider; no reverse engineering. Used for the REDCUBE 3D models (marked in their STEP headers). | 2026-10-26 |
| Espressif (official) | https://github.com/espressif/kicad-libraries | Espressif | Symbols, footprints, 3D models for Espressif SoCs, modules and DevKits; also a KiCad PCM add-on | CC-BY-SA 4.0 with the same design exception as KiCad's libraries. | 2026-10-26 |
| SparkFun KiCad libraries | https://github.com/sparkfun/SparkFun-KiCad-Libraries | SparkFun Electronics | Symbols (`SparkFun-<Category>.kicad_sym`), footprints, 3D models (mostly STEP); also a KiCad PCM add-on | CC-BY 4.0, stated in the README (the repo has no LICENSE file): attribution only, commercial use allowed, no share-alike. SparkFun also asks, not as a license condition, to be emailed a link when a product using their footprint goes on sale. Trusted by the user (2026-10-28). | 2026-10-28 |

## How to use a match

1. Find the part (or its package) in the libraries above and in the manufacturer's official library.
2. Compare it with the data sheet: pin map, land pattern (pads, drills, keep-outs), body, 3D model frame.
3. Decide with the user, per part, what to reuse (for example a vendor 3D model, or a land pattern) and
   what we build ourselves. Note the source, version or commit, and license in `part.yaml` and the PR.
4. Archive the license file of anything reused in `dropout-vendor-docs`.
