#!/usr/bin/env python3
"""Look up an exact MPN at DigiKey, Mouser and Newark and print what a DropOut symbol needs.

Usage: python3 scripts/distributor_lookup.py <MPN> [--json]

Reads API keys from the environment (exported by scripts/vendor-env.sh via ~/.zshrc):
DIGIKEY_CLIENT_ID, DIGIKEY_CLIENT_SECRET, MOUSER_SEARCH_API_KEY, NEWARK_SEARCH_API_KEY.
Keys are never printed. Prices and stock are dated observations, not quotes.
"""
import argparse
import datetime
import json
import os
import sys
import urllib.parse
import urllib.request


def req(url, data=None, headers=None):
    r = urllib.request.Request(url, data=data, headers=headers or {})
    with urllib.request.urlopen(r, timeout=30) as f:
        return json.load(f)


def digikey(mpn):
    cid, secret = os.environ.get("DIGIKEY_CLIENT_ID"), os.environ.get("DIGIKEY_CLIENT_SECRET")
    if not cid or not secret:
        return {"error": "DIGIKEY_CLIENT_ID/SECRET not set"}
    tok = req("https://api.digikey.com/v1/oauth2/token",
              urllib.parse.urlencode({"client_id": cid, "client_secret": secret,
                                      "grant_type": "client_credentials"}).encode(),
              {"Content-Type": "application/x-www-form-urlencoded"})["access_token"]
    p = req(f"https://api.digikey.com/products/v4/search/{urllib.parse.quote(mpn, safe="")}/productdetails",
            headers={"Authorization": f"Bearer {tok}", "X-DIGIKEY-Client-Id": cid,
                     "X-DIGIKEY-Locale-Site": "US", "X-DIGIKEY-Locale-Currency": "USD"})["Product"]
    return {"manufacturer": p["Manufacturer"]["Name"], "mpn": p["ManufacturerProductNumber"],
            "status": p["ProductStatus"]["Status"], "stock": p.get("QuantityAvailable"),
            "datasheet": p.get("DatasheetUrl"), "description": p["Description"]["DetailedDescription"],
            "part_numbers": {v["DigiKeyProductNumber"]: v["PackageType"]["Name"] for v in p["ProductVariations"]},
            "package": next((x["ValueText"] for x in p["Parameters"] if x["ParameterText"] == "Supplier Device Package"), None)}


def mouser(mpn):
    key = os.environ.get("MOUSER_SEARCH_API_KEY")
    if not key:
        return {"error": "MOUSER_SEARCH_API_KEY not set"}
    m = req(f"https://api.mouser.com/api/v1/search/partnumber?apiKey={key}",
            json.dumps({"SearchByPartRequest": {"mouserPartNumber": mpn, "partSearchOptions": "Exact"}}).encode(),
            {"Content-Type": "application/json"})
    parts = (m.get("SearchResults") or {}).get("Parts") or []
    return [{"part_number": p["MouserPartNumber"], "mpn": p["ManufacturerPartNumber"],
             "manufacturer": p["Manufacturer"], "lifecycle": p.get("LifecycleStatus"),
             "availability": p.get("Availability")} for p in parts if p["ManufacturerPartNumber"] == mpn] \
        or {"error": m.get("Errors") or "not found"}


def newark(mpn):
    key = os.environ.get("NEWARK_SEARCH_API_KEY")
    if not key:
        return {"error": "NEWARK_SEARCH_API_KEY not set"}
    n = req("https://api.element14.com/catalog/products?" + urllib.parse.urlencode({
        "term": f"manuPartNum:{mpn}", "storeInfo.id": "www.newark.com", "resultsSettings.offset": 0,
        "resultsSettings.numberOfResults": 5, "resultsSettings.responseGroup": "medium",
        "callInfo.responseDataFormat": "json", "callInfo.apiKey": key}))
    r = n.get("manufacturerPartNumberSearchReturn", {})
    return [{"sku": p.get("sku"), "mpn": p.get("translatedManufacturerPartNumber"), "brand": p.get("brandName")}
            for p in r.get("products", [])] or {"error": "not found"}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mpn")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    out = {"mpn": args.mpn, "observed": datetime.date.today().isoformat()}
    for name, fn in (("digikey", digikey), ("mouser", mouser), ("newark", newark)):
        try:
            out[name] = fn(args.mpn)
        except Exception as e:  # report and continue with the other distributors
            out[name] = {"error": f"{type(e).__name__}: {e}"}
    if args.json:
        print(json.dumps(out, indent=1))
        return
    print(f"{args.mpn}  (observed {out['observed']})")
    for name in ("digikey", "mouser", "newark"):
        print(f"\n{name}:")
        v = out[name]
        for item in (v if isinstance(v, list) else [v]):
            for k, val in item.items():
                print(f"  {k}: {val}")


if __name__ == "__main__":
    sys.exit(main())
