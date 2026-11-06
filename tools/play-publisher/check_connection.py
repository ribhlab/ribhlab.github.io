#!/usr/bin/env python3
"""Verify a GitHub Actions service-account secret and optional Play Console app access.

Never uploads a bundle, commits a release, or changes app store data.
If a package is supplied, creates and deletes an *uncommitted* edit.
"""
from __future__ import annotations

import argparse
import re
import sys

from publish import get_credentials

PACKAGE_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+$")


def validate_package(package: str) -> str:
    if package and not PACKAGE_PATTERN.fullmatch(package):
        raise ValueError("Invalid Android package name")
    return package


def run_check(package: str) -> None:
    from google.auth.transport.requests import Request

    credentials = get_credentials()
    credentials.refresh(Request())
    if not credentials.valid:
        raise RuntimeError("Service account could not obtain a valid access token")
    print("TOKEN_OK: service account JSON is usable; OAuth token obtained.")
    if not package:
        print("APP_NOT_CHECKED: provide an existing Play Console package name to verify API access.")
        return

    from googleapiclient.discovery import build

    client = build("androidpublisher", "v3", credentials=credentials, cache_discovery=False)
    edits = client.edits()
    edit_id = None
    try:
        created = edits.insert(packageName=package, body={}).execute()
        edit_id = created["id"]
        print("APP_API_OK: access to selected Play Console app confirmed.")
    finally:
        if edit_id:
            # Delete the uncommitted edit; never commit or publish.
            edits.delete(packageName=package, editId=edit_id).execute()
            print("CLEANUP_OK: temporary uncommitted edit deleted.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", default="", help="Optional existing appId (e.g. com.ribhlab.rivoscan)")
    parser.add_argument("--confirm-temp-edit", action="store_true",
                        help="Acknowledge temporary edit may invalidate another uncommitted edit")
    args = parser.parse_args(argv)
    try:
        package = validate_package(args.package.strip())
        if package and not args.confirm_temp_edit:
            raise ValueError("App check requires --confirm-temp-edit; creating an edit may invalidate an existing uncommitted edit")
        run_check(package)
        return 0
    except Exception as exc:
        # Avoid including API error text, which could contain sensitive metadata.
        status = getattr(getattr(exc, "resp", None), "status", None)
        if status in (401, 403):
            print("APP_API_DENIED: permission/authentication failed. Check service account invitation and app access.", file=sys.stderr)
        elif status == 404:
            print("APP_NOT_FOUND: app package may not exist in Play Console or service account cannot access it.", file=sys.stderr)
        else:
            print(f"CHECK_FAILED: {type(exc).__name__}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
