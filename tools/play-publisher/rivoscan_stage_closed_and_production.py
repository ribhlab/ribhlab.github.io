#!/usr/bin/env python3
"""Prepare RivoScan closed testing + non-public production draft from a SAVED AAB.

Never uploads a bundle, changes tester lists, completes production, or guesses a
versionCode. Default is offline inspection. --apply needs an explicit confirmation.
"""
from __future__ import annotations
import argparse
import json
import sys
from argparse import Namespace

from audit_releases import audit
from publish import get_credentials, get_target_track, build_releases

PACKAGE = "com.ribhlab.rivoscan"
MIN_VERSION = 99
CLOSED = "alpha"  # Play's default closed testing track; beta is OPEN testing.
PRODUCTION = "production"
CONFIRM = "SETUP_CLOSED_AND_PRODUCTION_DRAFT"
NOTES = (
    "RivoScan for Android: scan and crop documents, organize PDF pages, "
    "convert files, extract text and share completed documents."
)


def available_version(report: dict) -> int | None:
    """Only trust an observed version already attached to a saved Play release."""
    if report.get("package") != PACKAGE:
        return None
    codes = []
    for track, details in report.get("tracks", {}).items():
        if track not in ("qa", "internal", "alpha", "beta", PRODUCTION):
            continue
        if details.get("result") != "OK":
            continue
        for release in details.get("releases", []):
            for value in release.get("versionCodes", []):
                try:
                    code = int(value)
                except (ValueError, TypeError):
                    continue
                if code >= MIN_VERSION:
                    codes.append(code)
    return max(codes) if codes else None


def release_request(code: int, status: str) -> Namespace:
    if code < MIN_VERSION:
        raise ValueError("Refusing older RivoScan builds; current baseline is versionCode 99")
    if status not in ("completed", "draft"):
        raise ValueError("Unexpected status")
    return Namespace(
        package=PACKAGE, version_code=code,
        status=status, name=f"RivoScan Android {code}",
        notes=NOTES, language="en-US", track=CLOSED if status == "completed" else PRODUCTION,
        confirm_production="", confirm_commit="COMMIT",
    )


def stage_track(edits, code: int, requested: str, status: str) -> dict:
    """One self-contained edit per track: closed can succeed if production is blocked."""
    if requested not in (CLOSED, PRODUCTION):
        raise ValueError("Only the approved closed track and production draft are allowed")
    if requested == PRODUCTION and status != "draft":
        raise ValueError("This workflow NEVER publishes live production")
    if requested == CLOSED and status != "completed":
        raise ValueError("Closed testing should be an actual test release, not an inert draft")

    request = release_request(code, status)
    edit = edits.insert(packageName=PACKAGE, body={}).execute()
    eid = edit["id"]
    committed = False
    try:
        inventory = edits.bundles().list(packageName=PACKAGE, editId=eid).execute()
        versions = {str(b.get("versionCode")) for b in inventory.get("bundles", [])}
        if str(code) not in versions:
            return {"result": "BLOCKED_NOT_IN_BUNDLE_INVENTORY", "track": requested, "versionCode": code}
        actual, existing = get_target_track(edits, PACKAGE, eid, requested)
        if actual != requested:
            return {"result": "BLOCKED_UNEXPECTED_TRACK", "track": requested}
        existing_codes = {
            str(v)
            for release in existing
            for v in release.get("versionCodes", [])
        }
        if str(code) in existing_codes:
            return {"result": "ALREADY_ON_TRACK", "track": requested, "versionCode": code}
        # The publisher's existing safety checks reject conflicting drafts,
        # staged and halted releases. Do not bypass them or overwrite a rollout.
        releases = build_releases(request, str(code), existing)
        edits.tracks().update(
            packageName=PACKAGE, editId=eid, track=actual,
            body={"track": actual, "releases": releases},
        ).execute()
        edits.commit(packageName=PACKAGE, editId=eid).execute()
        committed = True
        return {"result": "TRACK_EDIT_COMMITTED", "track": actual,
                "versionCode": code, "status": status,
                "note": "Google Play review and account prerequisites still apply"}
    finally:
        if not committed:
            try:
                edits.delete(packageName=PACKAGE, editId=eid).execute()
            except Exception:
                print("WARNING: could not discard unused RivoScan edit", file=sys.stderr)


def deploy(code: int) -> dict:
    from googleapiclient.discovery import build
    service = build("androidpublisher", "v3", credentials=get_credentials(), cache_discovery=False)
    edits = service.edits()
    results = []
    # Ensure closed test is attempted first. Never make production publicly available.
    for track, status in ((CLOSED, "completed"), (PRODUCTION, "draft")):
        try:
            results.append(stage_track(edits, code, track, status))
        except Exception as exc:
            # Avoid logging API response bodies and secrets.
            http = getattr(getattr(exc, "resp", None), "status", None)
            results.append({"result": "BLOCKED", "track": track,
                            "httpStatus": http, "reason": type(exc).__name__})
    return {"package": PACKAGE, "versionCode": code, "tracks": results,
            "productionIsLive": False}


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--apply", action="store_true")
    p.add_argument("--confirm", default="")
    args = p.parse_args(argv)
    if args.apply and args.confirm != CONFIRM:
        print("BLOCKED: explicit release setup confirmation required", file=sys.stderr)
        return 2
    report = audit(PACKAGE)
    code = available_version(report)
    if code is None:
        print(json.dumps({"result": "WAITING_FOR_SAVED_RIVOSCAN_RELEASE", "package": PACKAGE,
                          "minVersionCode": MIN_VERSION, "tracksAttempted": False}))
        return 0
    if not args.apply:
        print(json.dumps({"result": "READY_TO_PREPARE_CLOSED_AND_PRODUCTION_DRAFT",
                          "versionCode": code, "closedTrack": CLOSED,
                          "production": "draft only"}))
        return 0
    result = deploy(code)
    print("RIVOSCAN_TRACK_SETUP=" + json.dumps(result, sort_keys=True))
    # Treat precondition blocks as actionable, not success. Already-on-track is idempotent.
    closed = next(x for x in result["tracks"] if x["track"] == CLOSED)
    return 0 if closed["result"] in ("TRACK_EDIT_COMMITTED", "ALREADY_ON_TRACK") else 1


if __name__ == "__main__":
    raise SystemExit(main())
