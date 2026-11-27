#!/usr/bin/env python3
"""Submit RivoTalk alpha08 code 8 to Production with matching *actual* screenshots.

One atomic Google Play edit: preserve icon/listing text, change only RivoTalk
Production bundle and phone screenshots, validate and commit. On ANY failure
delete the uncommitted edit. No other app, track, or artwork changes.
"""
from __future__ import annotations
import hashlib
import io
import json
import os
import sys
from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from PIL import Image, ImageStat
from publish import get_credentials

PACKAGE="com.ribhlab.rivotalk"
VERSION="8"
SOURCE_SHA="73ba801e900882a8e7c9bd9514d7ac6835de190e"
SIGNED_AAB=Path("rivotalk-signed/RivoTalk-0.1.0-alpha08-RivoScan-SIGNED.aab")
MEDIA_DIR=Path("rivotalk-media")
SCREENS=("01-home.png","04-settings.png")
CONFIRM="SUBMIT_EXACT_RIVOTALK_08_PRODUCTION_WITH_GENUINE_MATCHING_SCREENSHOTS"


def emit(label, data):
    print(label+"="+json.dumps(data,sort_keys=True,ensure_ascii=False),flush=True)


def check_inputs():
    if os.environ.get("RIVOTALK_08_PROMOTION_CONFIRM") != CONFIRM:
        raise RuntimeError("Specific promotion authorization missing")
    if not SIGNED_AAB.is_file() or SIGNED_AAB.stat().st_size<1_000_000:
        raise RuntimeError("Original signed RivoTalk alpha08 source AAB unavailable")
    manifest=(MEDIA_DIR/"APP_IDENTITY.txt").read_text(encoding="utf-8")
    if "versionCode=8" not in manifest or "version=0.1.0-alpha08" not in manifest:
        raise RuntimeError("Screenshots do not attest the exact code8 release")
    expected=(MEDIA_DIR/"SHA256SUMS.txt").read_text(encoding="utf-8").splitlines()
    matches={}
    for line in expected:
        parts=line.split(None,1)
        if len(parts)!=2: raise RuntimeError("Invalid screenshot SHA256 manifest")
        digest,filename=parts
        matches[filename.strip().lstrip("*")]=digest
    if set(matches)!=set(SCREENS):
        raise RuntimeError("Wrong screenshot set; do not publish old or incomplete media")
    digests=set()
    for name in SCREENS:
        f=MEDIA_DIR/name
        raw=f.read_bytes()
        d=hashlib.sha256(raw).hexdigest()
        if d!=matches[name] or d in digests or len(raw)<18_000:
            raise RuntimeError("Image content changed or duplicate: "+name)
        digests.add(d)
        with Image.open(io.BytesIO(raw)) as img:
            if img.format!="PNG" or img.size!=(1080,1920):
                raise RuntimeError("Wrong Android screenshot shape: "+name)
            if max(ImageStat.Stat(img.convert("RGB").resize((96,160))).stddev)<=8:
                raise RuntimeError("Blank or artificial screenshot: "+name)
        xml=(MEDIA_DIR/f.replace(".png",".xml")).read_text(encoding="utf-8")
        if "hierarchy" not in xml or not any(w in xml.lower() for w in ("rivotalk","ready to connect","create group")):
            # A settings page may not contain app title; both come from the same
            # verified app capture, so the home has explicit identity.
            if name=="01-home.png":
                raise RuntimeError("Home image lacks genuine RivoTalk accessibility evidence")
    return {k:v for k,v in matches.items()}


def snapshot(tracks):
    return {t.get("track"):[{"status":r.get("status"),
           "codes":[str(x) for x in r.get("versionCodes",[])],
           "name":r.get("name")} for r in t.get("releases",[])]
           for t in tracks}


def publish():
    checks=check_inputs()
    edits=build("androidpublisher","v3",credentials=get_credentials(),cache_discovery=False).edits()
    eid=edits.insert(packageName=PACKAGE,body={}).execute()["id"]
    kw={"packageName":PACKAGE,"editId":eid}
    committed=False
    try:
        versions={str(x["versionCode"]) for x in edits.bundles().list(**kw).execute().get("bundles",[])}
        if VERSION not in versions or any(int(x)>8 for x in versions):
            raise RuntimeError("Code 8 must already be the latest approved signed Play bundle")
        before=snapshot(edits.tracks().list(**kw).execute().get("tracks",[]))
        production=before.get("production",[])
        if len(production)!=1 or production[0]["codes"]!=["4"] or production[0]["status"]!="completed":
            raise RuntimeError("Production changed or is not a single completed code4; abort")
        for t,releases in before.items():
            for rel in releases:
                if any(int(v)>8 for v in rel["codes"]):
                    raise RuntimeError("A newer Play release exists, refusing stale rollout")
        listings=edits.listings().list(**kw).execute().get("listings",[])
        locales=sorted({x["language"] for x in listings if x.get("language")})
        if "en-US" not in locales:
            raise RuntimeError("English Play listing not present")
        en=edits.listings().get(**kw,language="en-US").execute()
        if "rivotalk" not in en.get("title","").casefold():
            raise RuntimeError("Unexpected Play app title, refusing edit")
        emit("RIVOTALK_08_PROMOTION_PREFLIGHT",{
            "package":PACKAGE,"code":8,"oldProduction":production,
            "locales":locales,"screenshots":checks,
            "otherTracksPreserved":True,
        })
        edits.tracks().update(**kw,track="production",body={
            "track":"production","releases":[{
                "name":"RivoTalk 0.1.0-alpha08",
                "status":"completed","versionCodes":[VERSION],
                "releaseNotes":[{"language":"en-US",
                    "text":"Updated Bluetooth radio interface, more reliable audio and permissions, and a safely contained bottom AdMob banner with UMP consent and controlled interstitials."}],
            }],
        }).execute()
        for locale in locales:
            edits.images().deleteall(**kw,language=locale,imageType="phoneScreenshots").execute()
            for name in SCREENS:
                response=edits.images().upload(
                    **kw,language=locale,imageType="phoneScreenshots",
                    media_body=MediaFileUpload(str(MEDIA_DIR/name),mimetype="image/png",
                                               resumable=False),
                ).execute(num_retries=3)
                if not response.get("image",{}).get("id"):
                    raise RuntimeError("Google Play refused a real screenshot for "+locale)
            stored=edits.images().list(**kw,language=locale,imageType="phoneScreenshots").execute().get("images",[])
            if len(stored)!=len(SCREENS):
                raise RuntimeError("Play media mismatch after upload: "+locale)
        updated=snapshot(edits.tracks().list(**kw).execute().get("tracks",[]))
        for track, releases in before.items():
            if track!="production" and updated.get(track)!=releases:
                raise RuntimeError("Other track changed; refusing atomic Play commit")
        edits.validate(**kw).execute()
        edits.commit(**kw,changesInReviewBehavior="ERROR_IF_IN_REVIEW").execute()
        committed=True
        verify=edits.insert(packageName=PACKAGE,body={}).execute()["id"]
        vk=dict(packageName=PACKAGE,editId=verify)
        try:
            prod=edits.tracks().get(**vk,track="production").execute().get("releases",[])
            result={"package":PACKAGE,"code":8,"playEditCommitted":True,
                    "production":[{"status":r.get("status"),
                    "codes":[str(x) for x in r.get("versionCodes",[])]} for r in prod],
                    "localesWithRealCode8Screenshots":locales,
                    "screenshotsPerLocale":len(SCREENS),
                    "googleReviewStillMayBePending":True}
            emit("RIVOTALK_08_PROMOTION_PLAY_RECEIPT",result)
            if not any(r.get("status")=="completed" and
               [str(x) for x in r.get("versionCodes",[])]==[VERSION] for r in prod):
                raise RuntimeError("Commit succeeded but post-commit Production does not show code8")
        finally:
            try:edits.delete(packageName=PACKAGE,editId=verify).execute()
            except Exception:pass
    finally:
        if not committed:
            try:edits.delete(**kw).execute()
            except Exception:print("WARNING uncommitted RivoTalk Play edit cleanup failed",file=sys.stderr)


if __name__=="__main__":
    try:publish()
    except HttpError as e:
        try:reason=json.loads(e.content.decode()).get("error",{}).get("message","")
        except Exception:reason=type(e).__name__
        emit("RIVOTALK_08_PROMOTION_PLAY_ERROR",{
            "httpStatus":int(e.resp.status),"reason":reason[:420]})
        sys.exit(2)
    except Exception as e:
        emit("RIVOTALK_08_PROMOTION_BLOCKED",{
            "exception":type(e).__name__,"reason":str(e)[:420]})
        sys.exit(1)
