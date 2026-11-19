#!/usr/bin/env python3
"""One-time, no-cost Play store organic localization: add missing locales ONLY.

Never buys advertising, changes app content declarations, release tracks,
screenshots, signing, existing locales, contact details or prices.
Google Android Publisher Edits API needs a temporary edit to read listings.
Do not run while manually editing unsaved listing changes in Play Console.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SOURCE = Path(__file__).with_name("organic-localizations-2026-11-19.json")
ALLOW_APPS = {"com.novagrid.cosmicpuzzle", "com.ribhlab.tradingfiew"}
ALLOW_LOCALES = {"es-ES", "de-DE", "pt-BR", "it-IT"}
FIELDS = (("title", 30), ("shortDescription", 80), ("fullDescription", 4000))


def load_and_validate(path: Path = SOURCE) -> dict:
    doc = json.loads(path.read_text(encoding="utf-8"))
    apps = doc.get("apps")
    if not isinstance(apps, dict) or set(apps) != ALLOW_APPS:
        raise ValueError("Unexpected app IDs: cannot publish")
    for pkg, locales in apps.items():
        if not isinstance(locales, dict) or set(locales) != ALLOW_LOCALES:
            raise ValueError("Unexpected locale set for " + pkg)
        for language, data in locales.items():
            if not isinstance(data, dict) or set(data) != {k for k, _ in FIELDS}:
                raise ValueError("Unexpected listing fields")
            for field, limit in FIELDS:
                value = data[field]
                if not isinstance(value, str) or not value.strip() or len(value) > limit:
                    raise ValueError(f"Invalid {pkg}/{language}/{field}: Play limit {limit}")
                if "\\x00" in value:
                    raise ValueError("Invalid null character")
    return apps


def find_missing(existing: list[dict], locales: dict) -> dict:
    known = {row.get("language") for row in existing if isinstance(row, dict)}
    return {lang: values for lang, values in locales.items() if lang not in known}


def apply_to_package(package: str, desired: dict, api) -> dict:
    """Add missing store listing locales to existing Play app, or do nothing.

    On validation failure, delete the temporary edit. An accepted commit is not
    proof that Google has finished its manual review or made it live.
    """
    edits = api.edits()
    edit = None
    committed = False
    try:
        edit = edits.insert(packageName=package, body={}).execute()
        args = {"packageName": package, "editId": edit["id"]}
        existing = edits.listings().list(**args).execute().get("listings", [])
        missing = find_missing(existing, desired)
        if not missing:
            return {"package": package, "result": "NO_CHANGE", "alreadyPresent": sorted(desired)}
        for lang, data in sorted(missing.items()):
            payload = {"language": lang, **data}
            edits.listings().update(**args, language=lang, body=payload).execute()
        edits.validate(**args).execute()
        edits.commit(**args).execute()
        committed = True
        return {"package": package, "result": "GOOGLE_PLAY_EDIT_COMMITTED",
                "addedLocales": sorted(missing),
                "preservedExistingLocales": True, "paidAds": False,
                "releaseTrackChanged": False, "reviewMayStillBePending": True}
    finally:
        if edit and not committed:
            try:
                edits.delete(packageName=package, editId=edit["id"]).execute()
            except Exception:
                print("PLAY_EDIT_CLEANUP_FAILED package=" + package, file=sys.stderr)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    try:
        apps = load_and_validate()
        if not args.apply:
            print("ORGANIC_LISTINGS_VALID=" + json.dumps(
                {pkg: sorted(locales) for pkg, locales in apps.items()}, sort_keys=True))
            return 0

        from googleapiclient.discovery import build
        from publish import get_credentials
        api = build("androidpublisher", "v3",
                    credentials=get_credentials(), cache_discovery=False)
        failed = False
        for pkg, desired in sorted(apps.items()):
            try:
                print("PLAY_ORGANIC_RESULT=" + json.dumps(
                    apply_to_package(pkg, desired, api), sort_keys=True))
            except Exception as exc:
                failed = True
                status = getattr(getattr(exc, "resp", None), "status", None)
                print("PLAY_ORGANIC_ERROR=" + json.dumps(
                    {"package": pkg, "errorType": type(exc).__name__,
                     "httpStatus": status, "committed": False}, sort_keys=True),
                    file=sys.stderr)
        return 1 if failed else 0
    except Exception as exc:
        print("PLAY_ORGANIC_VALIDATION_FAILED=" + type(exc).__name__, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
