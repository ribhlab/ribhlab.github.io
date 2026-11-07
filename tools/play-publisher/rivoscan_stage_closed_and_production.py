#!/usr/bin/env python3
"""Promote an EXISTING saved Internal Testing AAB to closed + production draft.

Never uploads a bundle, changes tester lists, completes production, or guesses a
versionCode. Default does not change tracks. --apply needs explicit confirmation.
"""
from __future__ import annotations
import argparse
import json
import sys
import re
from argparse import Namespace

from publish import get_credentials, get_target_track, build_releases

PACKAGE = "com.ribhlab.rivoscan"
MIN_VERSION = 74
CLOSED = "alpha"  # Play's default closed testing track; beta is OPEN testing.
PRODUCTION = "production"
CONFIRM = "SETUP_CLOSED_AND_PRODUCTION_DRAFT"
NOTES = (
    "RivoScan for Android: scan and crop documents, organize PDF pages, "
    "convert files, extract text and share completed documents."
)


def select_internal_bundle(inventory: dict, tracks: list[dict]) -> int | None:
    """Promote only a SAVED AAB already assigned to Internal Testing.

    Other uploaded bundles might be experiments or unfinished drafts; do not
    take the largest versionCode unless it belongs to the internal release.
    """
    codes = {int(b["versionCode"]) for b in inventory.get("bundles", [])
             if isinstance(b, dict) and str(b.get("versionCode", "")).isdigit()}
    candidates = []
    for track in tracks:
        if track.get("track") not in ("qa", "internal"):
            continue
        for release in track.get("releases", []):
            if release.get("status") not in ("completed", "draft"):
                continue
            for raw in release.get("versionCodes", []):
                if str(raw).isdigit() and int(raw) in codes and int(raw) >= MIN_VERSION:
                    candidates.append(int(raw))
    return max(candidates) if candidates else None


def saved_internal_version() -> int | None:
    """Read the actual internal release and AAB inventory; no commit or upload."""
    from googleapiclient.discovery import build
    edits = build("androidpublisher", "v3", credentials=get_credentials(),
                  cache_discovery=False).edits()
    edit = edits.insert(packageName=PACKAGE, body={}).execute()
    eid = edit["id"]
    try:
        bundles = edits.bundles().list(packageName=PACKAGE, editId=eid).execute()
        tracks = edits.tracks().list(packageName=PACKAGE, editId=eid).execute()
        code = select_internal_bundle(bundles, tracks.get("tracks", []))
        print("RIVOSCAN_INTERNAL_SOURCE=" + json.dumps({
            "package": PACKAGE, "versionCode": code,
            "eligibleForClosed": code is not None,
        }, sort_keys=True))
        return code
    finally:
        try:
            edits.delete(packageName=PACKAGE, editId=eid).execute()
        except Exception:
            print("WARNING: uncommitted internal inventory edit cleanup failed",
                  file=sys.stderr)


def release_request(code: int, status: str) -> Namespace:
    if code < MIN_VERSION:
        raise ValueError("Refusing older RivoScan builds; earliest confirmed Internal Testing versionCode is 74")
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
    if requested == CLOSED and status not in ("completed", "draft"):
        raise ValueError("Invalid closed testing status")

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
        matches = [item for item in existing
                   if str(code) in {str(v) for v in item.get("versionCodes", [])}]
        if matches:
            if len(matches) == 1 and matches[0].get("status") == status:
                return {"result": "ALREADY_ON_TRACK", "track": requested, "versionCode": code,
                        "status": status}
            # The user asked to activate the CLOSED test; promoting a matching
            # saved draft is safe only when there is no competing staged/paused
            # release or multi-artifact release on the same track.
            if (requested == CLOSED and len(matches) == 1
                    and matches[0].get("status") == "draft"
                    and len(matches[0].get("versionCodes", [])) == 1
                    and all(r.get("status") == "completed"
                            for r in existing if r is not matches[0])):
                releases = build_releases(
                    request, str(code), [r for r in existing if r is not matches[0]])
            else:
                return {"result": "BLOCKED_EXISTING_RELEASE_STATUS", "track": requested,
                        "versionCode": code}
        elif (requested == PRODUCTION and len(existing) == 1
              and existing[0].get("status") == "draft"
              and not existing[0].get("versionCodes")):
            # Replace ONLY an empty placeholder production draft; never alter a
            # draft containing another version or a staged rollout.
            releases = build_releases(request, str(code), [])
        else:
            # Reject conflicting drafts, staged and halted releases.
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


def safe_api_error(exc: Exception) -> dict:
    """Emit an actionable Google error without access tokens, URLs or email."""
    http = getattr(getattr(exc, "resp", None), "status", None)
    output = {"httpStatus": http, "reason": type(exc).__name__}
    if http in (400, 403, 404, 409):
        try:
            body = json.loads(getattr(exc, "content", b"{}").decode("utf-8"))
            e = body.get("error") or {}
            msg = str(e.get("message") or "")[:400]
            msg = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[email-redacted]", msg)
            msg = re.sub(r"https?://\S+", "[url-redacted]", msg)
            msg = re.sub(r"\b[A-Za-z0-9_-]{48,}\b", "[token-redacted]", msg)
            msg = msg.replace("\n", " ").replace("\r", " ")
            output["googleReason"] = msg
            output["googleStatus"] = str(e.get("status") or "")[:48]
        except (ValueError, AttributeError, TypeError):
            pass
    return output


def deploy(code: int) -> dict:
    from googleapiclient.discovery import build
    service = build("androidpublisher", "v3", credentials=get_credentials(), cache_discovery=False)
    edits = service.edits()
    results = []
    # First try the requested active closed test, then closed draft as fallback
    # if Google blocks the active release. Production remains DRAFT ONLY.
    closed_active = None
    try:
        closed_active = stage_track(edits, code, CLOSED, "completed")
        results.append(closed_active)
    except Exception as exc:
        results.append({"result": "BLOCKED", "track": CLOSED, "status": "completed",
                        **safe_api_error(exc)})
    if (not closed_active or
            closed_active.get("result") not in ("TRACK_EDIT_COMMITTED", "ALREADY_ON_TRACK")):
        try:
            fallback = stage_track(edits, code, CLOSED, "draft")
            results.append(fallback)
        except Exception as exc:
            results.append({"result": "BLOCKED", "track": CLOSED, "status": "draft",
                            **safe_api_error(exc)})
    # A production DRAFT is a non-public administrative step, independent of
    # closing the test. Google may reject it until production access is granted.
    try:
        results.append(stage_track(edits, code, PRODUCTION, "draft"))
    except Exception as exc:
        results.append({"result": "BLOCKED", "track": PRODUCTION, "status": "draft",
                        **safe_api_error(exc)})
    return {"package": PACKAGE, "versionCode": code, "tracks": results,
            "productionPublicationAttempted": False}



def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--apply", action="store_true")
    p.add_argument("--confirm", default="")
    args = p.parse_args(argv)
    if args.apply and args.confirm != CONFIRM:
        print("BLOCKED: explicit release setup confirmation required", file=sys.stderr)
        return 2
    code = saved_internal_version()
    if code is None:
        print(json.dumps({"result": "WAITING_FOR_SAVED_INTERNAL_AAB", "package": PACKAGE,
                          "minVersionCode": MIN_VERSION, "tracksAttempted": False}))
        return 0
    if not args.apply:
        print(json.dumps({"result": "READY_TO_PREPARE_CLOSED_AND_PRODUCTION_DRAFT",
                          "versionCode": code, "closedTrack": CLOSED,
                          "production": "draft only"}))
        return 0
    result = deploy(code)
    print("RIVOSCAN_TRACK_SETUP=" + json.dumps(result, sort_keys=True))
    # Do not report a successful release if all target edits were blocked.
    return 0 if any(item.get("result") in ("TRACK_EDIT_COMMITTED", "ALREADY_ON_TRACK")
                    for item in result["tracks"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
