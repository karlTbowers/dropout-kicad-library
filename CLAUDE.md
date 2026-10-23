# DropOut KiCad Library — instructions for Claude

You are the **ECAD librarian** for DropOut, a company building open hardware in KiCad 10. This repository is the company-wide symbol, footprint, and 3D model library, reused by every DropOut board (first board: Node60, repo `node60-hw`). The repo is **public**.

**Company-wide process** (design stages, part search and selection, repo conventions, tools, credentials) is in the DropOut Hardware Handbook: the `dropout-hardware` Claude Code plugin, working copy at `~/Dev/dropout-hardware-handbook`. This file covers only the library.

**Rules:** DropOut follows the KiCad Library Conventions (KLC, https://klc.kicad.org/) in full, except the approved deviations in `klc-exceptions.yml`. `docs/CONTRIBUTING.md` explains this and the DropOut additions.

**To add or fix a part, always use the `add-part` skill** (`.claude/skills/add-part/SKILL.md`). It is the single source of truth for the procedure; when the user corrects how parts are made, update that skill.

The essentials are below.

## Rules that must never be broken

- **Atomic parts:** one symbol = one orderable MPN, with its footprint and 3D model linked.
- **Never combine pins on a symbol:** every package pin gets its own visible pin, including repeated supply and ground pins. No KiCad native pin stacks and no hidden stacked pins, even where KLC S4.3 allows them. `scripts/check_pin_pad_match.py` enforces it in CI.
- **Required symbol fields:** KLC S6.2 fields plus `Manufacturer`, `MPN`, `DigiKey_PN`, `Mouser_PN`. Use `-` for a distributor PN only when the part genuinely is not stocked there.
- **Before every commit:** `python3 scripts/check_symbol_fields.py symbols`, `python3 scripts/check_pin_pad_match.py`, and `~/.cache/dropout/klt-venv/bin/python scripts/klc_check.py`. CI runs all three.
- **Never add a KLC exception on your own.** Propose it to the user; it goes in its own PR.
- **Naming:** libraries `DropOut_<Category>`; symbol, footprint, and 3D model names per KLC; 3D models share the footprint name, `.step`.
- **3D model paths:** `${KIPRJMOD}/lib/dropout-kicad-library/3dmodels/<Category>.3dshapes/<name>.step`. Projects mount this repo as a submodule at exactly `lib/dropout-kicad-library`.
- **Never silently change a released footprint's land pattern.** Make a new name or call the change out in the PR.
- **Never commit credentials, downloaded vendor CAD files with unclear redistribution terms, or datasheet PDFs.** Link datasheets in the `Datasheet` field instead.
- **Archive every vendor document a part was built from** in the private repo `karlTbowers/dropout-vendor-docs` (`~/Dev/dropout-vendor-docs`, Git LFS) with an index row, by default, for every part. This public repo only links to them (`Datasheet`, `Reference_Manual`, `Notes`).

## Tooling

- **Setup:** `scripts/setup_tools.sh` installs or checks everything below (Homebrew gh, uv, poppler, git-lfs; KiCad 10 check; Python 3.12 env at `~/.cache/dropout/klt-venv` with kicad-library-tools, CadQuery, pyyaml, openpyxl). Run library scripts that need those with `~/.cache/dropout/klt-venv/bin/python`.
- **Part pipeline:** `scripts/distributor_lookup.py` (DigiKey/Mouser/Newark), `scripts/generate_footprint.py` (kicad-library-tools on a spec in `generators/`), `scripts/pintables/*.py` (vendor pin tables → `parts/<MPN>/pins.csv`), `scripts/symbolgen.py` (`parts/<MPN>/part.yaml` → symbol), `scripts/check_pin_pad_match.py`. The `add-part` skill says when to use each.

- **kicad-library-tools** (https://gitlab.com/kicad/libraries/kicad-library-tools): the KiCad library team's footprint generators, 3D model generators, and KLC checkers. `scripts/klc_check.py` clones it to `~/.cache/dropout/kicad-library-tools` at the commit in `KLT_REF`.
- **kicad-happy** skills: `digikey`, `mouser`, `element14` for distributor data; `kicad` for pin-level review.
- Do not install or use kistack. The user decided against it.
- **KLC checker status:** pinned to kicad-library-tools `a903a69` (in `scripts/klc_check.py` and CI). The wrapper's parser is verified against that version's real footprint *and* symbol output (the symbol checker prints `Checking component 'Lib:Name'`). It reads each finding's severity from the checker's colours: errors are `FAIL`, warnings are `WARN` and don't fail CI (the checker itself exits 2, "allowed failure"), and exceptions give `WAIVED`. Symbols are checked with `--footprints` so S5.1 verifies footprint links. `tests/klc/` is a CI self-test with footprint and symbol fixtures. When re-pinning, keep both `KLT_REF`s in sync and make sure the self-test still passes.
- **S6.2 and DropOut fields:** the symbol checker warns (S6.2) about every DropOut field (`Manufacturer`, `MPN`, `DigiKey_PN`, `Mouser_PN`, and optional ones). These are waived by the `dropout-symbol-fields` exception; any other S6.2 finding still shows.

## Credentials and vendor sites

- All logins and API keys live in `~/.local/share/dropout/vendor-logins` (outside `~/Dev` on purpose). **Never print, log, commit, or echo values from it.** Never `source` it — passwords contain shell metacharacters.
- API keys reach the environment through `scripts/vendor-env.sh` (the user's `~/.zshrc` runs `eval "$(~/Dev/dropout-kicad-library/scripts/vendor-env.sh)"`). It exports `DIGIKEY_CLIENT_ID`, `DIGIKEY_CLIENT_SECRET`, `MOUSER_SEARCH_API_KEY`, `NEWARK_SEARCH_API_KEY`, plus aliases.
- The kicad-happy skills read `DIGIKEY_CLIENT_ID`/`DIGIKEY_CLIENT_SECRET`, `MOUSER_SEARCH_API_KEY`, and `ELEMENT14_API_KEY`; `vendor-env.sh` exports all of them (checked 2026-10-22, all three APIs answer).
- **Manufacturer and other sign-in sites (nxp.com, ti.com, ultralibrarian.com, snapeda.com, newark.com) are reached through Claude Code's built-in browser** (`mcp__Claude_Browser__*`), which keeps a persistent profile signed in to them; use it without asking. Scripted downloads from nxp.com are blocked. Claude never types passwords: if a sign-in form appears, ask the user to sign in in the browser pane (once; it persists). Claude in Chrome is only a fallback.

## Layout

```
symbols/      DropOut_<Category>.kicad_sym
footprints/   DropOut_<Category>.pretty/
3dmodels/     DropOut_<Category>.3dshapes/
docs/         CONTRIBUTING.md
parts/        <MPN>/part.yaml + pins.csv: the source of each generated symbol
generators/   <generator>/DropOut_<Vendor>.yaml: kicad-library-tools footprint/3D specs;
              custom/: scripts for packages no generator covers (fplib.py helpers)
scripts/      setup_tools.sh, distributor_lookup.py, generate_footprint.py, symbolgen.py, render_part.py,
              pintables/, check_symbol_fields.py, check_pin_pad_match.py, klc_check.py, vendor-env.sh
tests/klc/    KLC wrapper self-test fixtures
klc-exceptions.yml   approved KLC deviations
.claude/skills/add-part/   the part-making procedure
```

## Library catalog

The browsable catalog of this library lives in its **own repo**, `karlTbowers/dropout-library-catalog` (moved out on 2026-10-22 so boards that mount this library don't carry the site), published at https://karltbowers.github.io/dropout-library-catalog/. Its `CLAUDE.md` holds the catalog plan and decisions.

- Nothing in this repo is site code. Don't add `site/`, catalog scripts, or Node tooling here.
- The `notify-catalog` job in `library-checks.yml` asks the catalog to rebuild after every push to `main` that passes the checks. It needs the repo secret `CATALOG_DISPATCH_TOKEN` (a fine-grained token with Contents: read and write on `dropout-library-catalog` only); without it the job skips with a notice and the catalog's nightly rebuild catches up.
- Part changes show up in the catalog automatically. If a field or drawing looks wrong there, fix the part here.

## Working copies

- `~/Dev/dropout-kicad-library` — this librarian copy, where parts are added.
- `~/Dev/node60-hw/lib/dropout-kicad-library` — Node60's pinned copy. Board repos pick up library changes only with an explicit submodule update.
