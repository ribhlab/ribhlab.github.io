#!/usr/bin/env python3
"""Owner-approved: publish only signed RivoScan v0.45.93 (versionCode 208) to Production.

Images, feature graphics, icon, locales, descriptions, data safety and other
tracks are NEVER written. Verify exact downloaded AAB SHA256, check Play state,
use existing uploaded bundle if already available, and do not republish if
versionCode 208 is already completed in production.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from publish import get_credentials

PACKAGE = "com.ribhlab.rivoscan"
EXPECTED_CODE = "208"
EXPECTED_SHA256 = "db2189871d37817fbc5fa3b14962c35a43631dbcb95d179cdb11390e523415be"
EXPECTED_SIZE = 83122968
IMAGE_TYPES = ("icon", "featureGraphic", "phoneScreenshots", "sevenInchScreenshots", "tenInchScreenshots")
CONFIRM = "PUBLISH_RIVOSCAN_04593_PRODUCTION_PRESERVE_ALL_IMAGES"

RELEASE = {
    "name": "RivoScan 0.45.93 — Refined interface and scanner controls",
    "status": "completed",
    "versionCodes": [EXPECTED_CODE],
    "releaseNotes": [
        {"language": "en-US", "text": "Refined home header, clearer scanner controls, improved responsive layout and document navigation."},
        {"language": "fr-FR", "text": "En-tête amélioré, commandes de numérisation plus claires et navigation adaptée aux écrans."},
        {"language": "ar", "text": "تحسين الواجهة الرئيسية وأزرار المسح والتنقل بين المستندات."}
    ],
}

def check_file(path: Path):
    if path.name != "RivoScan-0.45.93-ALL-SUPPORTED-ANDROID-PLAY.aab" or not path.is_file():
        raise ValueError("Wrong or missing original signed 0.45.93 AAB")
    if path.stat().st_size != EXPECTED_SIZE:
        raise ValueError("AAB size differs from verified GitHub release asset")
    digest = hashlib.file_digest(path.open("rb"), "sha256").hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError("AAB SHA256 does not match signed GitHub release")
    print("RIVOSCAN_04593_SIGNED_AAB_VERIFIED=" + json.dumps(
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

    edits = build("androidpublisher", "v3", credentials=get_credentials(), cache_discovery=False).edits()
    eid = edits.insert(packageName=PACKAGE, body={}).execute()["id"]
    committed = False
    try:
        tracks = edits.tracks().list(packageName=PACKAGE, editId=eid).execute().get("tracks", [])
        production = next((t for t in tracks if t.get("track") == "production"), None)
        if production is None:
            raise RuntimeError("Existing Play production track not found")
        releases = production.get("releases", [])
        print("RIVOSCAN_04593_PLAY_PRODUCTION_BEFORE=" + json.dumps([
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
        print("RIVOSCAN_04593_IMAGES_BEFORE=" + json.dumps(
            {k: len(v) for k,v in images_before.items()}), flush=True)

        if codes == [EXPECTED_CODE]:
            print("RIVOSCAN_04593_ALREADY_PRODUCTION=" + json.dumps(
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
            media = MediaFileUpload(str(args.aab), mimetype="application/octet-stream", resumable=True)
            response = edits.bundles().upload(
                packageName=PACKAGE, editId=eid, media_body=media
            ).execute()
            if str(response.get("versionCode")) != EXPECTED_CODE:
                raise RuntimeError("Uploaded AAB has unexpected version code")
            print("RIVOSCAN_04593_BUNDLE_UPLOADED=208", flush=True)
        else:
            print("RIVOSCAN_04593_BUNDLE_REUSED=208", flush=True)

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
        print("RIVOSCAN_04593_PRODUCTION_COMMITTED=" + json.dumps({
            "result": "COMMITTED", "package": PACKAGE, "versionName": "0.45.93",
            "versionCode": 208, "track": "production", "releaseStatus": "completed",
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
        print("RIVOSCAN_04593_PRODUCTION_FAILED=" + json.dumps({
            "error": type(exc).__name__, "details": str(exc)[:450],
            "httpStatus": getattr(getattr(exc, "resp", None), "status", None)
        }), file=sys.stderr, flush=True)
        sys.exit(1)
