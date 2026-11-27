#!/usr/bin/env python3
"""Publish existing exact RivoNFC 0.6.1/8 AAB to Internal Testing only.

No upload, no edits to Production, no changes to other applications. Stop on
unexpected versions/tracks. Production was already submitted for review by
the owner through Play Console. This stage is separate.
"""
import json
import os
import sys

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from publish import get_credentials

PACKAGE = "com.ribhlab.rivonfc"
VERSION = "8"
TRACK = "internal"
CONFIRM = "PUBLISH_RIVONFC_061_INTERNAL_ONLY_AFTER_PRODUCTION_REVIEW"

def run():
    if os.environ.get("RIVONFC_INTERNAL_APPROVAL") != CONFIRM:
        raise RuntimeError("Missing explicit RivoNFC Internal Testing approval")
    api = build("androidpublisher", "v3", credentials=get_credentials(), cache_discovery=False)
    edits = api.edits()
    eid = edits.insert(packageName=PACKAGE, body={}).execute()["id"]
    kw = {"packageName":PACKAGE, "editId":eid}
    committed=False
    try:
        bundles=edits.bundles().list(**kw).execute().get("bundles",[])
        codes={str(x.get("versionCode")) for x in bundles}
        print("RIVONFC_EXISTING_BUNDLE_CODES="+json.dumps(sorted(codes)),flush=True)
        if codes!={VERSION}:
            raise RuntimeError("Expected one previously uploaded RivoNFC 0.6.1 bundle versionCode 8; found "+str(sorted(codes)))
        tracks=edits.tracks().list(**kw).execute().get("tracks",[])
        target=next((x for x in tracks if x.get("track")==TRACK),{})
        existing=target.get("releases") or []
        prod=next((x for x in tracks if x.get("track")=="production"),{})
        print("RIVONFC_TRACK_PREFLIGHT="+json.dumps({
          "production":[{"status":x.get("status"),"codes":x.get("versionCodes")} for x in (prod.get("releases") or [])],
          "internal":[{"status":x.get("status"),"codes":x.get("versionCodes")} for x in existing]
        }),flush=True)
        if len(existing)==1 and set(map(str, existing[0].get("versionCodes",[])))=={VERSION} and existing[0].get("status")=="completed":
            print("RIVONFC_INTERNAL_ALREADY_LIVE="+json.dumps({"package":PACKAGE,"track":TRACK,"versionCode":VERSION}),flush=True)
            return
        if existing:
            raise RuntimeError("Internal Testing has existing release(s), refusing overwrite")
        all_codes={str(c) for t in tracks for rel in (t.get("releases") or []) for c in rel.get("versionCodes",[])}
        if any(c!=VERSION for c in all_codes):
            raise RuntimeError("Other Play track already contains unexpected version codes "+str(sorted(all_codes)))
        media={}
        for kind in ("icon","featureGraphic","phoneScreenshots"):
            media[kind]=len(edits.images().list(**kw,language="en-US",imageType=kind).execute().get("images",[]))
        if media["icon"]!=1 or media["featureGraphic"]!=1 or media["phoneScreenshots"]<2:
            raise RuntimeError("Store media is not ready: "+json.dumps(media))
        listing=edits.listings().list(**kw).execute().get("listings",[])
        if not any(x.get("language")=="en-US" and "RivoNFC" in x.get("title","") for x in listing):
            raise RuntimeError("No prepared RivoNFC English store listing")
        release={
          "name":"RivoNFC 0.6.1 — Internal QA",
          "versionCodes":[VERSION],
          "status":"completed",
          "releaseNotes":[
             {"language":"en-US","text":"RivoNFC initial QA: NFC tag reading and writing, inspection, templates, encrypted notes, QR codes, and optional virtual card on compatible phones."},
             {"language":"fr-FR","text":"Test initial de RivoNFC : lecture et écriture NFC, inspection, modèles, notes chiffrées, QR codes et carte virtuelle facultative."},
             {"language":"ar","text":"اختبار RivoNFC الأول: قراءة وكتابة NFC، الفحص، القوالب، تشفير الملاحظات، رموز QR والبطاقة الافتراضية الاختيارية."}
          ]
        }
        edits.tracks().update(**kw,track=TRACK,body={"track":TRACK,"releases":[release]}).execute()
        edits.validate(**kw).execute()
        edits.commit(**kw).execute()
        committed=True
        print("RIVONFC_INTERNAL_COMMITTED="+json.dumps({
           "package":PACKAGE,"track":TRACK,"versionCode":8,"status":"completed",
           "storeImages":media,"otherTracksUnchanged":True,"productionMayStillBeInReview":True,
           "testersMustOptIn":True
        },sort_keys=True),flush=True)
    finally:
        if not committed:
            try:edits.delete(**kw).execute()
            except Exception:print("RIVONFC_EDIT_CLEANUP_WARNING",file=sys.stderr)

if __name__=="__main__":
    try:run()
    except HttpError as e:
        try:
            obj=json.loads(e.content.decode("utf-8"))
            message=obj.get("error",{}).get("message","")
        except Exception:message=str(e.reason)
        print("RIVONFC_INTERNAL_API_BLOCKED="+json.dumps({
            "httpStatus":e.resp.status,"reason":message[:350],"committed":False
        }),file=sys.stderr,flush=True)
        sys.exit(2)
    except Exception as e:
        print("RIVONFC_INTERNAL_BLOCKED="+json.dumps({
            "type":type(e).__name__,"reason":str(e)[:350],"committed":False
        }),file=sys.stderr,flush=True)
        sys.exit(1)
