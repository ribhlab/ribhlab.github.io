#!/usr/bin/env python3
"""Publish ONLY RivoSticker 1.0.4 / versionCode 5 using a verified RivoScan-key AAB.

Existing Play screenshots, icon, listings, Data Safety, and unrelated tracks are
read-only. Never overwrite draft, halted, staged, or newer releases.
"""
import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
import httplib2
from google_auth_httplib2 import AuthorizedHttp
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from publish import get_credentials

PACKAGE = "com.ribhlab.rivosticker"
CODE = "5"
OLD_CODE = "4"
CONFIRM = "PUBLISH_RIVOSTICKER_104_PRODUCTION_ORIGINAL_RIVOSCAN_KEY"
IMAGE_TYPES = ("icon", "featureGraphic", "phoneScreenshots", "sevenInchScreenshots", "tenInchScreenshots")
RELEASE = {
    "name": "RivoSticker 1.0.4 — Cartoon Studio",
    "status": "completed",
    "versionCodes": [CODE],
    "releaseNotes": [
        {"language":"en-US","text":"New offline cartoon effects (Comic, Anime, Poster, Sketch), colorful caption styles, and fixes for one-tap background removal, draggable text and crop."},
        {"language":"fr-FR","text":"Nouveaux effets cartoon hors ligne, styles de légendes colorés et corrections du détourage, du texte et du recadrage."},
        {"language":"ar","text":"تأثيرات كرتونية جديدة بدون إنترنت، أنماط وألوان للنصوص، وتحسين إزالة الخلفية وتثبيت النص والقص."}
    ]
}

def verify_input(path: Path) -> tuple[str, int]:
    expected_hash = os.environ.get("RIVOSTICKER_SIGNED_SHA256", "").lower()
    expected_size = int(os.environ.get("RIVOSTICKER_SIGNED_SIZE", "0"))
    if path.name != "RivoSticker-1.0.4-RivoScan-SIGNED.aab":
        raise ValueError("Refusing unknown signed bundle filename")
    if not path.is_file() or not re.fullmatch(r"[a-f0-9]{64}", expected_hash) or expected_size <= 0:
        raise ValueError("Missing signed file or pinned SHA-256/size from verified release")
    if path.stat().st_size != expected_size:
        raise ValueError("Signed bundle size mismatch")
    with path.open("rb") as stream:
        actual = hashlib.file_digest(stream, "sha256").hexdigest()
    if actual != expected_hash:
        raise ValueError("Signed bundle SHA-256 mismatch")
    return actual, expected_size

def image_snapshot(edits, edit_id: str) -> dict:
    return {
        kind: [
            str(image.get("id"))
            for image in edits.images().list(
                packageName=PACKAGE, editId=edit_id,
                language="en-US", imageType=kind
            ).execute().get("images", [])
        ]
        for kind in IMAGE_TYPES
    }

def publish(aab: Path):
    digest, size = verify_input(aab)
    transport = httplib2.Http(timeout=300)
    transport.redirect_codes = transport.redirect_codes - {308}
    edits = build("androidpublisher", "v3",
        http=AuthorizedHttp(get_credentials(), http=transport),
        cache_discovery=False).edits()
    edit_id = edits.insert(packageName=PACKAGE, body={}).execute()["id"]
    kw = {"packageName": PACKAGE, "editId": edit_id}
    committed = False
    try:
        tracks = edits.tracks().list(**kw).execute().get("tracks", [])
        production = next((x for x in tracks if x.get("track") == "production"), None)
        if production is None:
            raise RuntimeError("Production track missing; cancel publication")
        releases = production.get("releases", [])
        if len(releases) != 1 or releases[0].get("status") != "completed":
            raise RuntimeError("Expected one completed production release; do not overwrite drafts/staged releases")
        current = list(map(str, releases[0].get("versionCodes", [])))
        if current == [CODE]:
            print("RIVOSTICKER_104_ALREADY_COMPLETED=" +
                json.dumps({"package": PACKAGE,"versionCode":5,"status":"completed","changes":False}), flush=True)
            return
        if current != [OLD_CODE]:
            raise RuntimeError("Production version is not v4; do not overwrite: " + str(current))
        listed = edits.countryavailability().get(**kw, track="production").execute()
        if not listed.get("countries") and not listed.get("restOfWorld", False):
            raise RuntimeError("No production countries configured")
        existing_codes = [
            int(code) for track in tracks for release in track.get("releases",[])
            for code in release.get("versionCodes",[])
        ]
        if any(code > int(CODE) for code in existing_codes):
            raise RuntimeError("A newer version already exists")
        bundles = edits.bundles().list(**kw).execute().get("bundles", [])
        if any(str(bundle.get("versionCode")) == CODE for bundle in bundles):
            raise RuntimeError("VersionCode 5 already uploaded, require explicit existing-bundle audit")
        before = image_snapshot(edits, edit_id)
        if len(before["icon"]) != 1 or len(before["featureGraphic"]) != 1 or len(before["phoneScreenshots"]) < 2:
            raise RuntimeError("Current Play imagery incomplete; refusing automatic release")
        media = MediaFileUpload(str(aab), mimetype="application/octet-stream",
            resumable=True, chunksize=8 * 1024 * 1024)
        upload = edits.bundles().upload(**kw, media_body=media)
        response = None
        while response is None:
            progress, response = upload.next_chunk(num_retries=4)
            if progress:
                print("RIVOSTICKER_104_UPLOAD_PROGRESS=" + str(round(progress.progress() * 100)) + "%", flush=True)
        if str(response.get("versionCode")) != CODE:
            raise RuntimeError("Unexpected versionCode in uploaded bundle")
        edits.tracks().update(**kw, track="production",
            body={"track":"production","releases":[RELEASE]}).execute()
        after = image_snapshot(edits, edit_id)
        if before != after:
            raise RuntimeError("Play artwork changed unexpectedly; abort")
        edits.validate(**kw).execute()
        edits.commit(**kw).execute()
        committed = True
        print("RIVOSTICKER_104_PRODUCTION_COMMITTED=" + json.dumps({
            "package": PACKAGE, "versionCode": 5, "versionName": "1.0.4",
            "status": "completed", "signedAabSHA256": digest,
            "signedAabBytes": size, "artworkPreserved": True,
            "listingPreserved": True, "otherTracksPreserved": True,
            "googleReviewMayStillBeRequired": True
        }, sort_keys=True), flush=True)
    finally:
        if not committed:
            try:
                edits.delete(**kw).execute()
            except Exception:
                print("WARNING: could not discard temporary edit", file=sys.stderr)

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--aab", type=Path, required=True)
    p.add_argument("--confirm", required=True)
    args = p.parse_args()
    if args.confirm != CONFIRM:
        raise ValueError("Exact RivoSticker 1.0.4 production authorization required")
    try:
        publish(args.aab)
    except Exception as exc:
        print("RIVOSTICKER_104_PUBLISH_FAILED=" +
            json.dumps({"reason":type(exc).__name__,"detail":str(exc)[:450]}),
            file=sys.stderr, flush=True)
        sys.exit(1)
