#!/usr/bin/env python3
"""Update ONLY an app's official RibhLab website in Play Store developer contact.

No AAB upload, release track, listing text, ratings, advertising data,
screenshots, icon, feature graphic, privacy policy or permissions are changed.

The Play edit is explicitly gated. Never run during uncommitted Play Console
edits or an active app review unless a restart is intentionally authorized.
"""
from __future__ import annotations

import argparse
import json
import re
import sys

OFFICIAL_WEBSITES = {
    "com.ribhlab.rivoscan": "https://ribhlab.github.io/rivoscan/",
    "com.novagrid.cosmicpuzzle": "https://ribhlab.github.io/novagrid/",
    "com.ribhlab.tradingfiew": "https://ribhlab.github.io/tradingfiew/",
    "com.ribhlab.ribhmeasure": "https://ribhlab.github.io/ribhmeasure/",
    "com.rivocaption.editor": "https://ribhlab.github.io/rivocaption/",
    "com.ribhlab.rivotalk": "https://ribhlab.github.io/rivotalk/",
    "com.ribhlab.rivosticker": "https://ribhlab.github.io/rivosticker/",
    "com.ribhlab.rivonfc": "https://ribhlab.github.io/rivonfc/",
}
CONFIRMATION = "SET_WEBSITE_ONLY"
PACKAGE_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]*(?:[.][A-Za-z][A-Za-z0-9_]*)+$")


def verified_website(package: str) -> str:
    if package not in OFFICIAL_WEBSITES or not PACKAGE_PATTERN.fullmatch(package):
        raise ValueError("Package not in locked RibhLab app website allowlist")
    website = OFFICIAL_WEBSITES[package]
    if not website.startswith("https://ribhlab.github.io/") or not website.endswith("/"):
        raise ValueError("Unsafe RibhLab website URL")
    return website


def apply_contact_website(package: str) -> dict:
    from googleapiclient.discovery import build
    from publish import get_credentials

    website = verified_website(package)
    api = build("androidpublisher", "v3", credentials=get_credentials(), cache_discovery=False)
    edits = api.edits()
    edit_id = edits.insert(packageName=package, body={}).execute()["id"]
    args = {"packageName": package, "editId": edit_id}
    committed = False
    try:
        before = edits.details().get(**args).execute()
        old = before.get("contactWebsite", "")
        if old == website:
            return {"result": "ALREADY_CORRECT_NO_COMMIT", "package": package, "website": website}
        edits.details().patch(**args, body={"contactWebsite": website}).execute()
        after = edits.details().get(**args).execute()
        if after.get("contactWebsite") != website:
            raise RuntimeError("Google Play did not echo the requested developer website")
        # Confirm the rest of the app-details payload was not changed by our patch.
        for field in ("defaultLanguage", "contactEmail", "contactPhone"):
            if before.get(field) != after.get(field):
                raise RuntimeError("Unexpected mutation of Play appDetails field: " + field)
        edits.validate(**args).execute()
        result = edits.commit(**args, changesInReviewBehavior="ERROR_IF_IN_REVIEW").execute()
        committed = True
        return {"result": "APP_WEBSITE_COMMITTED", "package": package,
                "oldWebsite": old, "website": website,
                "editExpired": result.get("id") if isinstance(result, dict) else None,
                "releaseChanged": False, "listingTextChanged": False, "imagesChanged": False}
    finally:
        if not committed:
            try:
                edits.delete(**args).execute()
            except Exception:
                print("WARNING: could not clean up uncommitted Play edit", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm", default="")
    args = parser.parse_args(argv)
    try:
        site = verified_website(args.package)
        if not args.apply:
            print(json.dumps({"result": "DRY_RUN_NO_PLAY_API", "package": args.package,
                              "website": site}, sort_keys=True))
            return 0
        if args.confirm != CONFIRMATION:
            raise ValueError("Missing explicit SET_WEBSITE_ONLY confirmation")
        result = apply_contact_website(args.package)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except Exception as exc:
        status = getattr(getattr(exc, "resp", None), "status", None)
        print(json.dumps({"result": "FAILED", "type": type(exc).__name__,
                          "http_status": status,
                          "message": str(exc)[:300]}, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
