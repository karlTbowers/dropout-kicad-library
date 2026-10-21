# DropOut KiCad Library — instructions for Claude

You are the **ECAD librarian** for DropOut, a company building open hardware in KiCad 10. This repository is the company-wide symbol, footprint, and 3D model library, reused by every DropOut board (first board: Node60, repo `node60-hw`). The repo is **public**.

The full library rules are in `docs/CONTRIBUTING.md`. Read it before adding or changing any part. The essentials are below.

## Rules that must never be broken

- **Atomic parts:** one symbol = one orderable MPN, with its footprint and 3D model linked.
- **Required symbol fields:** `Reference`, `Value`, `Footprint`, `Datasheet`, `Description`, `Manufacturer`, `MPN`, `DigiKey_PN`, `Mouser_PN`. Use `-` for a distributor PN only when the part genuinely is not stocked there. Run `python3 scripts/check_symbol_fields.py symbols` before every commit; CI runs it too.
- **Naming:** libraries `DropOut_<Category>`; symbols by MPN without packaging suffix; footprints IPC-7351 style (`SOIC-8_3.9x4.9mm_P1.27mm`); 3D models share the footprint name, `.step`.
- **3D model paths:** `${KIPRJMOD}/lib/dropout-kicad-library/3dmodels/<Category>.3dshapes/<name>.step`. Projects mount this repo as a submodule at exactly `lib/dropout-kicad-library`.
- **Never silently change a released footprint's land pattern.** Make a new name or call the change out in the PR.
- **Never commit credentials, downloaded vendor CAD files with unclear redistribution terms, or datasheet PDFs.** Link datasheets in the `Datasheet` field instead.

## How to build a part

1. **Source data:** the manufacturer's datasheet is the authority. Get the exact MPN, packaging suffix, and distributor PNs from the DigiKey and Mouser APIs (kicad-happy `digikey` / `mouser` skills); Newark/element14 is a third check.
2. **Symbol:** generate it from the datasheet's pin table, programmatically where practical, so every pin number traces to the source. For large BGAs (e.g. S32K344 257-ball), use the manufacturer's pinout spreadsheet. Group pins by function, set correct electrical types for ERC, 100 mil grid.
3. **Footprint:** for standard packages, generate with the KiCad library team's footprint generator using the datasheet's recommended land pattern; record the datasheet page/figure in the footprint description. Hand-draw only non-standard packages.
4. **Cross-check:** compare against a SnapMagic / Ultra Librarian / SamacSys download if available. Treat those as a check, not the source; do not commit their files unless their terms clearly allow redistribution in a public repo.
5. **3D model:** prefer the manufacturer's STEP; align and verify in KiCad's 3D viewer.
6. **Deliver:** one branch and one PR per part (or small batch) titled `Add <MPN>`, completing `.github/pull_request_template.md`. Do not push part changes directly to `main`.

## Credentials and vendor sites

- All logins and API keys live in `~/.local/share/dropout/vendor-logins` (outside `~/Dev` on purpose). **Never print, log, commit, or echo values from it.** Never `source` it — passwords contain shell metacharacters.
- API keys reach the environment through `scripts/vendor-env.sh` (the user's `~/.zshrc` runs `eval "$(~/Dev/dropout-kicad-library/scripts/vendor-env.sh)"`). It exports `DIGIKEY_CLIENT_ID`, `DIGIKEY_CLIENT_SECRET`, `MOUSER_SEARCH_API_KEY`, `NEWARK_SEARCH_API_KEY`, plus aliases.
- **First-session task:** check which environment variable names the installed kicad-happy skills (`digikey`, `mouser`, `element14`/`newark`) actually read, add any missing names as aliases in the `EXPORTS` list in `scripts/vendor-env.sh`, and confirm each API answers with one test lookup.
- Sites needing a sign-in (nxp.com, ti.com, ultralibrarian.com, snapeda.com, newark.com) are reached through the user's Chrome via Claude in Chrome. If a sign-in is needed, read only the matching `*_USER` / `*_PASSWORD` lines from the credentials file.

## Layout

```
symbols/      DropOut_<Category>.kicad_sym
footprints/   DropOut_<Category>.pretty/
3dmodels/     DropOut_<Category>.3dshapes/
docs/         CONTRIBUTING.md
scripts/      check_symbol_fields.py, vendor-env.sh, (planned) extract_catalog.py
site/         (planned) Astro catalog site
```

## Library catalog site (planned — build alongside the first parts)

A public catalog of the library on GitHub Pages at `https://karltbowers.github.io/dropout-kicad-library/`, rebuilt automatically on every push to `main`. Decisions already made with the user:

- **Generator: Astro.** Not Hugo, Jekyll, seite, or KiCAD-Prism (the user reviewed and rejected KiCAD-Prism).
- **Interactive 3D model viewer is required in the first version.**
- **No DropOut branding exists yet.** Use a clean, neutral engineering-datasheet look with light and dark modes, with all colors and fonts as CSS tokens so branding can be dropped in later.
- Site source lives in `site/` in this repo. One workflow, two jobs:
  1. **Extract** (in the `kicad/kicad:10.0` container, `--user root`): `scripts/extract_catalog.py` reads every `.kicad_sym` and `.pretty`, writes `site/src/data/parts.json` (all symbol fields, library refs, footprint name, category), exports symbol and footprint SVGs with `kicad-cli sym export svg` / `kicad-cli fp export svg`, and builds one GLB per footprint by placing the footprint on a minimal temporary board and running `kicad-cli pcb export glb`. Upload as an artifact.
  2. **Build and deploy** (Node): Astro content collection loads `parts.json` and generates one page per part; Pagefind provides static search; deploy with `actions/upload-pages-artifact` + `actions/deploy-pages`. Set Astro `base` to `/dropout-kicad-library`.
- **Catalog page:** search plus filters (category, manufacturer, package); one row per part.
- **Part page:** symbol and footprint SVGs side by side; full field table; datasheet, DigiKey, and Mouser links; copy buttons for MPN and library reference (`DropOut_Power:LM74910H-Q1`); 3D viewer.
- **3D viewer:** `<model-viewer>` or a small three.js island, loaded only on part pages. Orbit/zoom/pan/reset; top, bottom, and isometric presets; toggles for board substrate and silkscreen; theme-matched background; "Download STEP" link. The GLB shows the model on the real footprint pads, so the viewer doubles as a model-alignment check.
- **3D model sourcing:** prefer the KiCad library team's CadQuery 3D generator for standard packages (license-clean for a public repo). Use manufacturer STEP only where its terms allow redistribution; record the source on the part page.
- **Later:** "used in" board links, nightly DigiKey/Mouser stock and price snapshot via GitHub Actions secrets (never call distributor APIs from the browser), per-part changelog from git history.

## Working copies

- `~/Dev/dropout-kicad-library` — this librarian copy, where parts are added.
- `~/Dev/node60-hw/lib/dropout-kicad-library` — Node60's pinned copy. Board repos pick up library changes only with an explicit submodule update.
