# KLC wrapper self-test

Fixture footprints and symbols that `scripts/klc_check.py` is run against in CI, to prove
that `klc-exceptions.yml` waives exactly what it should, and nothing more, that checker
errors fail and warnings don't, and that the parser still understands the pinned
kicad-library-tools output for both footprints and symbols.

| Fixture | Expected |
|---|---|
| `DropOut_Test.pretty/SOT-23` | F9.3 **waived** (correct `${KIPRJMOD}` model path); F5.2 **warn** (RefDes text too small, a checker warning) |
| `DropOut_Test.pretty/SOT-23_WrongDir` | F9.3 **fails** (model in the wrong `.3dshapes` folder, a checker error); F5.2 **warn** |
| `DropOut_TestSym.kicad_sym` `TEST-GOOD` | S6.2 **waived** by `dropout-symbol-fields` (DropOut fields `Manufacturer`, `MPN`, `DigiKey_PN`, `Mouser_PN`) |
| `DropOut_TestSym.kicad_sym` `TEST-BADFP` | S5.1 **fails** (footprint link to a file that doesn't exist) |

`expected.txt` lists the expected `FAIL`/`WARN`/`WAIVED` lines. Update it only when an exception or
the fixtures change on purpose. When re-pinning `KLT_REF`, this test failing means the
checker's output format changed and the wrapper's parser needs updating.

These files are not part of the library (CI only scans `symbols/` and `footprints/`).
