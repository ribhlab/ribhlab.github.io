#!/usr/bin/env python3
"""Promote the *already uploaded* RivoNFC 0.6.3 code 10 to Production,
then Internal Testing in separate independently validated Google Play edits.

Run ONLY after Play Console 'Contains ads' and Data safety declarations
have been checked and submitted for Google Mobile Ads SDK / UMP.
"""
import argparse
import json
import os
import sys

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from publish import get_credentials

PKG="com.ribhlab.rivonfc"
OLD="9"
NEW="10"
CONFIRM="RIVONFC_063_PLAY_ADS_DATASAFETY_VERIFIED"
NOTES=[
 {"language":"en-US","text":"New optional advertising with privacy choices. Banner sits in a dedicated bottom container; occasional interstitial ads appear between screens, never while reading or writing NFC tags. Reward videos remain optional."},
 {"language":"fr-FR","text":"Ajout de publicités avec choix de confidentialité. Bannière dans un espace séparé en bas; interstitiels occasionnels entre les écrans, jamais pendant l'usage NFC. Vidéos récompensées facultatives."},
 {"language":"ar","text":"إضافة إعلانات مع خيارات الخصوصية. بانر داخل حاوية مستقلة أسفل التطبيق وإعلانات متباعدة بين الأقسام دون مقاطعة NFC، وفيديوهات المكافآت اختيارية."},
]
def log(k,v):print(k+"="+json.dumps(v,ensure_ascii=False,sort_keys=True),flush=True)
def verify_exact_tracks(edits,kw,prod_expected,internal_expected):
    rows=edits.tracks().list(**kw).execute().get("tracks",[])
    tracks={t.get("track"):t for t in rows}
    for name,code in [("production",prod_expected),("internal",internal_expected)]:
        rel=(tracks.get(name) or {}).get("releases",[])
        if len(rel)!=1 or rel[0].get("status")!="completed" or [str(x) for x in rel[0].get("versionCodes",[])]!=[code]:
            raise RuntimeError("Unexpected "+name+" release; refusing overwrite: "+str(rel)[:450])
    for t in rows:
        if t.get("track") not in ("production","internal"):
            for rel in t.get("releases",[]):
                if any(int(x)>10 for x in rel.get("versionCodes",[])):
                    raise RuntimeError("Another track has newer code")
    return tracks
def notes_for(tr,phase):
    old=tr["releases"][0]
    rel={"name":"RivoNFC 0.6.3 — AdMob and privacy controls"+(" (Internal)" if phase=="internal" else ""),
         "versionCodes":[NEW],"status":"completed","releaseNotes":NOTES}
    for key in ("countryTargeting","inAppUpdatePriority"):
        if key in old:rel[key]=old[key]
    return rel
def media(edits,kw):
    return {p:[img["id"] for img in edits.images().list(**kw,language="en-US",imageType=p).execute().get("images",[])]
            for p in ("icon","featureGraphic","phoneScreenshots")}
def run(phase):
    if os.environ.get("RIVONFC_063_COMPLIANCE_APPROVAL")!=CONFIRM:
        raise RuntimeError("No verified Google Play ad declaration / Data safety compliance approval")
    api=build("androidpublisher","v3",credentials=get_credentials(),cache_discovery=False)
    edits=api.edits()
    eid=edits.insert(packageName=PKG,body={}).execute()["id"]
    kw={"packageName":PKG,"editId":eid}
    committed=False
    try:
        bundle_codes=[str(x.get("versionCode")) for x in edits.bundles().list(**kw).execute().get("bundles",[])]
        if NEW not in bundle_codes:raise RuntimeError("Signed code 10 missing from bundle library")
        if any(int(code)>10 for code in bundle_codes):raise RuntimeError("A newer bundle exists; verify latest source")
        expected_production=OLD if phase=="production" else NEW
        tracks=verify_exact_tracks(edits,kw,expected_production,OLD)
        countries=edits.countryavailability().get(**kw,track="production").execute()
        if not countries.get("restOfWorld") and not countries.get("countries"):
            raise RuntimeError("No Production availability configured")
        before=media(edits,kw)
        if len(before["icon"])!=1 or len(before["featureGraphic"])!=1 or len(before["phoneScreenshots"])<2:
            raise RuntimeError("Store artwork or authentic screenshots are missing")
        listings=edits.listings().list(**kw).execute().get("listings",[])
        if not any(x.get("language")=="en-US" and "RivoNFC" in x.get("title","") for x in listings):
            raise RuntimeError("Wrong or missing store listing")
        target=phase
        edits.tracks().update(**kw,track=target,body={
            "track":target,"releases":[notes_for(tracks[target],phase)]
        }).execute()
        after=media(edits,kw)
        if after!=before:raise RuntimeError("Play artwork changed unexpectedly")
        edits.validate(**kw).execute()
        edits.commit(**kw).execute()
        committed=True
        log("RIVONFC_063_PROMOTED",{"phase":phase,"package":PKG,"versionCode":10,
            "status":"completed","otherTrackUnchanged":True,"screenshotsPreserved":True,
            "googleReviewMayStillBeRequired":True})
    finally:
        if not committed:
            try:edits.delete(**kw).execute()
            except Exception:print("Unable to delete uncommitted edit",file=sys.stderr)
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--phase",choices=["production","internal"],required=True)
    a=p.parse_args()
    try:run(a.phase)
    except HttpError as e:
        try:msg=json.loads(e.content.decode()).get("error",{}).get("message","")
        except Exception:msg=str(e)
        log("RIVONFC_063_PLAY_ERROR",{"status":int(e.resp.status),"reason":msg[:550]})
        sys.exit(2)
    except Exception as e:
        log("RIVONFC_063_PROMOTION_BLOCKED",{"error":type(e).__name__,"reason":str(e)[:550]})
        sys.exit(1)
