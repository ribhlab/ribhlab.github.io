#!/usr/bin/env python3
"""Stage exact signed RivoCaption v0.4.4 (code 18) in Play bundle library ONLY.

Does not change Production, Internal, alpha/beta releases, listings, graphics,
Ads/Data safety declarations, or other applications. No user rollout. Uses
the same authorized original Google Play publisher and service account.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

import httplib2
from google_auth_httplib2 import AuthorizedHttp
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from publish import get_credentials

PACKAGE = "com.rivocaption.editor"
CODE = "18"
AAB = Path("rivocaption-signed/RivoCaption-0.4.4-RivoScan-SIGNED.aab")
APPROVAL = "RIVOCAPTION_044_LIBRARY_ONLY_WITHOUT_ANY_TRACK_CHANGES"


def log(label: str, data: dict) -> None:
    print(label + "=" + json.dumps(data, sort_keys=True, ensure_ascii=False), flush=True)


def tracks_snapshot(tracks: list[dict]) -> dict:
    return {
        t.get("track"): [
            {
                "status": release.get("status"),
                "versionCodes": [str(v) for v in release.get("versionCodes", [])],
                "name": release.get("name"),
            }
            for release in t.get("releases", [])
        ]
        for t in tracks
    }


def run() -> None:
    if os.environ.get("RIVOCAPTION_044_STAGE_CONFIRM") != APPROVAL:
        raise RuntimeError("Exact RivoCaption code18 stage-only authorization missing")
    if not AAB.is_file() or AAB.stat().st_size < 1_000_000:
        raise RuntimeError("Signed original RivoCaption v0.4.4 AAB not present")
    digest = hashlib.file_digest(AAB.open("rb"), "sha256").hexdigest()
    if len(digest) != 64:
        raise RuntimeError("Cannot verify signed app hash")
    http = httplib2.Http(timeout=280)
    http.redirect_codes = http.redirect_codes - {308}
    edits = build("androidpublisher", "v3",
                  http=AuthorizedHttp(get_credentials(), http=http),
                  cache_discovery=False).edits()
    edit_id = edits.insert(packageName=PACKAGE, body={}).execute()["id"]
    kw = dict(packageName=PACKAGE, editId=edit_id)
    committed = False
    try:
        before = tracks_snapshot(edits.tracks().list(**kw).execute().get("tracks", []))
        prod = before.get("production", [])
        # Prior read-only audit showed published code8 and code17 draft.
        # Refuse an unexpected release, while never touching any track.
        prod_codes = {v for release in prod for v in release["versionCodes"]}
        if not prod or not ({"8", "17"} & prod_codes):
            raise RuntimeError("RivoCaption Production no longer matches verified old/draft state")
        if any(int(v) >= 18 for v in prod_codes):
            raise RuntimeError("Production code18 or higher already exists; refusing duplicate stage")
        for track, releases in before.items():
            for release in releases:
                if any(int(v) > 18 for v in release["versionCodes"]):
                    raise RuntimeError("Newer RivoCaption track version detected; refusing obsolete update")
        bundles = {
            str(b["versionCode"])
            for b in edits.bundles().list(**kw).execute().get("bundles", [])
        }
        if any(int(v) > 18 for v in bundles):
            raise RuntimeError("Newer RivoCaption bundle exists; version 18 is no longer latest")
        english = edits.listings().get(**kw, language="en-US").execute()
        if "rivocaption" not in english.get("title", "").casefold():
            raise RuntimeError("Wrong app listing returned; refusing commit")
        log("RIVOCAPTION_08_STAGE_PREFLIGHT", {
            "package": PACKAGE, "code": int(CODE), "production": prod,
            "bundles": sorted(bundles), "sha256": digest, "bytes": AAB.stat().st_size,
            "trackChangesAllowed": False,
        })
        if CODE not in bundles:
            request = edits.bundles().upload(
                **kw, media_body=MediaFileUpload(
                    str(AAB), mimetype="application/octet-stream",
                    chunksize=8 * 1024 * 1024, resumable=True,
                )
            )
            result = None
            while result is None:
                progress, result = request.next_chunk(num_retries=3)
                if progress is not None:
                    print("RIVOCAPTION_08_UPLOAD_PROGRESS=" + str(round(progress.progress() * 100)), flush=True)
            if str(result.get("versionCode")) != CODE:
                raise RuntimeError("Play returned unexpected bundle version")
        after = tracks_snapshot(edits.tracks().list(**kw).execute().get("tracks", []))
        if before != after:
            raise RuntimeError("Unexpected track change; refusing commit")
        edits.validate(**kw).execute()
        edits.commit(**kw, changesInReviewBehavior="ERROR_IF_IN_REVIEW").execute()
        committed = True
        log("RIVOCAPTION_08_STAGE_COMMITTED", {
            "package": PACKAGE, "versionCode": int(CODE),
            "bundleSha256": digest, "uploadedToBundleLibrary": True,
            "productionUnchanged": True, "allTracksUnchanged": True,
            "foregroundServiceAndDataSafetyDeclarationNeedsConsoleVerification": True,
        })
    finally:
        if not committed:
            try:
                edits.delete(**kw).execute()
            except Exception:
                print("RIVOCAPTION_08_STAGE_UNCOMMITTED_EDIT_CLEANUP_FAILED", file=sys.stderr)


if __name__ == "__main__":
    try:
        run()
    except HttpError as exc:
        try:
            reason = json.loads(exc.content.decode()).get("error", {}).get("message", "")
        except Exception:
            reason = type(exc).__name__
        log("RIVOCAPTION_08_STAGE_PLAY_ERROR", {
            "httpStatus": int(exc.resp.status), "reason": reason[:400],
        })
        sys.exit(2)
    except Exception as exc:
        log("RIVOCAPTION_08_STAGE_BLOCKED", {
            "error": type(exc).__name__, "reason": str(exc)[:400],
        })
        sys.exit(1)
