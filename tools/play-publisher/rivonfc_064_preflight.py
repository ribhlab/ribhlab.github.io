#!/usr/bin/env python3
"""RivoNFC 0.6.4 code11 preflight; no release edits or commits.

Reads official Play track lifecycle, exact code11 bundle library, listings,
screenshots and publicly hosted app-ads.txt/privacy. The declarations 'Contains
ads' and Data Safety are NOT exposed by this Android Publisher API. This
script intentionally never invents their saved state.
"""
from __future__ import annotations

import json
import sys
from urllib.parse import quote

from google.auth.transport.requests import AuthorizedSession
from googleapiclient.discovery import build
from publish import get_credentials

PACKAGE="com.ribhlab.rivonfc"
API="https://androidpublisher.googleapis.com/androidpublisher/v3"
EXPECTED_APP_ADS_LINE="google.com, pub-7945572016731367, DIRECT, f08c47fec0942fa0"

def emit(name, value):
    print(name+"="+json.dumps(value,ensure_ascii=False,sort_keys=True),flush=True)

def get_releases(session, track):
    url=API+"/applications/"+quote(PACKAGE,safe="")+"/tracks/"+quote(track,safe="")+"/releases"
    response=session.get(url,timeout=25)
    if response.status_code!=200:
        return {"httpStatus":response.status_code,"releases":None}
    return {"httpStatus":200,"releases":[{
        "name":r.get("releaseName"),
        "lifecycle":r.get("releaseLifecycleState"),
        "versionCodes":[str(a.get("versionCode")) for a in r.get("activeArtifacts",[])]
    } for r in response.json().get("releases",[])]}

def run():
    creds=get_credentials()
    session=AuthorizedSession(creds)
    tracks={name:get_releases(session,name) for name in ("production","internal","alpha")}
    emit("RIVONFC_064_PLAY_TRACKS",{"package":PACKAGE,"tracks":tracks})
    if tracks["production"]["httpStatus"]!=200 or tracks["internal"]["httpStatus"]!=200:
        raise RuntimeError("Cannot verify both RivoNFC Production/Internal tracks")

    edits=build("androidpublisher","v3",credentials=creds,cache_discovery=False).edits()
    eid=edits.insert(packageName=PACKAGE,body={}).execute()["id"]
    kw={"packageName":PACKAGE,"editId":eid}
    try:
        bundles=sorted(int(b["versionCode"]) for b in
            edits.bundles().list(**kw).execute().get("bundles",[]))
        locales=edits.listings().list(**kw).execute().get("listings",[])
        media={}
        for row in locales:
            language=row["language"]
            if language not in ("en-US","fr-FR","ar"):
                # Also observe unexpected locales without assuming available images.
                media[language]={"uninspectedLocale":True}
                continue
            counts={}
            for typ in ("icon","featureGraphic","phoneScreenshots"):
                try:
                    images=edits.images().list(**kw,language=language,
                        imageType=typ).execute().get("images",[])
                    counts[typ]=len(images)
                except Exception as exc:
                    counts[typ]={"error":type(exc).__name__}
            media[language]=counts
        emit("RIVONFC_064_PLAY_LISTING_PREFLIGHT",{
            "package":PACKAGE,
            "bundleCodes":bundles,
            "listings":[{
                "language":row.get("language"),
                "title":row.get("title"),
                "hasShortDescription":bool(row.get("shortDescription")),
                "hasFullDescription":bool(row.get("fullDescription")),
                "descriptionMentionsAds":("ads" in
                    (row.get("fullDescription","")+" "+
                     row.get("shortDescription","")).casefold() or
                     "publicit" in (row.get("fullDescription","")).casefold() or
                     "إعلان" in row.get("fullDescription",""))
            } for row in locales],
            "mediaCounts":media,
            "adsAppContentDeclaration":"NOT_RETRIEVABLE_BY_ANDROID_PUBLISHER_API",
            "dataSafetyDeclaration":"NOT_RETRIEVABLE_BY_ANDROID_PUBLISHER_API",
            "playEditCommitted":False,
        })
    finally:
        try:edits.delete(**kw).execute()
        except Exception:
            print("RIVONFC_064_PREFLIGHT_DELETE_WARNING",file=sys.stderr)

    try:
        import requests
        for name,url,expect in [
            ("APP_ADS_TXT","https://ribhlab.github.io/app-ads.txt",
             EXPECTED_APP_ADS_LINE),
            ("PRIVACY","https://ribhlab.github.io/rivonfc/privacy/",
             "Google Mobile Ads"),
            ("WEBSITE","https://ribhlab.github.io/rivonfc/",
             "RivoNFC"),
        ]:
            response=requests.get(url,timeout=25,allow_redirects=True)
            emit("RIVONFC_064_PUBLIC_"+name,{
                "httpStatus":response.status_code,
                "matchesExpected":response.status_code==200 and
                                  expect in response.text,
                "resolvedHost":response.url.split("/")[2] if response.url.startswith("https://") else "OTHER",
            })
    except Exception as exc:
        emit("RIVONFC_064_PUBLIC_SITE_CHECK_ERROR",type(exc).__name__)
    emit("RIVONFC_064_PREFLIGHT_ACTIONS","NO_TRACK_EDITS_NO_MEDIA_UPDATES_NO_DECLARATION_CHANGES")

if __name__=="__main__":
    try:run()
    except Exception as exc:
        emit("RIVONFC_064_PREFLIGHT_ERROR",{
            "error":type(exc).__name__,"reason":str(exc)[:350]})
        sys.exit(1)
