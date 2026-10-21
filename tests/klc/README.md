# KLC wrapper self-test

Fixture footprints that `scripts/klc_check.py` is run against in CI, to prove that
`klc-exceptions.yml` waives exactly what it should, and nothing more, with the pinned
kicad-library-tools version.

| Footprint | Expected |
|---|---|
| `SOT-23` | F9.3 **waived** (correct `${KIPRJMOD}` model path); F5.2 **fails** (RefDes text too small) |
| `SOT-23_WrongDir` | F9.3 **fails** (model in the wrong `.3dshapes` folder); F5.2 **fails** |

`expected.txt` lists the expected `FAIL`/`WAIVED` lines. Update it only when an exception or
the fixtures change on purpose. When re-pinning `KLT_REF`, this test failing means the
checker's output format changed and the wrapper's parser needs updating.

These files are not part of the library (CI only scans `symbols/` and `footprints/`).
