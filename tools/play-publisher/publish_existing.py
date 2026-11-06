#!/usr/bin/env python3
"""Assign an already-uploaded Play Console AAB to a release track.

Does not upload binaries, create a new app, or perform first-time legal declarations.
Draft/internal is the default. The target version must exist in the app's API
bundle inventory, and all commits require explicit confirmation.
"""
from __future__ import annotations

import argparse
import json
import sys

from publish import (
    PACKAGE, LANGUAGE, TRACKS, STATUSES, build_releases,
    get_credentials, get_target_track,
)


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--package", required=True, help="Exact existing applicationId")
    p.add_argument("--version-code", type=int, required=True, help="AAB versionCode uploaded to Google Play")
    p.add_argument("--track", choices=TRACKS, default="internal")
    p.add_argument("--status", choices=STATUSES, default="draft")
    p.add_argument("--name", default="")
    p.add_argument("--notes", default="")
    p.add_argument("--language", default="en-US")
    p.add_argument("--confirm-commit", default="", help="Must equal COMMIT before any API changes")
    p.add_argument("--confirm-production", default="", help="Must equal PUBLISH for production completed")
    p.add_argument("--dry-run", action="store_true", help="Offline validation only, never accesses Google")
    return p


def validate(a: argparse.Namespace) -> None:
    if not PACKAGE.fullmatch(a.package):
        raise ValueError("Invalid Android applicationId")
    if not 1 <= a.version_code <= 2_100_000_000:
        raise ValueError("versionCode must be a positive 32-bit Play version code")
    if len(a.notes) > 500 or len(a.name) > 80:
        raise ValueError("Release notes (500) or name (80) too long")
    if not LANGUAGE.fullmatch(a.language):
        raise ValueError("Invalid release-notes language")
    if a.track == "production" and a.status == "completed" and a.confirm_production != "PUBLISH":
        raise ValueError("Production requires explicit PUBLISH confirmation")
    if not a.dry_run and a.confirm_commit != "COMMIT":
        raise ValueError("Any Play API edit requires explicit COMMIT confirmation")


def uploaded_versions(response: dict) -> set[str]:
    return {str(bundle["versionCode"]) for bundle in response.get("bundles", [])
            if isinstance(bundle, dict) and bundle.get("versionCode") is not None}


def perform(a: argparse.Namespace) -> dict:
    from googleapiclient.discovery import build

    service = build("androidpublisher", "v3", credentials=get_credentials(), cache_discovery=False)
    edits = service.edits()
    # Creating a fresh edit invalidates other uncommitted edits for this app.
    edit = edits.insert(packageName=a.package, body={}).execute()
    eid = edit["id"]
    committed = False
    try:
        inventory = edits.bundles().list(packageName=a.package, editId=eid).execute()
        versions = uploaded_versions(inventory)
        code = str(a.version_code)
        if code not in versions:
            raise ValueError(
                "That versionCode is not visible in the app's current Play bundle inventory. "
                "Complete the first Console upload and save the release; then verify the versionCode."
            )

        target, existing = get_target_track(edits, a.package, eid, a.track)
        for release in existing:
            if code in [str(v) for v in release.get("versionCodes", [])]:
                raise ValueError(
                    "This versionCode already belongs to a release on this track. "
                    "Review its current status in Play Console rather than overwriting it."
                )
        releases = build_releases(a, code, existing)
        edits.tracks().update(
            packageName=a.package,
            editId=eid,
            track=target,
            body={"track": target, "releases": releases},
        ).execute()
        edits.commit(packageName=a.package, editId=eid).execute()
        committed = True
        return {"result": "EDIT_COMMITTED", "package": a.package, "versionCode": a.version_code,
                "track": target, "status": a.status,
                "notice": "Google Play review and first publication may still require console steps"}
    finally:
        if not committed:
            try:
                edits.delete(packageName=a.package, editId=eid).execute()
            except Exception:
                print("CLEANUP_WARNING: uncommitted edit could not be deleted", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        validate(args)
        if args.dry_run:
            print(json.dumps({"result": "OFFLINE_PREFLIGHT_OK", "package": args.package,
                              "versionCode": args.version_code, "track": args.track,
                              "status": args.status}))
            return 0
        print(json.dumps(perform(args)))
        return 0
    except Exception as exc:
        status = getattr(getattr(exc, "resp", None), "status", None)
        error_name = type(exc).__name__
        if isinstance(exc, ValueError):
            # Internal validation errors contain no credentials or server response.
            print(f"PLAY_RELEASE_BLOCKED: {exc}", file=sys.stderr)
        elif status in (401, 403):
            print("PLAY_RELEASE_BLOCKED: service account permissions/auth rejected", file=sys.stderr)
        elif status == 404:
            print("PLAY_RELEASE_BLOCKED: app not accessible or not created in Play Console", file=sys.stderr)
        else:
            print(f"PLAY_RELEASE_ERROR: {error_name}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
