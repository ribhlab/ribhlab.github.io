#!/usr/bin/env python3
"""RivoSticker-specific Android Publisher Data Safety CSV submitter.

Google Mobile Ads SDK 25.5.0 disclosure: IP-based approximate location,
app interactions, diagnostics, and device/account identifiers. Selected photos
and created stickers are processed on the device, not sent to RibhLab servers.
User-initiated WhatsApp/Android sharing is separately expected by the user.
"""
from __future__ import annotations
import argparse
import csv
import io
import json
import sys
from pathlib import Path
from collections import defaultdict

PACKAGE = "com.ribhlab.rivosticker"
CSV = Path(__file__).parent / "store-listings/rivosticker-data-safety-candidate-2026-11-24.csv"
SDK_TYPES = {
    "PSL_APPROX_LOCATION",
    "PSL_USER_INTERACTION",
    "PSL_PERFORMANCE_DIAGNOSTICS",
    "PSL_DEVICE_ID",
}
FORBIDDEN_TYPES = {"PSL_PHOTOS", "PSL_FILES_AND_DOCS", "PSL_USER_GENERATED_CONTENT"}
EXPECTED_COUNT = 782
CONFIRM = "SUBMIT_RIVOSTICKER_VERIFIED_ADMOB_DATA_SAFETY"


def verify(text):
    table = list(csv.reader(io.StringIO(text)))
    if not table or table[0] != [
        "Question ID (machine readable)",
        "Response ID (machine readable)",
        "Response value",
        "Answer requirement",
        "Human-friendly question label",
    ] or len(table) - 1 != EXPECTED_COUNT:
        raise ValueError("Invalid official Google Play Data Safety CSV version")
    selections = defaultdict(set)
    by_key = {}
    for line_no, row in enumerate(table[1:], 2):
        if len(row) != 5:
            raise ValueError(f"Bad CSV columns on line {line_no}")
        question, code, value, requirement, label = row
        if value not in ("", "TRUE", "FALSE"):
            raise ValueError(f"Unexpected response on line {line_no}")
        if (question, code) in by_key:
            raise ValueError(f"Duplicate response on line {line_no}")
        by_key[(question, code)] = value
        if value == "TRUE":
            selections[question].add(code)

    def must(question, code, value):
        if by_key.get((question, code)) != value:
            raise ValueError(f"Data safety answer mismatch: {question}/{code}")

    must("PSL_DATA_COLLECTION_COLLECTS_PERSONAL_DATA", "", "TRUE")
    must("PSL_DATA_COLLECTION_ENCRYPTED_IN_TRANSIT", "", "FALSE")
    must("PSL_SUPPORTED_ACCOUNT_CREATION_METHODS", "PSL_ACM_NONE", "TRUE")
    must("PSL_HAS_OUTSIDE_APP_ACCOUNTS", "", "FALSE")
    must("PSL_SUPPORT_DATA_DELETION_BY_USER", "DATA_DELETION_NO", "TRUE")
    must("PSL_INDEPENDENTLY_VALIDATED", "", "FALSE")
    got = set().union(*(values for question, values in selections.items()
                        if question.startswith("PSL_DATA_TYPES_")))
    if got != SDK_TYPES:
        raise ValueError(f"Unexpected declared types: {got.symmetric_difference(SDK_TYPES)}")
    for typ in SDK_TYPES:
        prefix = f"PSL_DATA_USAGE_RESPONSES:{typ}:"
        must(prefix + "PSL_DATA_USAGE_COLLECTION_AND_SHARING", "PSL_DATA_USAGE_ONLY_COLLECTED", "TRUE")
        must(prefix + "PSL_DATA_USAGE_COLLECTION_AND_SHARING", "PSL_DATA_USAGE_ONLY_SHARED", "TRUE")
        must(prefix + "PSL_DATA_USAGE_EPHEMERAL", "", "FALSE")
        must(prefix + "DATA_USAGE_USER_CONTROL", "PSL_DATA_USAGE_USER_CONTROL_REQUIRED", "TRUE")
        for purpose in ("PSL_ADVERTISING", "PSL_ANALYTICS", "PSL_FRAUD_PREVENTION_SECURITY"):
            must(prefix + "DATA_USAGE_COLLECTION_PURPOSE", purpose, "TRUE")
            must(prefix + "DATA_USAGE_SHARING_PURPOSE", purpose, "TRUE")
    for typ in FORBIDDEN_TYPES:
        for (q, c), v in by_key.items():
            if (q.startswith("PSL_DATA_TYPES_") and c == typ) or q.startswith(f"PSL_DATA_USAGE_RESPONSES:{typ}:"):
                if v:
                    raise ValueError(f"User photos or local content must not be misdeclared: {q}")
    return {"package": PACKAGE, "rows": EXPECTED_COUNT, "adMobDataTypes": sorted(SDK_TYPES),
            "accountCreation": False, "userGeneratedImagesLocal": True,
            "csvVersion": "2026-11-24"}


def apply(text):
    from google.auth.transport.requests import AuthorizedSession
    from publish import get_credentials
    session = AuthorizedSession(get_credentials())
    response = session.post(
        f"https://androidpublisher.googleapis.com/androidpublisher/v3/applications/{PACKAGE}/dataSafety",
        json={"safetyLabels": text}, timeout=90,
    )
    if response.status_code not in (200, 204):
        message = "unknown"
        try:
            message = response.json().get("error", {}).get("message", "")[:180]
        except (ValueError, TypeError):
            pass
        raise RuntimeError(f"Play Data Safety POST rejected HTTP {response.status_code}: {message}")
    return {"status": "GOOGLE_PLAY_DATA_SAFETY_POST_ACCEPTED", "httpStatus": response.status_code,
            "app": PACKAGE, "reviewMayBeRequired": True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm", default="")
    args = parser.parse_args()
    text = CSV.read_text("utf-8")
    details = verify(text)
    print("RIVOSTICKER_DATA_SAFETY_PREFLIGHT=" + json.dumps(details, sort_keys=True), flush=True)
    if not args.apply:
        return
    if args.confirm != CONFIRM:
        raise ValueError("Explicit RivoSticker Data Safety confirmation required")
    result = apply(text)
    print("RIVOSTICKER_DATA_SAFETY_RESULT=" + json.dumps(result, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
