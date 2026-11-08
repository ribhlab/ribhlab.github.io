#!/usr/bin/env python3
"""Promote ONLY the exact owner-verified signed NovaGrid AAB to production.

Never uploads unsigned files, overwrites pending rollouts, or guesses versions.
The expected AAB SHA-256 comes from the user's 2026-11-08 jarsigner report.
If that exact file was not already uploaded and saved in Google Play, stop.
"""
from __future__ import annotations

import argparse
import json
import re
import sys

from publish import get_credentials

PACKAGE = "com.novagrid.cosmicpuzzle"
EXPECTED_SIGNED_AAB_SHA256 = "675ad0331cf6e6afbd3823e55153342377eab39df314ce6033c8de7a74bad04b"
CONFIRM = "PUBLISH_EXACT_SIGNED_NOVAGRID_UPDATE"
RELEASE_NOTES = (
    "New in this update:\n"
    "• Animated candy-glass crystals and brighter multicolor neon effects.\n"
    "• Replay controls in Classic and Blockfall.\n"
    "• Improved rescue blasts when no moves are available.\n"
    "• Gameplay stability, layout and touch refinements."
)


def choose_release(bundles: list[dict], production: list[dict]) -> dict:
    """Plan a precise, non-destructive production update, or return a blocker."""
    matches = [b for b in bundles
               if str(b.get("sha256", "")).lower() == EXPECTED_SIGNED_AAB_SHA256]
    old_codes = [int(c) for rel in production for c in rel.get("versionCodes", [])
                 if str(c).isdigit()]
    old_version = max(old_codes) if old_codes else 0
    if not matches:
        return {"result": "SIGNED_FILE_NOT_SAVED_IN_PLAY", "oldVersionCode": old_version,
                "requires": "Upload NovaGrid-Cosmic-SIGNED.aab matching the confirmed SHA256"}
    if len(matches) != 1 or not str(matches[0].get("versionCode", "")).isdigit():
        return {"result": "INVALID_OR_AMBIGUOUS_SIGNED_AAB", "oldVersionCode": old_version}
    code = int(matches[0]["versionCode"])
    if any(code in [int(c) for c in rel.get("versionCodes", []) if str(c).isdigit()]
           and rel.get("status") == "completed" for rel in production):
        return {"result": "ALREADY_IN_PRODUCTION", "versionCode": code}
    if any(rel.get("status") != "completed" for rel in production):
        return {"result": "PRODUCTION_HAS_PENDING_OR_HALTED_RELEASE",
                "oldVersionCode": old_version, "candidateVersionCode": code}
    if any(len(rel.get("versionCodes", [])) != 1 for rel in production):
        return {"result": "PRODUCTION_HAS_MULTI_BUNDLE_RELEASE",
                "oldVersionCode": old_version}
    if code <= old_version:
        return {"result": "CANDIDATE_NOT_NEWER",
                "oldVersionCode": old_version, "candidateVersionCode": code}
    return {"result": "READY_FOR_PRODUCTION",
            "oldVersionCode": old_version, "candidateVersionCode": code,
            "expectedSha256": EXPECTED_SIGNED_AAB_SHA256}


def production_update() -> dict:
    from googleapiclient.discovery import build

    edits = build("androidpublisher", "v3", credentials=get_credentials(),
                  cache_discovery=False).edits()
    # Do not touch any Play track if the AAB isn't the exact signed file.
    edit = edits.insert(packageName=PACKAGE, body={}).execute()
    eid = edit["id"]
    committed = False
    try:
        bundles = edits.bundles().list(packageName=PACKAGE, editId=eid).execute().get("bundles", [])
        tracks = edits.tracks().list(packageName=PACKAGE, editId=eid).execute().get("tracks", [])
        production = next((x.get("releases", []) for x in tracks
                           if x.get("track") == "production"), [])
        plan = choose_release(bundles, production)
        if plan["result"] != "READY_FOR_PRODUCTION":
            return plan
        version_code = plan["candidateVersionCode"]
        edits.tracks().update(
            packageName=PACKAGE,
            editId=eid,
            track="production",
            body={"track": "production", "releases": [{
                "status": "completed",
                "versionCodes": [str(version_code)],
                "name": f"NovaGrid Cosmic Block Puzzle — {version_code}",
                "releaseNotes": [{"language": "en-US", "text": RELEASE_NOTES}],
            }]},
        ).execute()
        # Commit only after Google accepts the track update. Account publishing
        # status and review can still prevent it appearing to players immediately.
        edits.commit(packageName=PACKAGE, editId=eid).execute()
        committed = True
        return {"result": "PRODUCTION_EDIT_COMMITTED",
                "package": PACKAGE, "versionCode": version_code,
                "previousVersionCode": plan["oldVersionCode"],
                "releaseStatus": "completed",
                "requiresStoreReview": "Check Play Console Publishing overview"}
    finally:
        if not committed:
            try:
                edits.delete(packageName=PACKAGE, editId=eid).execute()
            except Exception:
                print("NOVAGRID_PRODUCTION_CLEANUP_WARNING", file=sys.stderr)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm", default="")
    args = parser.parse_args(argv)
    if not args.apply:
        print("NOVAGRID_PRODUCTION_PREFLIGHT=" + json.dumps({
            "result": "OFFLINE_CONFIRMED_PACKAGE_AND_HASH",
            "package": PACKAGE, "expectedSha256": EXPECTED_SIGNED_AAB_SHA256}))
        return 0
    if args.confirm != CONFIRM:
        print("NOVAGRID_PRODUCTION_BLOCKED: confirmation missing", file=sys.stderr)
        return 2
    try:
        result = production_update()
        print("NOVAGRID_PRODUCTION_RESULT=" + json.dumps(result, sort_keys=True))
        return 0 if result["result"] in ("PRODUCTION_EDIT_COMMITTED", "ALREADY_IN_PRODUCTION") else 2
    except Exception as exc:
        code = getattr(getattr(exc, "resp", None), "status", None)
        print("NOVAGRID_PRODUCTION_API_ERROR=" + json.dumps({
            "exception": type(exc).__name__, "httpStatus": code,
            "committed": False,
        }), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
