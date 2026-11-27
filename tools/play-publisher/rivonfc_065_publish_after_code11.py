#!/usr/bin/env python3
"""Guarded release of RivoNFC 0.6.5 code12, ONLY after code11 is PUBLISHED.

Atomic Google Play edit uploads original-key-signed code12 bundle, authentic
code12 screenshots and genuine 512px icon. Never touches a different package,
another track, privacy declarations, or a release already being reviewed.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import cairosvg
import requests
from google.auth.transport.requests import AuthorizedSession
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from PIL import Image, ImageStat
from publish import get_credentials

PKG="com.ribhlab.rivonfc"
NEW="12"
OLD="11"
API="https://androidpublisher.googleapis.com/androidpublisher/v3"
AAB=Path("signed/RivoNFC-0.6.5-RivoScan-SIGNED.aab")
MEDIA=Path("rivonfc-code12-store")
SVG=Path("public/rivonfc/icon.svg")
ICON=MEDIA/"RivoNFC-0.6.5-Safe-Zone-Play-Icon-512.png"
PROD_CONFIRM="PUBLISH_RIVONFC_065_CODE12_ONLY_AFTER_CODE11_GOOGLE_PUBLISHED"
EXPECTED_AAB_SHA256="089375fbefdd1e0f25878ac88725dbad304854e0361a1c93bfc4a74e2b8e90f6"
EXPECTED_CAPTURE="signed-release-APK-Android35-adb-no-synthetic-content"

def emit(label,value):
    print(label+"="+json.dumps(value,sort_keys=True,ensure_ascii=False),flush=True)

def get_prod_release_state(credentials):
    session=AuthorizedSession(credentials)
    uri=API+"/applications/"+PKG+"/tracks/production/releases"
    for attempt in range(5):
        try:
            res=session.get(uri,timeout=25)
            if res.status_code==200:
                arr=[]
                for release in res.json().get("releases",[]):
                    arr.append({
                        "name":release.get("releaseName",""),
                        "state":release.get("releaseLifecycleState"),
                        "codes":[int(a.get("versionCode",-1)) for a in release.get("activeArtifacts",[])]
                    })
                return arr
            if res.status_code not in (403,429,500,503):
                raise RuntimeError("Google Play production releases read rejected HTTP "+
                                   str(res.status_code))
        except requests.RequestException:
            if attempt==4:raise
        if attempt<4:time.sleep(3+attempt*2)
    raise RuntimeError("Cannot independently verify latest RivoNFC Google Play lifecycle")

def verify_production_release(credentials):
    releases=get_prod_release_state(credentials)
    if any(12 in r["codes"] for r in releases):
        raise RuntimeError("Code12 already present in Production; never duplicate or replace review")
    if not any(r["codes"]==[11] and
               r["state"]=="RELEASE_LIFECYCLE_STATE_PUBLISHED" for r in releases):
        emit("RIVONFC_065_GOOGLE_REVIEW_GATE",{
            "package":PKG,"required":"code11 PUBLISHED",
            "observed":releases,"code12Submitted":False,
        })
        raise RuntimeError("RivoNFC code11 is not yet PUBLISHED; code12 cannot be submitted")
    if any(any(v>12 for v in r["codes"]) for r in releases):
        raise RuntimeError("Newer Production version exists; refuse downgrading")
    return releases

def verify_source_media():
    m=json.loads((MEDIA/"CAPTURE-MANIFEST.json").read_text())
    if (m.get("package")!=PKG or m.get("versionName")!="0.6.5" or
        m.get("versionCode")!=12 or m.get("capture")!=EXPECTED_CAPTURE or
        m.get("size")!="1080x1920" or m.get("noLiveAdRequests") is not True or
        m.get("simulatedNfcReads") is not False):
        raise RuntimeError("Media are not authentic original-key signed RivoNFC code12")
    entries=m.get("screens",[])
    files=["01-scan.png","02-write.png","03-tools.png","04-history.png"]
    if [r.get("file") for r in entries]!=files:
        raise RuntimeError("Exactly four actual NFC code12 screens are required")
    hashes=set()
    for entry,heading in zip(entries,("RivoNFC","Create & write","Tag tools","Activity")):
        filename=entry["file"]
        png=(MEDIA/filename).read_bytes()
        digest=hashlib.sha256(png).hexdigest()
        if digest!=entry.get("sha256") or digest in hashes or len(png)<16000:
            raise RuntimeError("Screenshot missing, duplicate or modified: "+filename)
        hashes.add(digest)
        with Image.open(io.BytesIO(png)) as im:
            if im.format!="PNG" or im.size!=(1080,1920):
                raise RuntimeError("Expected actual 1080x1920 PNG: "+filename)
            if max(ImageStat.Stat(im.convert("RGB").resize((96,160))).stddev)<8:
                raise RuntimeError("Invalid blank RivoNFC screenshot "+filename)
        nodes=list(ET.parse(MEDIA/entry["hierarchy"]).getroot().iter("node"))
        text=" ".join(x.attrib.get("text","")+" "+
                      x.attrib.get("content-desc","") for x in nodes).casefold()
        if heading.casefold() not in text or "advertisement" not in text:
            raise RuntimeError("Accessibility evidence mismatch "+filename)
        if filename=="01-scan.png" and any(
            x.attrib.get("scrollable")=="true" for x in nodes):
            raise RuntimeError("New code12 Scan page incorrectly scrolls")
    if not AAB.is_file() or AAB.stat().st_size<1_000_000:
        raise RuntimeError("Original-signed RivoNFC code12 AAB missing")
    with AAB.open("rb") as f:
        aab_sha=hashlib.file_digest(f,"sha256").hexdigest()
    if aab_sha!=EXPECTED_AAB_SHA256:
        raise RuntimeError("Original signed code12 AAB SHA256 changed")
    source=SVG.read_text(encoding="utf-8")
    if ('viewBox="0 0 512 512"' not in source or
        'transform="translate(64 64) scale(0.75)"' not in source):
        raise RuntimeError("Play icon source does not match safe-zone version12")
    MEDIA.mkdir(parents=True,exist_ok=True)
    cairosvg.svg2png(bytestring=source.encode(),write_to=str(ICON),
                     output_width=512,output_height=512)
    with Image.open(ICON) as im:
        if im.size!=(512,512) or im.format!="PNG":
            raise RuntimeError("Play icon render is not PNG512")
        if max(ImageStat.Stat(im.convert("RGB").resize((64,64))).stddev)<8:
            raise RuntimeError("Play icon is blank or uniform")
    return files,aab_sha,hashlib.sha256(ICON.read_bytes()).hexdigest()

def tracks(edits,kw):
    return {t["track"]:t for t in edits.tracks().list(**kw).execute().get("tracks",[])}

def one_release(track,code):
    if not track:return False
    arr=track.get("releases",[])
    return len(arr)==1 and arr[0].get("status")=="completed" and [
        str(x) for x in arr[0].get("versionCodes",[])]==[code]

def image_ids(edits,kw,kind):
    return [i["id"] for i in edits.images().list(
        **kw,language="en-US",imageType=kind).execute().get("images",[])]

def publish():
    if os.getenv("RIVONFC_065_PRODUCTION_CONFIRM")!=PROD_CONFIRM:
        raise RuntimeError("Specific original-signed code12 Production approval missing")
    files,aab_sha,icon_sha=verify_source_media()
    creds=get_credentials()
    prod_before=verify_production_release(creds)
    edits=build("androidpublisher","v3",credentials=creds,
                cache_discovery=False).edits()
    eid=edits.insert(packageName=PKG,body={}).execute()["id"]
    kw={"packageName":PKG,"editId":eid}
    committed=False
    try:
        before=tracks(edits,kw)
        if not one_release(before.get("production"),OLD):
            raise RuntimeError("Production track not exclusively code11 completed")
        # Preserve all other channels: no Internal or Closed changes.
        codes=[str(x["versionCode"]) for x in
               edits.bundles().list(**kw).execute().get("bundles",[])]
        if any(int(x)>12 for x in codes):
            raise RuntimeError("Newer code exists, refuse older source")
        listings=edits.listings().list(**kw).execute().get("listings",[])
        locale={r["language"]:r for r in listings}
        if locale.get("en-US",{}).get("title")!="RivoNFC: NFC Tools":
            raise RuntimeError("Wrong Play listing or locale")
        if not all(s in locale["en-US"].get("fullDescription","")
                   for s in ("Advertising:","https://ribhlab.github.io/rivonfc/privacy/")):
            raise RuntimeError("Code11 advertising disclosures missing from Play listing")
        icon_before=image_ids(edits,kw,"icon")
        feature_before=image_ids(edits,kw,"featureGraphic")
        if len(icon_before)!=1 or len(feature_before)!=1:
            raise RuntimeError("Original Play icon/feature image incomplete")
        emit("RIVONFC_065_PRODUCTION_PREFLIGHT",{
            "package":PKG,"code12AabSha256":aab_sha,
            "code12IconSha256":icon_sha,"realCode12Screens":files,
            "publishedCode11":prod_before,"otherAppsTouched":False,
            "otherTracksChanged":False,
        })
        if NEW not in codes:
            req=edits.bundles().upload(**kw,
                media_body=MediaFileUpload(str(AAB),
                    mimetype="application/octet-stream",
                    chunksize=8*1024*1024,resumable=True))
            result=None
            while result is None:
                progress,result=req.next_chunk(num_retries=4)
                if progress:print("RIVONFC_065_AAB_PROGRESS="+str(
                    round(progress.progress()*100))+"%",flush=True)
            if str(result.get("versionCode"))!=NEW:
                raise RuntimeError("Play accepted a bundle with unexpected versionCode")
        edits.tracks().update(**kw,track="production",body={
            "track":"production",
            "releases":[{
                "name":"RivoNFC 0.6.5 — improved safe-area app icon",
                "status":"completed","versionCodes":[NEW],
                "releaseNotes":[
                    {"language":"en-US","text":"Fixed launcher icon cropping on phones, tablets and Android themed icons. Same NFC reader/writer with consent-aware contained advertising."},
                    {"language":"fr-FR","text":"Icône de lancement corrigée pour éviter les éléments coupés; NFC et publicités conformes aux choix de confidentialité."},
                    {"language":"ar","text":"إصلاح قص أيقونة التطبيق لتحافظ موجات NFC والشريحة على مظهرها داخل أقنعة أندرويد المختلفة."}
                ]
            }]
        }).execute()
        edits.images().deleteall(**kw,language="en-US",imageType="phoneScreenshots").execute()
        for name in files:
            result=edits.images().upload(**kw,language="en-US",
                imageType="phoneScreenshots",
                media_body=MediaFileUpload(str(MEDIA/name),mimetype="image/png")
            ).execute(num_retries=3)
            if not result.get("image",{}).get("id"):
                raise RuntimeError("Google Play rejected genuine code12 "+name)
        edits.images().deleteall(**kw,language="en-US",imageType="icon").execute()
        result=edits.images().upload(**kw,language="en-US",imageType="icon",
            media_body=MediaFileUpload(str(ICON),mimetype="image/png")).execute(num_retries=3)
        if not result.get("image",{}).get("id"):
            raise RuntimeError("Google Play rejected 512x512 corrected icon")
        after=tracks(edits,kw)
        for track,raw in before.items():
            if track!="production" and after.get(track)!=raw:
                raise RuntimeError("Unrelated NFC testing track was unexpectedly modified")
        if len(image_ids(edits,kw,"phoneScreenshots"))!=4:
            raise RuntimeError("Four original-signed code12 Play screenshots required")
        if len(image_ids(edits,kw,"icon"))!=1:
            raise RuntimeError("Corrected Play launcher icon not accepted")
        if image_ids(edits,kw,"featureGraphic")!=feature_before:
            raise RuntimeError("Feature graphic changed unexpectedly")
        edits.validate(**kw).execute()
        # Any in-review changes cause a safe failure; never cancel a review.
        edits.commit(**kw,changesInReviewBehavior="ERROR_IF_IN_REVIEW").execute()
        committed=True
        emit("RIVONFC_065_PRODUCTION_PLAY_RECEIPT",{
            "package":PKG,"versionCode":12,"editCommitted":True,
            "fourMatchingCode12Screens":True,
            "safeZoneStoreIcon512":True,"otherTracksUnchanged":True,
            "GoogleReviewMayStillBeRequired":True,
        })
    finally:
        if not committed:
            try:edits.delete(**kw).execute()
            except Exception:print("RIVONFC_065_EDIT_CLEANUP_WARNING",file=sys.stderr)

if __name__=="__main__":
    try:publish()
    except HttpError as exc:
        try:msg=json.loads(exc.content.decode()).get("error",{}).get("message","")
        except Exception:msg=type(exc).__name__
        emit("RIVONFC_065_GOOGLE_PLAY_BLOCKED",{
            "httpStatus":int(exc.resp.status),"reason":msg[:440]})
        sys.exit(2)
    except Exception as exc:
        emit("RIVONFC_065_SAFE_RELEASE_BLOCKED",{
            "type":type(exc).__name__,"reason":str(exc)[:440]})
        sys.exit(1)
