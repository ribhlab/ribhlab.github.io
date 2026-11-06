#!/usr/bin/env python3
"""Safely upload a signed Android App Bundle to an existing Google Play app.

The default is a draft in the internal testing track. Nothing is published
without an explicit --status completed, and production needs another gate.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

PACKAGE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+$")
LANGUAGE = re.compile(r"^[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$")
TRACKS = ("internal", "alpha", "beta", "production")
STATUSES = ("draft", "completed")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aab", required=True, type=Path, help="Signed .aab from an existing Play Console app")
    parser.add_argument("--package", required=True, help="Existing Android applicationId")
    parser.add_argument("--track", choices=TRACKS, default="internal")
    parser.add_argument("--status", choices=STATUSES, default="draft")
    parser.add_argument("--name", default="", help="Optional release name")
    parser.add_argument("--notes", default="", help="What is new (max 500 characters)")
    parser.add_argument("--language", default="en-US", help="BCP-47 locale for notes")
    parser.add_argument("--confirm-production", default="", help="Must equal PUBLISH for a completed production release")
    parser.add_argument("--dry-run", action="store_true", help="Validate only; do not call Play API")
    return parser


def validate(args: argparse.Namespace) -> Path:
    if not PACKAGE.fullmatch(args.package):
        raise ValueError("Invalid Android package name")
    if args.aab.suffix.lower() != ".aab" or not args.aab.is_file():
        raise ValueError("A signed .aab file must exist")
    if args.aab.stat().st_size == 0:
        raise ValueError("AAB file is empty")
    if not LANGUAGE.fullmatch(args.language):
        raise ValueError("Invalid release notes language")
    if len(args.notes) > 500:
        raise ValueError("Release notes must be 500 characters or fewer")
    if len(args.name) > 80:
        raise ValueError("Release name must be 80 characters or fewer")
    if args.track == "production" and args.status == "completed" and args.confirm_production != "PUBLISH":
        raise ValueError("Publishing to production requires --confirm-production PUBLISH")
    return args.aab.resolve()


def get_credentials():
    from google.oauth2 import service_account

    secret = os.environ.get("GOOGLE_PLAY_SERVICE_ACCOUNT_JSON", "").strip()
    if not secret:
        raise ValueError("Missing GOOGLE_PLAY_SERVICE_ACCOUNT_JSON Actions secret")
    try:
        credentials_info = json.loads(secret)
    except json.JSONDecodeError as exc:
        raise ValueError("GOOGLE_PLAY_SERVICE_ACCOUNT_JSON must be valid JSON") from exc
    if credentials_info.get("type") != "service_account":
        raise ValueError("GOOGLE_PLAY_SERVICE_ACCOUNT_JSON must contain service account credentials")
    return service_account.Credentials.from_service_account_info(
        credentials_info,
        scopes=["https://www.googleapis.com/auth/androidpublisher"],
    )


def get_target_track(edits, package: str, edit_id: str, requested: str) -> tuple[str, list[dict]]:
    """Resolve the internal/qa alias against actual Play tracks."""
    result = edits.tracks().list(packageName=package, editId=edit_id).execute()
    known = {
        item["track"]: item.get("releases", [])
        for item in result.get("tracks", [])
        if item.get("track")
    }
    if requested == "internal":
        # Google's current public docs call the internal track "qa".
        # Some existing API integrations use the legacy "internal" name.
        track = next((name for name in ("qa", "internal") if name in known), "qa")
    else:
        track = requested
    return track, known.get(track, [])


def build_releases(args: argparse.Namespace, code: str, existing: list[dict]) -> list[dict]:
    """Keep existing serving releases intact when preparing a new draft."""
    release = {"status": args.status, "versionCodes": [str(code)]}
    if args.name:
        release["name"] = args.name
    if args.notes:
        release["releaseNotes"] = [{"language": args.language, "text": args.notes}]

    if args.status == "draft":
        if any(item.get("status") == "draft" for item in existing):
            raise ValueError("An existing draft already occupies this track; resolve it in Play Console first")
        return [*existing, release]

    # A completed release replaces the serving version. Never silently override
    # a staged, halted, or drafted release, or a multi-APK compatibility setup.
    if any(item.get("status") != "completed" for item in existing):
        raise ValueError("Track contains a draft, staged, or halted release; review in Play Console first")
    if any(len(item.get("versionCodes", [])) > 1 for item in existing):
        raise ValueError("Existing multi-APK release requires manual review in Play Console")
    return [release]


def upload(args: argparse.Namespace, aab: Path) -> dict:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    client = build("androidpublisher", "v3", credentials=get_credentials(), cache_discovery=False)
    edits = client.edits()
    edit = edits.insert(packageName=args.package, body={}).execute()
    edit_id = edit["id"]
    target_track, existing = get_target_track(edits, args.package, edit_id, args.track)
    # Apply potentially destructive track changes only after checking existing releases.
    # Version code is known only after upload; this edit is not committed until all succeed.
    if args.status == "draft" and any(item.get("status") == "draft" for item in existing):
        raise ValueError("Track already has a draft release; resolve it in Play Console")
    if args.status == "completed":
        if any(item.get("status") != "completed" for item in existing):
            raise ValueError("Track has staged, halted, or draft releases; resolve them before publishing")
        if any(len(item.get("versionCodes", [])) > 1 for item in existing):
            raise ValueError("Existing multi-APK configuration requires manual review")

    media = MediaFileUpload(str(aab), mimetype="application/octet-stream", resumable=True)
    bundle = edits.bundles().upload(
        packageName=args.package, editId=edit_id, media_body=media
    ).execute()
    code = str(bundle["versionCode"])

    releases = build_releases(args, code, existing)
    edits.tracks().update(
        packageName=args.package,
        editId=edit_id,
        track=target_track,
        body={"track": target_track, "releases": releases},
    ).execute()
    edits.commit(packageName=args.package, editId=edit_id).execute()
    return {"package": args.package, "track": target_track, "status": args.status, "versionCode": code}


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        aab = validate(args)
        if args.dry_run:
            print(f"PREVIEW ONLY | {args.package} | {args.track} | {args.status} | {aab.name}")
            return 0
        result = upload(args, aab)
        print("Committed Play API edit:", json.dumps(result, ensure_ascii=False))
        print("Google may still require Play Console review/approval; check Console status.")
        return 0
    except Exception as exc:
        print(f"Publisher failed: {type(exc).__name__}: {str(exc)[:350]}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
