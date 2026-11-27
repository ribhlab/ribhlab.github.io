#!/usr/bin/env python3
"""RivoNFC 0.6.2 (code 9) authorized update of exact Play tracks and official icon.

Production first: upload one original-key-signed, hash-verified AAB, replace the
single English store icon, and promote production only. Internal second:
reuse the already uploaded code 9, leaving artwork and production unchanged.
Strictly no changes to other packages or unexpected release states.
"""
import argparse
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
from PIL import Image

from publish import get_credentials

PACKAGE = "com.ribhlab.rivonfc"
OLD = "8"
NEW = "9"
VERSION_NAME = "0.6.2"
AAB_NAME = "RivoNFC-0.6.2-RivoScan-SIGNED.aab"
CONFIRM = "PUBLISH_RIVONFC_062_ORIGINAL_KEY_PROD_THEN_INTERNAL"
NOTES = [
    {"language": "en-US", "text": "A fresh NFC chip and contactless signal icon across your home screen and Google Play. Same familiar NFC tools with improved app recognition."},
    {"language": "fr-FR", "text": "Nouvelle icône NFC avec puce et ondes sans contact sur votre téléphone et Google Play. Les outils NFC habituels restent disponibles."},
    {"language": "ar", "text": "أيقونة جديدة واضحة لشريحة NFC وموجات الاتصال على الهاتف والمتجر. أدوات NFC نفسها دون تغيير."},
]
IMAGE_TYPES = ("icon", "featureGraphic", "phoneScreenshots")


def write_message(name, value):
    print(name + "=" + json.dumps(value, sort_keys=True, ensure_ascii=False), flush=True)


def verify_bundle(aab: Path):
    if not aab.is_file() or aab.name != AAB_NAME:
        raise RuntimeError("Expected exact signed RivoNFC 0.6.2 AAB")
    sha = os.environ.get("RIVONFC_062_SIGNED_SHA256", "").lower()
    size = int(os.environ.get("RIVONFC_062_SIGNED_BYTES", "0"))
    if len(sha) != 64 or size < 1000000 or any(c not in "0123456789abcdef" for c in sha):
        raise RuntimeError("Pinned signed AAB SHA-256 and byte size required")
    if aab.stat().st_size != size or hashlib.sha256(aab.read_bytes()).hexdigest() != sha:
        raise RuntimeError("Signed AAB checksum / size mismatch")
    return sha, size


def api_edits():
    transport = httplib2.Http(timeout=300)
    transport.redirect_codes = transport.redirect_codes - {308}
    return build("androidpublisher", "v3", http=AuthorizedHttp(get_credentials(),http=transport),
                 cache_discovery=False).edits()


def sole_release(tracks, name, expected_code):
    tr = next((t for t in tracks if t.get("track") == name), None)
    if not tr or len(tr.get("releases") or []) != 1:
        raise RuntimeError(f"{name} must contain exactly one release; refuse to overwrite drafts or staggered releases")
    rel = tr["releases"][0]
    if rel.get("status") != "completed" or list(map(str, rel.get("versionCodes") or [])) != [expected_code]:
        raise RuntimeError(f"{name} release is not completed code {expected_code}: " + str(rel)[:300])
    return rel


def other_tracks_safe(tracks):
    for t in tracks:
        if t.get("track") not in ("production", "internal"):
            if any(int(code) > int(NEW) for rel in t.get("releases",[])
                   for code in (rel.get("versionCodes") or [])):
                raise RuntimeError("Unexpected newer app bundle in an unrelated track")


def media_snapshot(edits, kw):
    return {kind: [str(i.get("id")) for i in
        edits.images().list(**kw, language="en-US", imageType=kind).execute().get("images",[])]
        for kind in IMAGE_TYPES}


def make_release(before, phase):
    release = {
        "name": f"RivoNFC {VERSION_NAME} — New NFC Icon" + (" Internal" if phase == "internal" else ""),
        "versionCodes": [NEW], "status": "completed", "releaseNotes": NOTES
    }
    # Preserve the scope and priority of the previously authorized track.
    for key in ("countryTargeting", "inAppUpdatePriority"):
        if key in before:
            release[key] = before[key]
    return release


def update_production(edits, kw, aab: Path):
    sha, size = verify_bundle(aab)
    bundles = {str(x.get("versionCode")) for x in edits.bundles().list(**kw).execute().get("bundles",[])}
    tracks = edits.tracks().list(**kw).execute().get("tracks",[])
    other_tracks_safe(tracks)
    prod = sole_release(tracks, "production", OLD)
    sole_release(tracks, "internal", OLD)
    if bundles != {OLD}:
        raise RuntimeError(f"Expected only the earlier uploaded code {OLD}; got {bundles}")
    country = edits.countryavailability().get(**kw, track="production").execute()
    if not country.get("restOfWorld") and not country.get("countries"):
        raise RuntimeError("No Production countries enabled")
    before = media_snapshot(edits, kw)
    if not (len(before["icon"]) == 1 and len(before["featureGraphic"]) == 1
            and len(before["phoneScreenshots"]) >= 2):
        raise RuntimeError("Expected existing Play icon, feature graphic and real screenshots")
    listings = edits.listings().list(**kw).execute().get("listings",[])
    if not any(z.get("language")=="en-US" and "RivoNFC" in z.get("title","") for z in listings):
        raise RuntimeError("RivoNFC store listing missing")
    icon_path = Path("tools/play-publisher/rivonfc-062-store-icon.png")
    with Image.open(icon_path) as im:
        if im.size != (512,512) or im.format != "PNG":
            raise RuntimeError("Play icon must be PNG at 512x512")
    write_message("RIVONFC_062_PREFLIGHT", {
        "oldProductionCode": OLD,"oldInternalCode": OLD, "newVersionCode": NEW,
        "signedAabSha256":sha,"signedAabBytes":size,
        "oldIconCount":len(before["icon"]),"realScreens":len(before["phoneScreenshots"])
    })
    # All changes belong to the single new edit until validated+committed.
    upload = edits.bundles().upload(**kw, media_body=MediaFileUpload(
        str(aab), mimetype="application/octet-stream", resumable=True,
        chunksize=8*1024*1024))
    result = None
    while result is None:
        progress,result=upload.next_chunk(num_retries=4)
        if progress:print("RIVONFC_062_AAB_UPLOAD_PROGRESS="+str(round(progress.progress()*100))+"%",flush=True)
    if str(result.get("versionCode")) != NEW:
        raise RuntimeError("Play returned unexpected uploaded versionCode")
    edits.images().deleteall(**kw, language="en-US", imageType="icon").execute()
    edits.images().upload(**kw, language="en-US", imageType="icon",
        media_body=MediaFileUpload(str(icon_path),mimetype="image/png")).execute()
    after=media_snapshot(edits, kw)
    if (len(after["icon"]) != 1 or before["featureGraphic"] != after["featureGraphic"]
            or before["phoneScreenshots"] != after["phoneScreenshots"]):
        raise RuntimeError("New single store icon or screenshot preservation failed")
    edits.tracks().update(**kw,track="production",body={
        "track":"production","releases":[make_release(prod,"production")]
    }).execute()
    edits.validate(**kw).execute()
    edits.commit(**kw).execute()
    write_message("RIVONFC_062_PRODUCTION_COMMITTED",{
        "package":PACKAGE,"versionCode":9,"track":"production","status":"completed",
        "signedAabSHA256":sha,"bytes":size,"newIcon":True,
        "otherTracksUnchanged":True,"realScreensPreserved":True,
        "googleReviewMayStillBeRequired":True
    })


def update_internal(edits, kw):
    bundles = {str(x.get("versionCode")) for x in edits.bundles().list(**kw).execute().get("bundles",[])}
    if NEW not in bundles:
        raise RuntimeError("Code 9 not uploaded to Play; cannot update Internal")
    tracks=edits.tracks().list(**kw).execute().get("tracks",[])
    other_tracks_safe(tracks)
    sole_release(tracks,"production",NEW)
    internal = sole_release(tracks,"internal",OLD)
    snapshot = media_snapshot(edits,kw)
    if (len(snapshot["icon"])!=1 or len(snapshot["featureGraphic"])!=1
            or len(snapshot["phoneScreenshots"])<2):
        raise RuntimeError("Store artwork missing")
    edits.tracks().update(**kw,track="internal",body={
        "track":"internal","releases":[make_release(internal,"internal")]
    }).execute()
    if media_snapshot(edits,kw) != snapshot:raise RuntimeError("Unexpected store media changes")
    edits.validate(**kw).execute()
    edits.commit(**kw).execute()
    write_message("RIVONFC_062_INTERNAL_COMMITTED",{
        "package":PACKAGE,"versionCode":9,"track":"internal","status":"completed",
        "productionPreserved":True,"storeArtworkPreserved":True,
        "testersMustOptIn":True
    })


def run():
    arg=argparse.ArgumentParser()
    arg.add_argument("--phase",choices=("production","internal"),required=True)
    arg.add_argument("--aab",type=Path)
    args=arg.parse_args()
    if os.environ.get("RIVONFC_062_APPROVAL")!=CONFIRM:
        raise RuntimeError("Exact release authorization missing")
    if args.phase=="production" and not args.aab:
        raise RuntimeError("AAB required for production")
    edits=api_edits()
    eid=edits.insert(packageName=PACKAGE,body={}).execute()["id"]
    kw={"packageName":PACKAGE,"editId":eid}
    try:
        if args.phase=="production":update_production(edits,kw,args.aab)
        else:update_internal(edits,kw)
    except Exception:
        try:edits.delete(**kw).execute()
        except Exception:print("RIVONFC_062_EDIT_CLEANUP_WARNING",file=sys.stderr)
        raise

if __name__=="__main__":
    try:run()
    except HttpError as exc:
        try:
            detail=json.loads(exc.content.decode("utf-8")).get("error",{}).get("message","")
        except Exception:detail=str(exc)
        write_message("RIVONFC_062_PLAY_API_ERROR",{
            "status":int(exc.resp.status),"detail":detail[:550],
            "committedByThisAttempt":False})
        sys.exit(2)
    except Exception as exc:
        write_message("RIVONFC_062_RELEASE_BLOCKED",{"type":type(exc).__name__,"reason":str(exc)[:550]})
        sys.exit(1)
