#!/usr/bin/env python3
"""Atomic normal TradingFiew 1.0.4 update (code5) for Production.

Strictly verifies the current code4 production state and signed bundle identity
before changing any track. No advertising campaigns or store title changes.
Only run after independent signed Android emulator QA succeeds.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from publish import get_credentials

PACKAGE = "com.ribhlab.tradingfiew"
VERSION = "5"
RELEASE_NAME = "TradingFiew 1.0.4"


def publish(bundle: Path) -> int:
    if not bundle.is_file() or bundle.suffix != ".aab" or bundle.stat().st_size < 100000:
        raise RuntimeError("Signed TradingFiew version5 AAB missing")
    edits = build(
        "androidpublisher", "v3", credentials=get_credentials(),
        cache_discovery=False
    ).edits()
    eid = None
    committed = False
    try:
        eid = edits.insert(packageName=PACKAGE, body={}).execute()["id"]
        args = {"packageName": PACKAGE, "editId": eid}
        inventory = edits.bundles().list(**args).execute().get("bundles", [])
        existing_codes = {str(b.get("versionCode")) for b in inventory}
        if "4" not in existing_codes or any(
            code.isdigit() and int(code) > 5 for code in existing_codes
        ):
            raise RuntimeError("Unexpected bundle inventory; refusing production update")
        details = edits.details().get(**args).execute()
        if details.get("contactWebsite", "").rstrip("/") != "https://tradingfiew.github.io":
            raise RuntimeError("Unexpected app website; refusing production update")
        track = edits.tracks().get(**args, track="production").execute()
        releases = track.get("releases", [])
        if len(releases) != 1:
            raise RuntimeError("Expected one existing Production release")
        old = releases[0]
        previous_codes = [str(c) for c in old.get("versionCodes", [])]
        if previous_codes == ["5"] and old.get("status") == "completed":
            print("TRADINGFIEW_V5_PRODUCTION=" + json.dumps({
                "result": "ALREADY_COMPLETED", "package": PACKAGE, "versionCode": 5
            }), flush=True)
            return 0
        if previous_codes != ["4"] or old.get("status") != "completed":
            raise RuntimeError("Expected Production code4 completed; refusing replace")
        if VERSION not in existing_codes:
            media = MediaFileUpload(
                str(bundle), mimetype="application/octet-stream",
                resumable=True, chunksize=8 * 1024 * 1024
            )
            result = edits.bundles().upload(**args, media_body=media).execute()
            if str(result.get("versionCode")) != VERSION:
                raise RuntimeError("Google Play returned an unexpected bundle version")
        release = {
            "name": RELEASE_NAME, "status": "completed", "versionCodes": [VERSION],
            "releaseNotes": [
                {"language": "en-US", "text":
                 "Improves Android startup stability and chart compatibility."}
            ],
        }
        edits.tracks().update(
            **args, track="production",
            body={"track": "production", "releases": [release]}
        ).execute()
        edits.validate(**args).execute()
        edits.commit(**args).execute()
        committed = True
        verify_id = None
        try:
            verify_id = edits.insert(packageName=PACKAGE, body={}).execute()["id"]
            current = edits.tracks().get(
                packageName=PACKAGE, editId=verify_id, track="production"
            ).execute()
            state = current.get("releases", [])
            verified = len(state) == 1 and state[0].get("status") == "completed" and [
                str(c) for c in state[0].get("versionCodes", [])
            ] == [VERSION]
            print("TRADINGFIEW_V5_PRODUCTION=" + json.dumps({
                "result": "COMMITTED_AND_VERIFIED" if verified else "COMMITTED_NEEDS_REVIEW",
                "package": PACKAGE, "versionCode": 5, "committed": True,
                "status": state[0].get("status") if state else "missing",
                "publicStoreAvailabilityNotGuaranteed": True
            }), flush=True)
            if not verified:
                return 5
        finally:
            if verify_id:
                try: edits.delete(packageName=PACKAGE, editId=verify_id).execute()
                except Exception: print("PLAY_VERIFY_EDIT_CLEANUP_FAILED", flush=True)
        return 0
    except HttpError as error:
        detail = ""
        try: detail = json.loads(error.content).get("error", {}).get("message", "")[:350]
        except Exception: pass
        print("TRADINGFIEW_V5_PRODUCTION=" + json.dumps({
            "result": "PLAY_API_REJECTED", "code": error.resp.status,
            "detail": detail, "committed": committed
        }), flush=True)
        return 3
    except Exception as error:
        print("TRADINGFIEW_V5_PRODUCTION=" + json.dumps({
            "result": "NOT_PUBLISHED", "reason": str(error)[:400],
            "committed": committed
        }), flush=True)
        return 4
    finally:
        if eid and not committed:
            try: edits.delete(packageName=PACKAGE, editId=eid).execute()
            except Exception: print("PLAY_EDIT_CLEANUP_FAILED", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--aab", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm", default="")
    args = parser.parse_args()
    if not args.apply or args.confirm != "PUBLISH_TRADINGFIEW_5":
        print("SAFE_MODE: requires --apply --confirm PUBLISH_TRADINGFIEW_5")
        return 2
    return publish(args.aab)


if __name__ == "__main__":
    sys.exit(main())
