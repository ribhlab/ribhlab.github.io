#!/usr/bin/env python3
"""Validate and submit the RivoScan (not any other app) Play Data Safety CSV.

Data Safety POST writes an entire declaration, not an Android Publisher edit.
Never run against another application or use another app's existing answers.
"""
from __future__ import annotations
import argparse, csv, json, sys
from pathlib import Path
from collections import defaultdict

PACKAGE = "com.ribhlab.rivoscan"
BASE = Path(__file__).parent
CSV_FILE = BASE / "store-listings/rivoscan-data-safety-candidate-2026-11-07.csv"
CONFIRM = "RIVOSCAN_DATA_SAFETY_V74_CONFIRM"
EXPECTED_TYPES = {
    "PSL_APPROX_LOCATION","PSL_USER_INTERACTION",
    "PSL_PERFORMANCE_DIAGNOSTICS","PSL_DEVICE_ID",
    "PSL_FILES_AND_DOCS","PSL_PHOTOS","PSL_USER_GENERATED_CONTENT"
}
SDK_TYPES = {
    "PSL_APPROX_LOCATION","PSL_USER_INTERACTION",
    "PSL_PERFORMANCE_DIAGNOSTICS","PSL_DEVICE_ID"
}
OPTIONAL_TYPES = EXPECTED_TYPES - SDK_TYPES
EXPECTED_COUNT = 782

def validate(content: str) -> dict:
    rows = list(csv.reader(content.splitlines()))
    if not rows or rows[0] != [
            "Question ID (machine readable)","Response ID (machine readable)",
            "Response value","Answer requirement","Human-friendly question label"]:
        raise ValueError("Not the official five-column Play Safety Labels format")
    if len(rows)-1 != EXPECTED_COUNT:
        raise ValueError("Google Play template row count changed; refresh current export")
    by_key = {}
    selections = defaultdict(list)
    for i, row in enumerate(rows[1:],2):
        if len(row) != 5:
            raise ValueError(f"Wrong column count at CSV line {i}")
        q, code, response, requirement, label = row
        if (q,code) in by_key:
            raise ValueError(f"Duplicate Google response ID at CSV line {i}")
        if response not in ("","TRUE","FALSE"):
            raise ValueError(f"Unexpected data value at CSV line {i}")
        by_key[q,code] = response
        if response == "TRUE":
            selections[q].append(code)
        if requirement not in ("REQUIRED","MULTIPLE_CHOICE","SINGLE_CHOICE",
                               "MAYBE_REQUIRED","OPTIONAL"):
            raise ValueError(f"Unexpected Google requirement at {i}")
    def must(q,code,value):
        if by_key.get((q,code)) != value:
            raise ValueError(f"Missing/mismatched RivoScan declaration: {q}/{code}")
    must("PSL_DATA_COLLECTION_COLLECTS_PERSONAL_DATA","","TRUE")
    must("PSL_DATA_COLLECTION_ENCRYPTED_IN_TRANSIT","","FALSE")
    must("PSL_SUPPORTED_ACCOUNT_CREATION_METHODS","PSL_ACM_NONE","TRUE")
    must("PSL_HAS_OUTSIDE_APP_ACCOUNTS","","FALSE")
    must("PSL_SUPPORT_DATA_DELETION_BY_USER","DATA_DELETION_NO","TRUE")
    actual_types = set()
    for q, responses in selections.items():
        if q.startswith("PSL_DATA_TYPES_"):
            actual_types.update(responses)
    if actual_types != EXPECTED_TYPES:
        raise ValueError("Data-type checklist was altered from verified v74 audit")
    for kind in EXPECTED_TYPES:
        prefix = f"PSL_DATA_USAGE_RESPONSES:{kind}:"
        must(prefix+"PSL_DATA_USAGE_COLLECTION_AND_SHARING","PSL_DATA_USAGE_ONLY_COLLECTED","TRUE")
        must(prefix+"PSL_DATA_USAGE_EPHEMERAL","","FALSE")
        if kind in SDK_TYPES:
            must(prefix+"PSL_DATA_USAGE_COLLECTION_AND_SHARING","PSL_DATA_USAGE_ONLY_SHARED","TRUE")
            must(prefix+"DATA_USAGE_USER_CONTROL","PSL_DATA_USAGE_USER_CONTROL_REQUIRED","TRUE")
            for purpose in ("PSL_ADVERTISING","PSL_ANALYTICS","PSL_FRAUD_PREVENTION_SECURITY"):
                must(prefix+"DATA_USAGE_COLLECTION_PURPOSE",purpose,"TRUE")
                must(prefix+"DATA_USAGE_SHARING_PURPOSE",purpose,"TRUE")
        else:
            must(prefix+"DATA_USAGE_USER_CONTROL","PSL_DATA_USAGE_USER_CONTROL_OPTIONAL","TRUE")
            must(prefix+"DATA_USAGE_COLLECTION_PURPOSE","PSL_APP_FUNCTIONALITY","TRUE")
            if selections.get(prefix+"DATA_USAGE_SHARING_PURPOSE"):
                raise ValueError("User-initiated AI types unexpectedly declared shared")
    count = sum(v in ("TRUE","FALSE") for v in by_key.values())
    return {"package":PACKAGE,"dataTypes":sorted(actual_types),"rows":len(rows)-1,
            "answeredRows":count,"status":"PREVALIDATED_CANDIDATE",
            "limitations":"The signed AAB binary/actual runtime network traffic have not been audited."}

def apply(content: str) -> dict:
    from google.auth.transport.requests import AuthorizedSession
    from publish import get_credentials
    session = AuthorizedSession(get_credentials())
    url=f"https://androidpublisher.googleapis.com/androidpublisher/v3/applications/{PACKAGE}/dataSafety"
    result=session.post(url,json={"safetyLabels":content},timeout=60)
    if result.status_code not in (200,204):
        msg="UNKNOWN"
        try:
            details=result.json().get("error",{})
            msg=str(details.get("message",""))[:250]
        except (ValueError,TypeError):
            pass
        # Never print an entire API server response, token, or user record.
        print("RIVOSCAN_DATA_SAFETY_API_ERROR="+json.dumps({
            "status":result.status_code,"kind":str(details.get("status",""))[:65] if "details" in locals() else "",
            "reasonClass":"GOOGLE_CSV_VALIDATION_OR_PERMISSION",
            "messageContainsMissing":("missing" in msg.lower()),
            "messageContainsInvalid":("invalid" in msg.lower())}),file=sys.stderr)
        return {"result":"API_REJECTED","httpStatus":result.status_code}
    return {"result":"DATA_SAFETY_DECLARATION_POST_ACCEPTED","httpStatus":result.status_code,
            "note":"Google may still review or reject disclosures; not a public release"}

def main(argv=None) -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--apply",action="store_true")
    p.add_argument("--confirm",default="")
    args=p.parse_args(argv)
    content=CSV_FILE.read_text(encoding="utf-8")
    try:
        info=validate(content)
        if not args.apply:
            print("RIVOSCAN_DATA_SAFETY_PREFLIGHT="+json.dumps(info,sort_keys=True))
            return 0
        if args.confirm!=CONFIRM:
            print("BLOCKED: explicit package-specific approval required",file=sys.stderr)
            return 2
        result=apply(content)
        print("RIVOSCAN_DATA_SAFETY_RESULT="+json.dumps(result,sort_keys=True))
        return 0 if result["result"]=="DATA_SAFETY_DECLARATION_POST_ACCEPTED" else 1
    except Exception as exc:
        print("RIVOSCAN_DATA_SAFETY_FAILED="+type(exc).__name__,file=sys.stderr)
        return 1

if __name__=="__main__":
    raise SystemExit(main())
