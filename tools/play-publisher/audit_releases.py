#!/usr/bin/env python3
"""Read-only Google Play release audit: no Edits, no uploads, no commits.

Queries documented GET applications/{package}/tracks/{track}/releases for
an explicitly supplied Android package. Does not enumerate all Play apps.
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from urllib.parse import quote
from google.auth.transport.requests import AuthorizedSession

from publish import get_credentials

PACKAGE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)+$")
TRACKS = ("qa", "beta", "production", "alpha")
API = "https://androidpublisher.googleapis.com/androidpublisher/v3"


def validate_package(package: str) -> str:
    if not PACKAGE.fullmatch(package):
        raise ValueError("Invalid package identifier")
    return package


def summarize_response(status: int, payload: dict | None) -> dict:
    """Only include safe fields from the API response; never log a credential or server error body."""
    if status != 200:
        name = {401: "AUTHENTICATION_FAILED", 403: "ACCESS_DENIED", 404: "NOT_FOUND_OR_NOT_ACCESSIBLE",
                400: "INVALID_REQUEST"}.get(status, "HTTP_ERROR")
        return {"result": name, "httpStatus": status}
    releases = (payload or {}).get("releases", [])
    return {
        "result": "OK",
        "releaseCount": len(releases),
        "releases": [
            {"releaseName": str(r.get("releaseName", ""))[:90],
             "lifecycle": r.get("releaseLifecycleState", "UNKNOWN"),
             "versionCodes": [a.get("versionCode") for a in r.get("activeArtifacts", []) if isinstance(a, dict)]}
            for r in releases if isinstance(r, dict)
        ],
    }


def audit(package: str, tracks: tuple[str, ...] = TRACKS) -> dict:
    credentials = get_credentials()
    session = AuthorizedSession(credentials)
    result = {"package": package, "tracks": {}}
    for track in tracks:
        path = f"/applications/{quote(package, safe='')}/tracks/{quote(track, safe='')}/releases"
        try:
            response = session.get(API + path, timeout=25)
            # Avoid printing the response body, which may contain unexpected metadata.
            payload = response.json() if response.status_code == 200 else None
            result["tracks"][track] = summarize_response(response.status_code, payload)
        except Exception as exc:
            result["tracks"][track] = {"result": f"REQUEST_FAILED_{type(exc).__name__}"}
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", required=True)
    args = parser.parse_args(argv)
    try:
        package = validate_package(args.package)
        output = audit(package)
        print("PLAY_RELEASE_AUDIT_JSON_START")
        print(json.dumps(output, ensure_ascii=False, sort_keys=True))
        print("PLAY_RELEASE_AUDIT_JSON_END")
        return 0 if any(item.get("result") == "OK" for item in output["tracks"].values()) else 2
    except Exception as exc:
        print(f"PLAY_RELEASE_AUDIT_FAILED: {type(exc).__name__}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
