#!/usr/bin/env python3
"""Safely send only the already-saved RivoMeasure Closed Alpha changes for review.

RivoMeasure production versionCode 13 is already PUBLISHED. The Alpha release
versionCode 13 is currently NOT_SENT_FOR_REVIEW (verified Nov 27, 2026).

Does not upload an AAB, change releases, lists, metadata or any other app.
Commits an empty Play edit to request review of ALREADY-SAVED Console changes.
Never cancels an existing review: ERROR_IF_IN_REVIEW is mandatory.

The public release-lifecycle endpoint verifies the result independently.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from urllib.parse import quote

PACKAGE = "com.ribhlab.ribhmeasure"
VERSION = 13
API = "https://androidpublisher.googleapis.com/androidpublisher/v3"
NOT_SENT = "RELEASE_LIFECYCLE_STATE_NOT_SENT_FOR_REVIEW"
PUBLISHED = "RELEASE_LIFECYCLE_STATE_PUBLISHED"
ALLOWED_AFTER = {
    "RELEASE_LIFECYCLE_STATE_IN_REVIEW",
    "RELEASE_LIFECYCLE_STATE_APPROVED_NOT_PUBLISHED",
    "RELEASE_LIFECYCLE_STATE_PUBLISHED",
}
CONFIRM = "SEND_RIVOMEASURE_ALPHA_13"


def safe_release_states(production: dict, alpha: dict) -> str:
    """Require one exact known release per track; never touch an unknown release."""
    def matched(payload: dict, state: str, name: str) -> bool:
        releases = payload.get("releases")
        if not isinstance(releases, list) or len(releases) != 1:
            return False
        release = releases[0]
        if release.get("releaseName") != name or release.get("releaseLifecycleState") != state:
            return False
        versions = [v.get("versionCode") for v in release.get("activeArtifacts", [])]
        return versions == [VERSION]

    if not matched(production, PUBLISHED, "RivoMeasure 1.3.9"):
        raise ValueError("Production release is not the expected published code 13; refusing edit")
    if matched(alpha, NOT_SENT, "RivoMeasure 1.3.9 – Closed Alpha"):
        return "PENDING_ALPHA_13"
    if matched(alpha, "RELEASE_LIFECYCLE_STATE_IN_REVIEW", "RivoMeasure 1.3.9 – Closed Alpha"):
        return "ALREADY_IN_REVIEW"
    if matched(alpha, PUBLISHED, "RivoMeasure 1.3.9 – Closed Alpha"):
        return "ALREADY_PUBLISHED"
    raise ValueError("Alpha release has changed or is not the expected unsent code 13; refusing edit")


def fetch_track(session, track: str) -> dict:
    uri = f"{API}/applications/{quote(PACKAGE, safe='')}/tracks/{quote(track, safe='')}/releases"
    response = session.get(uri, timeout=25)
    if response.status_code != 200:
        raise RuntimeError(f"Read-only {track} release audit failed HTTP {response.status_code}")
    return response.json()


def status(session) -> str:
    return safe_release_states(fetch_track(session, "production"), fetch_track(session, "alpha"))


def submit_pending_alpha(credentials, session) -> dict:
    from googleapiclient.discovery import build

    state = status(session)
    if state in {"ALREADY_IN_REVIEW", "ALREADY_PUBLISHED"}:
        return {"result": state, "commitAttempted": False}
    if state != "PENDING_ALPHA_13":
        raise ValueError("Unexpected RivoMeasure preflight state")

    edits = build("androidpublisher", "v3", credentials=credentials, cache_discovery=False).edits()
    edit_id = edits.insert(packageName=PACKAGE, body={}).execute()["id"]
    committed = False
    try:
        # Do NOT patch any track or metadata. Console already saved exactly
        # four pending Alpha changes. An edit commit can submit those existing
        # Console changes; changing a release again is NOT required.
        #
        # Explicit ERROR_IF_IN_REVIEW is essential. Google's default would
        # cancel an ongoing production review.
        edits.commit(
            packageName=PACKAGE,
            editId=edit_id,
            changesInReviewBehavior="ERROR_IF_IN_REVIEW",
            changesNotSentForReview=False,
        ).execute()
        committed = True
    finally:
        if not committed:
            try:
                edits.delete(packageName=PACKAGE, editId=edit_id).execute()
            except Exception:
                print("CLEANUP_WARNING: failed to discard uncommitted RivoMeasure edit", file=sys.stderr)

    # The commit succeeding is NOT proof that Google actually started review.
    # Verify the *public release lifecycle*; no retries that submit again.
    observed = "PENDING_ALPHA_13"
    for attempt in range(6):
        if attempt:
            time.sleep(6)
        observed = status(session)
        if observed != "PENDING_ALPHA_13":
            break
    return {"result": "REVIEW_SUBMITTED" if observed != "PENDING_ALPHA_13" else
            "COMMIT_ACCEPTED_BUT_REVIEW_STILL_PENDING",
            "observed": observed, "commitAttempted": True,
            "releaseChanged": False, "package": PACKAGE, "versionCode": VERSION}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Commit a no-op edit to submit saved Console changes")
    parser.add_argument("--confirm", default="", help="Must equal SEND_RIVOMEASURE_ALPHA_13")
    args = parser.parse_args(argv)
    if args.apply and args.confirm != CONFIRM:
        print("BLOCKED: explicit exact package/version review confirmation missing", file=sys.stderr)
        return 2
    try:
        from google.auth.transport.requests import AuthorizedSession
        from publish import get_credentials
        credentials = get_credentials()
        session = AuthorizedSession(credentials)
        if not args.apply:
            print(json.dumps({"package": PACKAGE, "versionCode": VERSION,
                              "result": "READ_ONLY_PREFLIGHT", "state": status(session)},
                             sort_keys=True))
            return 0
        result = submit_pending_alpha(credentials, session)
        print("RIVOMEASURE_ALPHA_RESULT " + json.dumps(result, sort_keys=True))
        return 0 if result["result"] in ("REVIEW_SUBMITTED", "ALREADY_IN_REVIEW", "ALREADY_PUBLISHED") else 2
    except Exception as error:
        http = getattr(getattr(error, "resp", None), "status", None)
        if http in (400, 409):
            print("BLOCKED: possible changes already in Google review or API precondition failed", file=sys.stderr)
        elif http in (401, 403):
            print("BLOCKED: Google Play service account credentials or permissions", file=sys.stderr)
        elif isinstance(error, ValueError):
            print("BLOCKED: " + str(error), file=sys.stderr)
        else:
            print("RIVOMEASURE_SUBMIT_ERROR " + type(error).__name__ +
                  (" HTTP " + str(http) if http else ""), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
