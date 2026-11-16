#!/usr/bin/env python3
"""Deploy the signed RivoScan 0.45.40 AAB through the existing Play publisher.

Preserve *all* Play Store text, graphics, screenshots and icons. First commit
versionCode 144 to an existing completed testing track; then promote to
Production in a separate validated Play edit. Only an explicit owner-approved
--apply flag changes Play state. Never touch unrelated application IDs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

APP = "com.ribhlab.rivoscan"
VERSION = 144
VERSION_NAME = "0.45.40"
ASSET = "RivoScan-0.45.40-GooglePlay.aab"
URL = ("https://github.com/univcours/ribhlab/releases/download/"
       "rivoscan-0.45.40-original-key/" + ASSET)
EXPECTED_SHA256 = "893957e3e9e86d6ac5a365541ce3b441c22d1d22ee70cf8bd00e71c0ea1fef64"
CERT = "E9:B3:E2:77:95:75:BA:08:A9:13:72:FC:38:85:EB:A0:1D:D3:E7:3E"
CONFIRM = "PUBLISH_SIGNED_RIVOSCAN_144_PRODUCTION"
TEST_TRACKS = ("alpha", "beta", "qa", "internal")
NOTES = [
    {"language": "en-US", "text": "Larger 6x document-corner magnifier, fixed above the image and positioned away from your finger in PerfectScan and saved-document edge editing."},
    {"language": "fr-FR", "text": "Loupe x6 plus grande, toujours au-dessus du document et éloignée du doigt pour ajuster les coins dans PerfectScan et les fichiers enregistrés."},
    {"language": "ar", "text": "عدسة تكبير ×6 أكبر وثابتة أعلى الصورة وبعيدة عن الإصبع لضبط زوايا المستند في PerfectScan والملفات المحفوظة."},
]


def report(event, **values):
    print("RIVOSCAN_04540_" + event + "=" +
          json.dumps(values, sort_keys=True, ensure_ascii=False), flush=True)


def verify_bundle(folder: Path):
    path = folder / ASSET
    request = urllib.request.Request(
        URL, headers={"User-Agent": "RivoScan-original-key-GooglePlay-Publisher/0.45.40"})
    with urllib.request.urlopen(request, timeout=180) as response, path.open("wb") as out:
        size = 0
        while True:
            chunk = response.read(131072)
            if not chunk:
                break
            size += len(chunk)
            if size > 110_000_000:
                raise RuntimeError("AAB exceeds size cap")
            out.write(chunk)
    if path.stat().st_size != 47_721_295:
        raise RuntimeError("Unexpected RivoScan 0.45.40 AAB byte size")
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    if sha != EXPECTED_SHA256:
        raise RuntimeError("Signed AAB SHA256 mismatch — refusing to upload")
    with zipfile.ZipFile(path) as archive:
        if "base/manifest/AndroidManifest.xml" not in archive.namelist() or archive.testzip():
            raise RuntimeError("Invalid or corrupt Android AAB archive")
    cert = subprocess.run(["keytool", "-printcert", "-jarfile", str(path)],
                          capture_output=True, text=True, check=True)
    if ("SHA1: " + CERT) not in (cert.stdout + cert.stderr):
        raise RuntimeError("AAB is not signed with original RivoScan Google Play upload key")
    signed = subprocess.run(["jarsigner", "-verify", str(path)],
                            capture_output=True, text=True, check=True)
    if "jar verified" not in (signed.stdout + signed.stderr):
        raise RuntimeError("AAB signature check failed")
    report("BUNDLE_VERIFIED", asset=ASSET, bytes=path.stat().st_size,
           sha256=sha, uploadCertificateVerified=True, versionCode=VERSION)
    return path


def get_edits():
    from googleapiclient.discovery import build
    from publish import get_credentials
    return build("androidpublisher", "v3", credentials=get_credentials(),
                 cache_discovery=False).edits()


def production_version(tracks):
    found = [x for x in tracks if x.get("track") == "production"]
    if len(found) != 1 or len(found[0].get("releases", [])) != 1:
        raise RuntimeError("Production is not a single existing release; review in Play Console")
    record = found[0]["releases"][0]
    codes = [int(x) for x in record.get("versionCodes", [])]
    if record.get("status") != "completed" or len(codes) != 1:
        raise RuntimeError("Production is staged, halted, draft or multi-AAB: stop")
    code = codes[0]
    if code > VERSION:
        raise RuntimeError(f"Production serves newer versionCode {code}; refusing downgrade")
    return code


def inventory_check(edits, eid):
    stored = edits.bundles().list(packageName=APP, editId=eid).execute().get("bundles", [])
    matching = [b for b in stored if int(b.get("versionCode", 0)) == VERSION]
    if len(matching) > 1:
        raise RuntimeError("Duplicate bundle inventory")
    if matching:
        sha = str(matching[0].get("sha256") or "").replace("sha256:", "").lower()
        if sha and sha != EXPECTED_SHA256:
            raise RuntimeError("A different AAB already occupies versionCode 144")
    return bool(matching)


def complete_tracks_only(edits, eid):
    return edits.tracks().list(packageName=APP, editId=eid).execute().get("tracks", [])


def choose_test_track(tracks):
    options = []
    for index, name in enumerate(TEST_TRACKS):
        record = next((t for t in tracks if t.get("track") == name), None)
        if record is None:
            continue
        releases = record.get("releases", [])
        if len(releases) == 1 and releases[0].get("status") == "completed" and len(releases[0].get("versionCodes", [])) == 1:
            options.append((index, name, int(releases[0]["versionCodes"][0])))
    if not options:
        raise RuntimeError("No existing completed single-version testing track; no Production changed")
    options.sort()
    return options[0][1], options[0][2]


def cleanup(edits, eid):
    try:
        edits.delete(packageName=APP, editId=eid).execute()
    except Exception:
        report("CLEANUP_WARNING", editId=eid)


def stage_test(edits, aab: Path):
    from googleapiclient.http import MediaFileUpload
    eid = edits.insert(packageName=APP, body={}).execute()["id"]
    committed = False
    try:
        tracks = complete_tracks_only(edits, eid)
        prod = production_version(tracks)
        higher = [int(v) for t in tracks for r in t.get("releases", [])
                  for v in r.get("versionCodes", []) if int(v) > VERSION]
        if higher:
            raise RuntimeError("A newer version exists on Google Play; abort")
        if prod == VERSION:
            report("ALREADY_PUBLISHED", productionVersionCode=prod)
            return prod, None
        target, old = choose_test_track(tracks)
        report("PRECHECK", productionVersionCode=prod, testTrack=target, previousTestCode=old)
        if old > VERSION:
            raise RuntimeError("Test track already contains newer versionCode")
        if old == VERSION:
            report("TEST_ALREADY_COMPLETED", versionCode=VERSION, track=target)
            return prod, target
        if not inventory_check(edits, eid):
            uploaded = edits.bundles().upload(
                packageName=APP, editId=eid,
                media_body=MediaFileUpload(str(aab), mimetype="application/octet-stream",
                                          resumable=True)).execute(num_retries=2)
            if int(uploaded.get("versionCode", 0)) != VERSION:
                raise RuntimeError("Google Play returned an unexpected AAB versionCode")
            report("SIGNED_AAB_UPLOADED", versionCode=VERSION, testingTrack=target)
        edits.tracks().update(packageName=APP, editId=eid, track=target,
            body={"track": target, "releases": [{
                "name": "RivoScan " + VERSION_NAME,
                "status": "completed", "versionCodes": [str(VERSION)],
                "releaseNotes": NOTES
            }]}).execute()
        edits.validate(packageName=APP, editId=eid).execute()
        edits.commit(packageName=APP, editId=eid).execute()
        committed = True
        report("TEST_TRACK_COMMITTED", versionCode=VERSION, track=target,
               productionUntouched=True)
        return prod, target
    finally:
        if not committed:
            cleanup(edits, eid)


def publish_production(edits, initial_prod, test_track):
    eid = edits.insert(packageName=APP, body={}).execute()["id"]
    committed = False
    try:
        tracks = complete_tracks_only(edits, eid)
        current = production_version(tracks)
        if current == VERSION:
            report("PRODUCTION_ALREADY_COMPLETE", versionCode=VERSION)
            return
        if current != initial_prod:
            raise RuntimeError("Production changed concurrently; refusing to overwrite")
        tests = [r for t in tracks if t.get("track") == test_track
                 for r in t.get("releases", [])
                 if r.get("status") == "completed"
                 and str(VERSION) in [str(v) for v in r.get("versionCodes", [])]]
        if not tests:
            raise RuntimeError("Signed 144 must be completed in a test track first")
        edits.tracks().update(packageName=APP, editId=eid, track="production",
            body={"track": "production", "releases": [{
                "name": "RivoScan " + VERSION_NAME + " — Top Magnifier",
                "status": "completed", "versionCodes": [str(VERSION)],
                "releaseNotes": NOTES
            }]}).execute()
        edits.validate(packageName=APP, editId=eid).execute()
        edits.commit(packageName=APP, editId=eid).execute()
        committed = True
        report("PRODUCTION_COMMITTED", versionCode=VERSION, versionName=VERSION_NAME,
               previousCode=initial_prod, status="completed", track="production",
               featureGraphicUnchanged=True, appIconUnchanged=True,
               screenshotsUnchanged=True, listingTextUnchanged=True,
               reviewMayBeRequired=True)
    finally:
        if not committed:
            cleanup(edits, eid)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm", default="")
    args = parser.parse_args()
    if args.apply and args.confirm != CONFIRM:
        raise ValueError("Explicit owner confirmation is required")
    with tempfile.TemporaryDirectory() as temp:
        aab = verify_bundle(Path(temp))
        if not args.apply:
            report("DRY_RUN_OK", package=APP, versionCode=VERSION,
                   productionAndListingUnchanged=True)
            return
        edits = get_edits()
        prev, test = stage_test(edits, aab)
        if test is not None:
            publish_production(edits, prev, test)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        report("ERROR", type=type(exc).__name__,
               message=str(exc)[:300],
               httpStatus=getattr(getattr(exc, "resp", None), "status", None))
        sys.exit(1)
