#!/usr/bin/env python3
"""Atomic RivoNFC 0.6.5 code12 signed icon fix release with real matching media.

No other package, track, listing description, feature graphic, privacy policy,
developer account setting or content declaration is changed. Original code11
Production must be published; code12 must be the newest certified signed AAB.
Any pending Google Play review is preserved: ERROR_IF_IN_REVIEW, never cancel.
"""
from __future__ import annotations
import hashlib
import io
import json
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import httplib2
from google_auth_httplib2 import AuthorizedHttp
from google.auth.transport.requests import AuthorizedSession
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from PIL import Image,ImageStat
from publish import get_credentials

PKG="com.ribhlab.rivonfc"
OLD="11"
NEW="12"
AAB=Path("signed/RivoNFC-0.6.5-RivoScan-SIGNED.aab")
STORE_ICON=Path("signed/RivoNFC-store-icon-065.png")
MEDIA=Path("rivonfc-code12-store")
CONFIRM="RIVONFC_065_ORIGINAL_SIGNED_CODE12_ICON_SAFE_MATCHING_SCREENSHOTS_KEEP_REVIEWS"
ORIGINAL_CAP="signed-release-APK-Android35-adb-no-synthetic-content"
IMAGES=["01-scan.png","02-write.png","03-tools.png","04-history.png"]
NOTES=[
 {"language":"en-US","text":"Fixed the clipped RivoNFC icon for Android launcher masks. Improved app and Play Store icon padding while keeping NFC tools and ad placements consistent."},
 {"language":"fr-FR","text":"Icône NFC corrigée pour les masques Android, sans couper les ondes ni la puce. Les fonctions NFC et les publicités restent identiques."},
 {"language":"ar","text":"إصلاح قص أيقونة NFC في الشاشة الرئيسية مع المحافظة على موجات وشريحة NFC. بدون تغيير وظائف التطبيق والإعلانات."},
]

def emit(label,value):
    print(label+"="+json.dumps(value,ensure_ascii=False,sort_keys=True),flush=True)

def verify_files():
    if os.getenv("RIVONFC_065_PRODUCTION_CONFIRM")!=CONFIRM:
        raise RuntimeError("Explicit package- and release-scoped code12 authorization missing")
    if not AAB.is_file() or AAB.stat().st_size<5_000_000:
        raise RuntimeError("Certified original-key signed RivoNFC code12 AAB missing")
    if not STORE_ICON.is_file() or STORE_ICON.stat().st_size<15000:
        raise RuntimeError("Required 512×512 icon with clipped-artwork fix missing")
    with Image.open(STORE_ICON) as im:
        if im.format!="PNG" or im.size!=(512,512):
            raise RuntimeError("The Play icon must be a 512 x 512 genuine PNG")
        if max(ImageStat.Stat(im.convert("RGB").resize((80,80))).stddev)<12:
            raise RuntimeError("Store icon looks visually blank")
    manifest=json.loads((MEDIA/"CAPTURE-MANIFEST.json").read_text(encoding="utf-8"))
    if any([
        manifest.get("package")!=PKG,
        manifest.get("versionCode")!=12,
        manifest.get("versionName")!="0.6.5",
        manifest.get("capture")!=ORIGINAL_CAP,
        manifest.get("noLiveAdRequests") is not True,
        manifest.get("simulatedNfcReads") is not False,
        manifest.get("size")!="1080x1920",
    ]):
        raise RuntimeError("Store images not captured from the genuine original-signed code12 APK")
    rows=manifest.get("screens",[])
    if [x.get("file") for x in rows]!=IMAGES:
        raise RuntimeError("Missing code12 screenshot or duplicate image ordering")
    seen=set()
    for row,heading in zip(rows,("RivoNFC","Create & write","Tag tools","Activity")):
        name=row["file"]
        b=(MEDIA/name).read_bytes()
        sha=hashlib.sha256(b).hexdigest()
        if sha!=row["sha256"] or sha in seen or len(b)<16000:
            raise RuntimeError("Inauthentic/duplicate RivoNFC code12 image "+name)
        seen.add(sha)
        with Image.open(io.BytesIO(b)) as im:
            if im.format!="PNG" or im.size!=(1080,1920):
                raise RuntimeError("Genuine code12 screenshot geometry invalid")
        root=ET.parse(MEDIA/row["hierarchy"]).getroot()
        nodes=list(root.iter("node"))
        text=" ".join(n.attrib.get("text","")+" "+n.attrib.get("content-desc","") for n in nodes)
        if heading.casefold() not in text.casefold() or "advertisement" not in text.casefold():
            raise RuntimeError("Android screen hierarchy lacks actual NFC UI or ad dock "+name)
        if name=="01-scan.png" and any(n.attrib.get("scrollable")=="true" for n in nodes):
            raise RuntimeError("Signed code12 Scan home wrongly scrolls vertically")
    with AAB.open("rb") as file:
        digest=hashlib.file_digest(file,"sha256").hexdigest()
    return digest

def tracks_map(edit,kw):
    return {t["track"]:t for t in edit.tracks().list(**kw).execute().get("tracks",[])}

def exact_published(track,code):
    releases=(track or {}).get("releases",[])
    return len(releases)==1 and releases[0].get("status")=="completed" and [str(x) for x in releases[0].get("versionCodes",[])]==[code]

def ids(edit,kw,image_type):
    return [r["id"] for r in edit.images().list(
        **kw,language="en-US",imageType=image_type).execute().get("images",[])]

def publish():
    digest=verify_files()
    credentials=get_credentials()
    transport=httplib2.Http(timeout=300)
    transport.redirect_codes=transport.redirect_codes-{308}
    edits=build("androidpublisher","v3",http=AuthorizedHttp(credentials,http=transport),cache_discovery=False).edits()
    eid=edits.insert(packageName=PKG,body={}).execute()["id"]
    kw={"packageName":PKG,"editId":eid}
    committed=False
    try:
        tracks=tracks_map(edits,kw)
        if not exact_published(tracks.get("production"),OLD):
            raise RuntimeError("Production no longer exactly the previously published original-key code11; refusing overwrites")
        for t in tracks.values():
            for rel in t.get("releases",[]):
                if any(int(x)>12 for x in rel.get("versionCodes",[])):
                    raise RuntimeError("A newer version is already on Google Play")
        bundles=[int(x["versionCode"]) for x in edits.bundles().list(**kw).execute().get("bundles",[])]
        if any(x>12 for x in bundles):
            raise RuntimeError("A newer staged bundle than code12 exists")
        old_icon=ids(edits,kw,"icon")
        old_graphic=ids(edits,kw,"featureGraphic")
        old_screens=ids(edits,kw,"phoneScreenshots")
        if len(old_icon)!=1 or len(old_graphic)!=1 or len(old_screens)<2:
            raise RuntimeError("Unexpected existing Play listing artwork; no update is safe")
        listing=edits.listings().get(**kw,language="en-US").execute()
        if listing.get("title")!="RivoNFC: NFC Tools":
            raise RuntimeError("Not the intended exact Google Play RivoNFC listing")
        emit("RIVONFC_065_PRODUCTION_PREFLIGHT",{
            "package":PKG,"previousPublishedCode":11,"newOriginalSignedCode":12,
            "releaseAabSha256":digest,"fourGenuineScreens":IMAGES,
            "oldProductionRelease":tracks["production"].get("releases",[]),
            "oldPlayIconCount":len(old_icon),"oldPlayPhoneScreens":len(old_screens),
            "preserveOtherTracks":True,"preservePrivacyAndDataSafety":True,
        })
        if 12 not in bundles:
            req=edits.bundles().upload(**kw,
                media_body=MediaFileUpload(str(AAB),mimetype="application/octet-stream",
                                           chunksize=8*1024*1024,resumable=True))
            got=None
            while got is None:
                progress,got=req.next_chunk(num_retries=4)
                if progress is not None:
                    print("RIVONFC_065_CODE12_AAB_UPLOAD_PERCENT="+str(round(progress.progress()*100)),flush=True)
            if int(got.get("versionCode",-1))!=12:
                raise RuntimeError("Google Play returned incorrect bundle code after signed upload")
        original=tracks["production"]["releases"][0]
        new_release={"name":"RivoNFC 0.6.5 — fixed fully visible NFC icon",
                     "status":"completed","versionCodes":[NEW],"releaseNotes":NOTES}
        for preserved in ("countryTargeting","inAppUpdatePriority"):
            if preserved in original:new_release[preserved]=original[preserved]
        edits.tracks().update(**kw,track="production",body={
            "track":"production","releases":[new_release]}).execute()
        edits.images().deleteall(**kw,language="en-US",imageType="icon").execute()
        icon_reply=edits.images().upload(**kw,language="en-US",imageType="icon",
            media_body=MediaFileUpload(str(STORE_ICON),mimetype="image/png")).execute(num_retries=3)
        if not icon_reply.get("image",{}).get("id"):
            raise RuntimeError("Google Play did not accept corrected icon")
        edits.images().deleteall(**kw,language="en-US",imageType="phoneScreenshots").execute()
        for item in IMAGES:
            reply=edits.images().upload(**kw,language="en-US",imageType="phoneScreenshots",
                media_body=MediaFileUpload(str(MEDIA/item),mimetype="image/png")).execute(num_retries=3)
            if not reply.get("image",{}).get("id"):
                raise RuntimeError("Google Play rejected real code12 screen "+item)
        after=tracks_map(edits,kw)
        for track,original_track in tracks.items():
            if track!="production" and after.get(track)!=original_track:
                raise RuntimeError("Another Google Play track changed unexpectedly")
        if len(ids(edits,kw,"icon"))!=1 or ids(edits,kw,"featureGraphic")!=old_graphic or len(ids(edits,kw,"phoneScreenshots"))!=4:
            raise RuntimeError("Icon change or genuine media count failed Play edit verification")
        edits.validate(**kw).execute()
        edits.commit(**kw,changesInReviewBehavior="ERROR_IF_IN_REVIEW").execute()
        committed=True
        resp=AuthorizedSession(credentials).get(
            "https://androidpublisher.googleapis.com/androidpublisher/v3/applications/"
            +PKG+"/tracks/production/releases",timeout=25)
        lifecycle="NOT_VERIFIABLE"
        if resp.status_code==200:
            for r in resp.json().get("releases",[]):
                if 12 in [a.get("versionCode") for a in r.get("activeArtifacts",[])]:
                    lifecycle=r.get("releaseLifecycleState","UNKNOWN")
                    break
        emit("RIVONFC_065_PRODUCTION_RECEIPT",{
            "package":PKG,"code":12,"commitAccepted":True,
            "fourGenuineSignedAppScreens":True,"fixedIcon512Pixels":True,
            "originalPlayGraphicUnchanged":True,"otherPlayTracksUnchanged":True,
            "releaseLifecycleState":lifecycle,
            "GoogleReviewNotAssumedApproved":True,
        })
    finally:
        if not committed:
            try:edits.delete(**kw).execute()
            except Exception:print("RIVONFC_065_UNCOMMITTED_EDIT_CLEANUP_WARNING",file=sys.stderr)

if __name__=="__main__":
    try:publish()
    except HttpError as e:
        try:msg=json.loads(e.content.decode()).get("error",{}).get("message","")
        except Exception:msg=type(e).__name__
        emit("RIVONFC_065_GOOGLE_PLAY_BLOCKED",{"httpStatus":int(e.resp.status),"reason":msg[:480]})
        sys.exit(2)
    except Exception as e:
        emit("RIVONFC_065_PRODUCTION_BLOCKED",{"type":type(e).__name__,"reason":str(e)[:480]})
        sys.exit(1)
