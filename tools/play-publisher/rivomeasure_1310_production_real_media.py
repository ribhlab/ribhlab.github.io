#!/usr/bin/env python3
"""RivoMeasure 1.3.10 code14 — guarded Production submission with real code14 media.

Google Play edit is atomic: a release and genuine screenshots from the SAME
original-key-signed APK. No other app, alpha track, store icon, feature image,
listing text, privacy statement, or rating is ever modified. On failure
the uncommitted edit is discarded, never cancelling a review.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import sys
from pathlib import Path

from google.auth.transport.requests import AuthorizedSession
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from PIL import Image, ImageStat
from publish import get_credentials

PACKAGE="com.ribhlab.ribhmeasure"
CODE="14"
AAB=Path("signed-1310/RivoMeasure-v1.3.10-code14-original-SIGNED.aab")
MEDIA=Path("code14-store")
APPROVAL="SUBMIT_RIVOMEASURE_1310_CODE14_PRODUCTION_WITH_REAL_SIGNED_APK_SCREENS"
API="https://androidpublisher.googleapis.com/androidpublisher/v3"


def emit(label, data):
    print(label+"="+json.dumps(data,sort_keys=True,ensure_ascii=False),flush=True)


def snapshot(tracks):
    return {t.get("track"):[
        {"status":r.get("status"),
         "versionCodes":[str(c) for c in r.get("versionCodes",[])],
         "name":r.get("name")} for r in t.get("releases",[])]
        for t in tracks}


def verify_inputs():
    if os.getenv("RIVOMEASURE_1310_PRODUCTION_CONFIRM")!=APPROVAL:
        raise RuntimeError("Exact code14 Production authorization missing")
    if not AAB.is_file() or AAB.stat().st_size<1_000_000:
        raise RuntimeError("Missing exact original-signed code14 AAB")
    m=json.loads((MEDIA/"CAPTURE-MANIFEST.json").read_text(encoding="utf-8"))
    if (m.get("package")!=PACKAGE or m.get("versionCode")!=14 or
        m.get("versionName")!="1.3.10" or
        m.get("captureMethod")!="original-signed-release-apk/adb" or
        m.get("liveAdRequestsDisabledDuringQa") is not True):
        raise RuntimeError("Play screenshots do not derive from signed code14 APK")
    imgs=m.get("screens")
    if not isinstance(imgs,list) or not 2<=len(imgs)<=8:
        raise RuntimeError("Google Play requires 2–8 verified phone screenshots")
    names=set(); hashes=set()
    for i in imgs:
        name=i.get("file","")
        if name in names or not name.endswith(".png") or "/" in name or ".." in name:
            raise RuntimeError("Untrusted or duplicate screenshot name")
        names.add(name)
        raw=(MEDIA/name).read_bytes()
        digest=hashlib.sha256(raw).hexdigest()
        if digest!=i.get("sha256") or digest in hashes or len(raw)<20_000:
            raise RuntimeError("Modified, blank, or duplicate code14 screenshot "+name)
        hashes.add(digest)
        with Image.open(io.BytesIO(raw)) as image:
            if image.format!="PNG" or image.size!=(1080,1920):
                raise RuntimeError("Unexpected screenshot pixel geometry "+name)
            if max(ImageStat.Stat(image.convert("RGB").resize((96,160))).stddev)<=8:
                raise RuntimeError("Uniform/blank screenshot "+name)
        xml=(MEDIA/name.replace(".png",".xml")).read_text(encoding="utf-8")
        if "<hierarchy" not in xml:
            raise RuntimeError("Missing genuine Android accessibility evidence "+name)
        if name=="01-home.png" and "rivomeasure" not in xml.casefold():
            raise RuntimeError("Home capture is not from RivoMeasure")
    if "01-home.png" not in names or "02-settings.png" not in names:
        raise RuntimeError("Actual code14 home and settings must be present")
    with AAB.open("rb") as f:
        aab_hash=hashlib.file_digest(f,"sha256").hexdigest()
    return [i["file"] for i in imgs],aab_hash


def publish():
    pictures,aab_hash=verify_inputs()
    credentials=get_credentials()
    edits=build("androidpublisher","v3",credentials=credentials,
                cache_discovery=False).edits()
    eid=edits.insert(packageName=PACKAGE,body={}).execute()["id"]
    kw={"packageName":PACKAGE,"editId":eid}
    committed=False
    try:
        tracks=snapshot(edits.tracks().list(**kw).execute().get("tracks",[]))
        for t in ("production","alpha"):
            releases=tracks.get(t,[])
            if len(releases)!=1 or releases[0]["status"]!="completed" or releases[0]["versionCodes"]!=["13"]:
                raise RuntimeError("Play "+t+" has changed; refusing to overwrite a review or different release")
        bundles={str(b["versionCode"]) for b in
                 edits.bundles().list(**kw).execute().get("bundles",[])}
        if CODE not in bundles or any(int(v)>14 for v in bundles):
            raise RuntimeError("Only the exact latest uploaded code14 may be rolled out")
        listings=edits.listings().list(**kw).execute().get("listings",[])
        locales=sorted({x["language"] for x in listings if x.get("language")})
        if not locales or "en-US" not in locales:
            raise RuntimeError("Expected existing English app listing absent")
        title=edits.listings().get(**kw,language="en-US").execute().get("title","")
        if "rivomeasure" not in title.casefold():
            raise RuntimeError("Wrong Google Play listing")
        emit("RIVOMEASURE_1310_PRODUCTION_PREFLIGHT",{
            "package":PACKAGE,"newCode":14,"priorProduction":tracks["production"],
            "priorAlpha":tracks["alpha"],"storeLanguages":locales,
            "signedAabSha256":aab_hash,"realScreenshots":pictures,
        })
        edits.tracks().update(**kw,track="production",body={
            "track":"production","releases":[{
                "name":"RivoMeasure 1.3.10",
                "status":"completed","versionCodes":[CODE],
                "releaseNotes":[{
                    "language":"en-US",
                    "text":"Improved adaptive banner layout with a dedicated bottom dock, safer interstitial timing after completed measurements, and clearer advertising/privacy information."
                }]
            }]
        }).execute()
        for language in locales:
            edits.images().deleteall(**kw,language=language,imageType="phoneScreenshots").execute()
            for name in pictures:
                response=edits.images().upload(
                    **kw,language=language,imageType="phoneScreenshots",
                    media_body=MediaFileUpload(str(MEDIA/name),mimetype="image/png",resumable=False)
                ).execute(num_retries=3)
                if not response.get("image",{}).get("id"):
                    raise RuntimeError("Google Play rejected genuine code14 screenshot "+language+"/"+name)
            uploaded=edits.images().list(**kw,language=language,
                                          imageType="phoneScreenshots").execute().get("images",[])
            if len(uploaded)!=len(pictures):
                raise RuntimeError("Uploaded Play screenshots count differs from real code14 captures")
        updated=snapshot(edits.tracks().list(**kw).execute().get("tracks",[]))
        for track, releases in tracks.items():
            if track!="production" and updated.get(track)!=releases:
                raise RuntimeError("Another Play track changed, refusing to commit")
        edits.validate(**kw).execute()
        edits.commit(**kw,changesInReviewBehavior="ERROR_IF_IN_REVIEW").execute()
        committed=True
        # The public review lifecycle endpoint is independent of edit commit.
        response=AuthorizedSession(credentials).get(
            API+"/applications/"+PACKAGE+"/tracks/production/releases",timeout=25)
        lifecycle="NOT_VERIFIABLE"
        if response.status_code==200:
            releases=response.json().get("releases",[])
            matches=[r for r in releases if 14 in [
                a.get("versionCode") for a in r.get("activeArtifacts",[])]]
            if matches:lifecycle=matches[0].get("releaseLifecycleState","UNKNOWN")
        emit("RIVOMEASURE_1310_PRODUCTION_PLAY_RECEIPT",{
            "package":PACKAGE,"versionCode":14,"apiEditCommitted":True,
            "realScreenshotsPerLocale":len(pictures),"languages":locales,
            "observedLifecycle":lifecycle,
            "noChangeToClosedAlpha":True,
            "reviewOrPublicAvailabilityMayStillBePending":True,
        })
    finally:
        if not committed:
            try:edits.delete(**kw).execute()
            except Exception:
                print("RIVOMEASURE_1310_UNCOMMITTED_EDIT_CLEANUP_WARNING",file=sys.stderr)


if __name__=="__main__":
    try:publish()
    except HttpError as e:
        try:message=json.loads(e.content.decode()).get("error",{}).get("message","")
        except Exception:message=type(e).__name__
        emit("RIVOMEASURE_1310_PRODUCTION_GOOGLE_ERROR",{
            "httpStatus":int(e.resp.status),"reason":message[:450]})
        sys.exit(2)
    except Exception as e:
        emit("RIVOMEASURE_1310_PRODUCTION_BLOCKED",{
            "exception":type(e).__name__,"reason":str(e)[:450]})
        sys.exit(1)
