#!/usr/bin/env python3
"""Owner-approved: publish only signed RivoScan v0.45.95 (versionCode 210) to Production.

Images, feature graphics, icon, locales, descriptions, data safety and other
tracks are NEVER written. Verify exact downloaded AAB SHA256, check Play state,
use existing uploaded bundle if already available, and do not republish if
versionCode 210 is already completed in production.
"""
import argparse
import os
import hashlib
import json
import sys
from pathlib import Path
from googleapiclient.discovery import build
from google_auth_httplib2 import AuthorizedHttp
import httplib2
from googleapiclient.http import MediaFileUpload
from publish import get_credentials

PACKAGE = "com.ribhlab.rivoscan"
EXPECTED_CODE = "210"
EXPECTED_SHA256 = os.environ.get("RIVO_EXPECTED_SHA256","")
EXPECTED_SIZE = int(os.environ.get("RIVO_EXPECTED_SIZE","0"))
IMAGE_TYPES = ("icon", "featureGraphic", "phoneScreenshots", "sevenInchScreenshots", "tenInchScreenshots")
CONFIRM = "PUBLISH_RIVOSCAN_04595_PRODUCTION_PRESERVE_ALL_IMAGES"

RELEASE = {
    "name": "RivoScan 0.45.95 — Banner ID fix",
    "status": "completed",
    "versionCodes": [EXPECTED_CODE],
    "releaseNotes": [
        {"language": "en-US", "text": "Corrected banner ad unit configuration and retained safe retry handling."},
        {"language": "fr-FR", "text": "Correction de la configuration des annonces bannière et conservation des relances sécurisées."},
        {"language": "ar", "text": "تصحيح إعدادات الوحدة الإعلانية للبانر وتحسين استقرار إعادة المحاولة."}
    ],
}

def check_file(path: Path):
    if len(EXPECTED_SHA256)!=64 or EXPECTED_SIZE<=0:raise ValueError('Missing verified release digest and size')
    if path.name != "RivoScan-0.45.95-ALL-SUPPORTED-ANDROID-PLAY.aab" or not path.is_file():
        raise ValueError("Wrong or missing original signed 0.45.95 AAB")
    if path.stat().st_size != EXPECTED_SIZE:
        raise ValueError("AAB size differs from verified GitHub release asset")
    digest = hashlib.file_digest(path.open("rb"), "sha256").hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError("AAB SHA256 does not match signed GitHub release")
    print("RIVOSCAN_04595_SIGNED_AAB_VERIFIED=" + json.dumps(
        {"name": path.name, "size": EXPECTED_SIZE, "sha256": digest}), flush=True)

def media_snapshot(edits, eid):
    # Keep an audit of the five current en-US image slots, without modifying them.
    result = {}
    for kind in IMAGE_TYPES:
        items = edits.images().list(
            packageName=PACKAGE, editId=eid, language="en-US", imageType=kind
        ).execute().get("images", [])
        result[kind] = [str(item.get("id")) for item in items]
    return result

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--aab", type=Path, required=True)
    p.add_argument("--confirm", required=True)
    args = p.parse_args()
    if args.confirm != CONFIRM:
        raise ValueError("Explicit approval required")
    check_file(args.aab)

    transport = httplib2.Http(timeout=300)
    # Google resumable uploads return HTTP 308 Resume Incomplete, not an HTTP redirect.
    transport.redirect_codes = transport.redirect_codes - {308}
    edits = build("androidpublisher", "v3", http=AuthorizedHttp(get_credentials(), http=transport), cache_discovery=False).edits()
    eid = edits.insert(packageName=PACKAGE, body={}).execute()["id"]
    committed = False
    try:
        tracks = edits.tracks().list(packageName=PACKAGE, editId=eid).execute().get("tracks", [])
        production = next((t for t in tracks if t.get("track") == "production"), None)
        if production is None:
            raise RuntimeError("Existing Play production track not found")
        releases = production.get("releases", [])
        print("RIVOSCAN_04595_PLAY_PRODUCTION_BEFORE=" + json.dumps([
            {"name": r.get("name"), "versionCodes": r.get("versionCodes"),
             "status": r.get("status")} for r in releases]), flush=True)
        if any(r.get("status") != "completed" for r in releases):
            raise RuntimeError("Production contains draft/staged/halted release; no automatic overwrite")
        if any(len(r.get("versionCodes", [])) != 1 for r in releases):
            raise RuntimeError("Production has multi-APK setup; require manual review")
        if len(releases) > 1:
            raise RuntimeError("Multiple current production releases; cannot safely replace")
        codes = [str(c) for r in releases for c in r.get("versionCodes", [])]
        images_before = media_snapshot(edits, eid)
        print("RIVOSCAN_04595_IMAGES_BEFORE=" + json.dumps(
            {k: len(v) for k,v in images_before.items()}), flush=True)

        if codes == [EXPECTED_CODE]:
            print("RIVOSCAN_04595_ALREADY_PRODUCTION=" + json.dumps(
                {"versionCode": EXPECTED_CODE, "status": "completed",
                 "imagesChanged": False, "appBundleUploaded": False}), flush=True)
            return

        all_codes=[int(c) for t in tracks for release in t.get('releases',[]) for c in release.get('versionCodes',[])]
        if any(c > int(EXPECTED_CODE) for c in all_codes):
            raise RuntimeError("A newer production version exists; cannot downgrade")
        if not codes:
            raise RuntimeError("Production track is empty; require additional verification")

        bundles = edits.bundles().list(packageName=PACKAGE, editId=eid).execute().get("bundles", [])
        existing = next((b for b in bundles if str(b.get("versionCode")) == EXPECTED_CODE), None)
        if existing and existing.get("sha256", "").lower() != EXPECTED_SHA256:
            raise RuntimeError("Existing Play bundle has different hash; abort")
        bundle_present = existing is not None
        if not bundle_present:
            media = MediaFileUpload(str(args.aab), mimetype="application/octet-stream", resumable=True, chunksize=8*1024*1024)
            request = edits.bundles().upload(packageName=PACKAGE, editId=eid, media_body=media)
            response = None
            while response is None:
                progress, response = request.next_chunk(num_retries=5)
                if progress:print(f'RIVOSCAN_UPLOAD_PROGRESS={progress.progress():.0%}',flush=True)
            if str(response.get("versionCode")) != EXPECTED_CODE:
                raise RuntimeError("Uploaded AAB has unexpected version code")
            print("RIVOSCAN_04595_BUNDLE_UPLOADED=210", flush=True)
        else:
            print("RIVOSCAN_04595_BUNDLE_REUSED=210", flush=True)

        # ONLY write the production track. All Play Store images and listings are untouched.
        edits.tracks().update(
            packageName=PACKAGE, editId=eid, track="production",
            body={"track": "production", "releases": [RELEASE]}
        ).execute()
        images_after = media_snapshot(edits, eid)
        if images_before != images_after:
            raise RuntimeError("Image IDs unexpectedly changed within Play edit; abort")

        edits.validate(packageName=PACKAGE, editId=eid).execute()
        edits.commit(packageName=PACKAGE, editId=eid).execute()
        committed = True
        print("RIVOSCAN_04595_PRODUCTION_COMMITTED=" + json.dumps({
            "result": "COMMITTED", "package": PACKAGE, "versionName": "0.45.95",
            "versionCode": 210, "track": "production", "releaseStatus": "completed",
            "sameImagesVerified": images_before == images_after,
            "imageCounts": {k:len(v) for k,v in images_after.items()},
            "imagesChanged": False, "featureGraphicChanged": False,
            "iconChanged": False, "listingChanged": False,
            "otherTracksChanged": False, "reviewMayBeRequired": True
        }), flush=True)
    finally:
        if not committed:
            try:
                edits.delete(packageName=PACKAGE, editId=eid).execute()
            except Exception:
                pass

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("RIVOSCAN_04595_PRODUCTION_FAILED=" + json.dumps({
            "error": type(exc).__name__, "details": str(exc)[:450],
            "httpStatus": getattr(getattr(exc, "resp", None), "status", None)
        }), file=sys.stderr, flush=True)
        sys.exit(1)
