#!/usr/bin/env python3
"""Place Amphenol Sine's own AT13-2P-BM04 STEP model in the footprint's frame.

Usage: ~/.cache/dropout/klt-venv/bin/python generators/custom/Amphenol_AT13-2P-BMxx_step.py <AT13-2P-BM04.stp>

Input: the manufacturer model from Amphenol Sine's CADENAS catalog
(https://amphenolsine-embedded.partcommunity.com?catalog=amphenolsine&part=AT13-2P-BM04),
STEP AP242, header "License CC BY-ND 4.0", organization CADENAS. Amphenol Sine told the user
(2026-10-25) that it may be published in this repository and modified where needed. The original
is archived in dropout-vendor-docs, Amphenol-Sine/BoardLock/.

The vendor model has its origin on the mating axis at the flange seal face, the mating face
toward -x, the board side toward -y (boss faces at y = -13.995) and the pins at x = 15.49,
z = -2.7 / +2.7. KLC F9.3 wants the model in the footprint's frame with zero offset and rotation:
KiCad model X = board x, Y = -board y, Z up from the board. This script does not touch the
geometry or colours: it wraps the vendor solid in an assembly whose single component carries
the placement X = z + 2.7, Y = x - 15.49, Z = y + 13.995 (a proper rotation), so pin 1 (vendor
z = -2.7) lands on the origin, pin 2 on X = +5.40, the shroud toward the board edge (+y) and
the bosses on the seating plane.
"""
import sys
from pathlib import Path

from OCP.APIHeaderSection import APIHeaderSection_MakeHeader
from OCP.gp import gp_Trsf
from OCP.IFSelect import IFSelect_RetDone
from OCP.STEPCAFControl import STEPCAFControl_Reader, STEPCAFControl_Writer
from OCP.STEPControl import STEPControl_AsIs
from OCP.TCollection import TCollection_ExtendedString, TCollection_HAsciiString
from OCP.TDataStd import TDataStd_Name
from OCP.TDF import TDF_LabelSequence
from OCP.TDocStd import TDocStd_Document
from OCP.TopLoc import TopLoc_Location
from OCP.XCAFDoc import XCAFDoc_DocumentTool

REPO = Path(__file__).resolve().parents[2]
LIB = "DropOut_Connector_Amphenol"
NAME = "Amphenol_AT13-2P-BMxx_1x02_P5.40mm_Horizontal"


def main(src):
    doc = TDocStd_Document(TCollection_ExtendedString("XmlOcaf"))
    reader = STEPCAFControl_Reader()
    reader.SetColorMode(True)
    reader.SetNameMode(True)
    if reader.ReadFile(str(src)) != IFSelect_RetDone or not reader.Transfer(doc):
        sys.exit(f"cannot read {src}")
    tool = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    roots = TDF_LabelSequence()
    tool.GetFreeShapes(roots)
    if roots.Length() != 1:
        sys.exit(f"expected one root shape, found {roots.Length()}")

    t = gp_Trsf()
    t.SetValues(0, 0, 1, 2.7,           # X = z + 2.7
                1, 0, 0, -15.49,        # Y = x - 15.49
                0, 1, 0, 13.995)        # Z = y + 13.995
    asm = tool.NewShape()
    TDataStd_Name.Set_s(asm, TCollection_ExtendedString(NAME))
    tool.AddComponent(asm, roots.Value(1), TopLoc_Location(t))
    tool.UpdateAssemblies()

    writer = STEPCAFControl_Writer()
    writer.SetColorMode(True)
    writer.SetNameMode(True)
    writer.Transfer(doc, STEPControl_AsIs)
    header = APIHeaderSection_MakeHeader(writer.ChangeWriter().Model())
    header.SetName(TCollection_HAsciiString(NAME))
    header.SetAuthorValue(1, TCollection_HAsciiString("Amphenol Sine Systems / CADENAS, License CC BY-ND 4.0"))
    header.SetOrganizationValue(1, TCollection_HAsciiString(
        "Re-placed in the footprint frame by DropOut with Amphenol Sine's permission (2026-10-25); geometry unchanged"))
    out = REPO / "3dmodels" / f"{LIB}.3dshapes" / f"{NAME}.step"
    out.parent.mkdir(parents=True, exist_ok=True)
    if writer.Write(str(out)) != IFSelect_RetDone:
        sys.exit(f"cannot write {out}")
    print("3D model  ", out)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(Path(sys.argv[1]))
