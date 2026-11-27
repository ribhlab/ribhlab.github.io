#!/usr/bin/env python3
"""Publish ONLY verified signed RivoSticker 1.0.5 code 6 and its new icon.

Never touch other apps, testing tracks, feature graphics or screenshots.
Explicitly submit the updated version for Google Play review.
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

PACKAGE="com.ribhlab.rivosticker"
CODE="6"
OLD_CODE="5"
EXPECTED_CERT_SHA1="E9:B3:E2:77:95:75:BA:08:A9:13:72:FC:38:85:EB:A0:1D:D3:E7:3E"
IMAGE_TYPES=("icon","featureGraphic","phoneScreenshots","sevenInchScreenshots","tenInchScreenshots")
RELEASE={
    "name":"RivoSticker 1.0.5 - Sticker Maker",
    "status":"completed",
    "versionCodes":[CODE],
    "releaseNotes":[
        {"language":"en-US","text":"Beautiful new RivoSticker app icon, safely framed for circular Android launchers. AdMob banner, interstitial and optional rewarded ads verified and consent-gated."},
        {"language":"fr-FR","text":"Nouvelle icone RivoSticker adaptee aux formats Android. Configuration publicitaire AdMob verifiee et soumise au consentement."},
        {"language":"ar","text":"أيقونة جديدة جميلة لا تنقص في الأشكال الدائرية. تحسين إعدادات إعلانات AdMob مع احترام موافقة المستخدم."},
    ]
}

def valid_input(path:Path,expected_name:str,expected_sha:str,expected_size:int):
    if path.name!=expected_name or not path.is_file():
        raise RuntimeError("Untrusted or missing publication file")
    if not re.fullmatch(r"[0-9a-f]{64}",expected_sha) or expected_size<1:
        raise RuntimeError("Missing valid pinned checksum or size")
    if path.stat().st_size!=expected_size:
        raise RuntimeError("File byte count changed")
    with path.open("rb") as f:
        digest=hashlib.file_digest(f,"sha256").hexdigest()
    if digest!=expected_sha:
        raise RuntimeError("SHA-256 mismatch: refusing to publish")
    return digest

def image_snapshot(edits,kw):
    return {
        kind: [str(x.get("id")) for x in edits.images().list(
            **kw,language="en-US",imageType=kind
        ).execute().get("images",[])]
        for kind in IMAGE_TYPES
    }

def publish(aab:Path,icon:Path,aab_sha:str,aab_size:int,icon_sha:str,icon_size:int):
    valid_input(aab,"RivoSticker-1.0.5-RivoScan-SIGNED.aab",aab_sha,aab_size)
    valid_input(icon,"RivoSticker-1.0.5-Play-Icon-512.png",icon_sha,icon_size)
    if icon_size>=1048576 or icon.read_bytes()[:8]!=b"\x89PNG\r\n\x1a\n":
        raise RuntimeError("Play Store icon must be PNG under 1MB")
    data=icon.read_bytes()
    if int.from_bytes(data[16:20],"big")!=512 or int.from_bytes(data[20:24],"big")!=512:
        raise RuntimeError("Play Store icon must be exactly 512x512")
    if data[25] != 6:
        raise RuntimeError("Play Store icon must be RGBA with alpha channel")
    http=httplib2.Http(timeout=300)
    http.redirect_codes=http.redirect_codes-{308}
    edits=build("androidpublisher","v3",
        http=AuthorizedHttp(get_credentials(),http=http),
        cache_discovery=False).edits()
    edit_id=edits.insert(packageName=PACKAGE,body={}).execute()["id"]
    kw={"packageName":PACKAGE,"editId":edit_id}
    committed=False
    try:
        tracks=edits.tracks().list(**kw).execute().get("tracks",[])
        prod=next((t for t in tracks if t.get("track")=="production"),None)
        if prod is None or len(prod.get("releases",[]))!=1:
            raise RuntimeError("Expected exactly one existing production release")
        current=prod["releases"][0]
        codes=list(map(str,current.get("versionCodes",[])))
        if current.get("status")!="completed":
            raise RuntimeError("Existing production not completed; do not replace staged or draft")
        if codes==[CODE]:
            raise RuntimeError("Version 6 already on production; verify icon independently, no duplicate upload")
        if codes!=[OLD_CODE]:
            raise RuntimeError("Unexpected previous Production code: "+str(codes))
        for tr in tracks:
            for release in tr.get("releases",[]):
                if any(int(code)>6 for code in release.get("versionCodes",[])):
                    raise RuntimeError("Newer release exists: abort")
        available=edits.countryavailability().get(**kw,track="production").execute()
        if not available.get("countries") and not available.get("restOfWorld",False):
            raise RuntimeError("No production countries: abort")
        bundles=edits.bundles().list(**kw).execute().get("bundles",[])
        if any(str(b.get("versionCode"))==CODE for b in bundles):
            raise RuntimeError("Code6 already uploaded in Play Console; prevent overwrite")
        before=image_snapshot(edits,kw)
        if len(before["icon"])!=1 or len(before["featureGraphic"])!=1 or len(before["phoneScreenshots"])<2:
            raise RuntimeError("Previous Play Store media incomplete; abort")
        print("RIVOSTICKER_105_PREFLIGHT="+json.dumps({"package":PACKAGE,
            "oldCode":OLD_CODE,"newCode":CODE,
            "existingScreenshots":len(before["phoneScreenshots"]),
            "newIconBytes":icon_size,"signedAabBytes":aab_size}),flush=True)
        media=MediaFileUpload(str(aab),mimetype="application/octet-stream",
            resumable=True,chunksize=8*1024*1024)
        req=edits.bundles().upload(**kw,media_body=media)
        response=None
        while response is None:
            progress,response=req.next_chunk(num_retries=4)
            if progress:
                print("RIVOSTICKER_105_AAB_PROGRESS="+str(round(progress.progress()*100))+"%",flush=True)
        if str(response.get("versionCode"))!=CODE:
            raise RuntimeError("Uploaded AAB did not have versionCode 6")
        edits.images().deleteall(**kw,language="en-US",imageType="icon").execute()
        edits.images().upload(**kw,language="en-US",imageType="icon",
            media_body=MediaFileUpload(str(icon),mimetype="image/png")).execute()
        edits.tracks().update(**kw,track="production",
            body={"track":"production","releases":[RELEASE]}).execute()
        after=image_snapshot(edits,kw)
        if any(before[k]!=after[k] for k in IMAGE_TYPES if k!="icon"):
            raise RuntimeError("Non-icon Play media unexpectedly changed; ABORT")
        if len(after["icon"])!=1 or after["icon"]==before["icon"]:
            raise RuntimeError("New Play icon not recorded")
        edits.validate(**kw).execute()
        # Google Play API default cancels any *existing* review when submitting
        # a newer release. Request that behavior explicitly to prevent silently
        # leaving v1.0.5 under Changes not yet sent for review.
        result=edits.commit(**kw,changesNotSentForReview=False,
            changesInReviewBehavior="CANCEL_IN_REVIEW_AND_SUBMIT").execute()
        committed=True
        print("RIVOSTICKER_105_PRODUCTION_SUBMITTED="+json.dumps({
            "package":PACKAGE,"versionCode":6,"versionName":"1.0.5",
            "track":"production","status":"completed",
            "reviewSubmittedByApi":True,
            "priorReviewMayHaveBeenRequeued":True,
            "newPlayIcon":True,"newIconSHA256":icon_sha,
            "originalRivoScanUploadKeyVerifiedByWorkflow":True,
            "otherStoreMediaPreserved":True,"otherTracksPreserved":True,
            "googlePlayApprovalStillRequired":True,
            "editId":result.get("id"),
        },sort_keys=True),flush=True)
    finally:
        if not committed:
            try: edits.delete(**kw).execute()
            except Exception: pass

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--aab",required=True,type=Path)
    p.add_argument("--icon",required=True,type=Path)
    p.add_argument("--aab-sha256",required=True)
    p.add_argument("--aab-size",required=True,type=int)
    p.add_argument("--icon-sha256",required=True)
    p.add_argument("--icon-size",required=True,type=int)
    p.add_argument("--confirm",required=True)
    a=p.parse_args()
    if a.confirm!="PUBLISH_RIVOSTICKER_105_PRODUCTION_AND_NEW_STORE_ICON":
        raise SystemExit("Missing exact authorized package/version target")
    try: publish(a.aab,a.icon,a.aab_sha256,a.aab_size,a.icon_sha256,a.icon_size)
    except Exception as error:
        print("RIVOSTICKER_105_FAILURE="+json.dumps({"type":type(error).__name__,
            "message":str(error)[:500]}),file=sys.stderr,flush=True)
        raise SystemExit(1)
