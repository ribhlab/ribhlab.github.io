#!/usr/bin/env python3
"""Publish owner-authorized TradingFiew Android v1.0.3 (versionCode 4) to Production.

Safeguards: exact app, bundle, existing release draft, no unrelated track or
version modifications, store listing/media checks, and post-commit Play API
verification. Do not claim public availability from a successful commit alone.
"""
from __future__ import annotations

import json
import sys
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from publish import get_credentials

APP="com.ribhlab.tradingfiew"
CODE="4"
RELEASE_NAME="TradingFiew 1.0.3 — AdMob Interstitial"

def say(**values):
    print("TRADINGFIEW_V4_PRODUCTION="+json.dumps(values,ensure_ascii=False),flush=True)

def summaries(prod):
    return [
        {"status":r.get("status"),"versions":[str(v) for v in r.get("versionCodes",[])],
         "name":r.get("name")}
        for r in prod.get("releases",[])
    ]

def main():
    service=build("androidpublisher","v3",credentials=get_credentials(),cache_discovery=False)
    edits=service.edits()
    eid=None
    committed=False
    try:
        eid=edits.insert(packageName=APP,body={}).execute()["id"]
        a={"packageName":APP,"editId":eid}
        bundles=edits.bundles().list(**a).execute().get("bundles",[])
        codes={str(b.get("versionCode")) for b in bundles}
        if not {"3","4"}.issubset(codes) or any(int(v)>4 for v in codes if v.isdigit()):
            raise RuntimeError("Unexpected bundle inventory; refusing to modify Production")
        d=edits.details().get(**a).execute()
        website=d.get("contactWebsite","").rstrip("/")
        if website!="https://tradingfiew.github.io":
            raise RuntimeError("Unexpected developer website: refuse")
        locales=edits.listings().list(**a).execute().get("listings",[])
        if not {"en-US","fr-FR","ar"}.issubset({x.get("language") for x in locales}):
            raise RuntimeError("Multilingual listing is incomplete")
        if not all(x.get("title") and x.get("fullDescription") and x.get("shortDescription") for x in locales):
            raise RuntimeError("One or more Play descriptions are incomplete")
        for kind,count in (("icon",1),("featureGraphic",1),("phoneScreenshots",2)):
            imgs=edits.images().list(**a,language="en-US",imageType=kind).execute().get("images",[])
            if len(imgs)<count:raise RuntimeError("Missing Play listing graphics: "+kind)
        tracks=edits.tracks().list(**a).execute().get("tracks",[])
        prod=next((t for t in tracks if t.get("track")=="production"),None)
        if prod is None:raise RuntimeError("Production track missing")
        old=summaries(prod)
        new4=[r for r in prod.get("releases",[]) if CODE in [str(v) for v in r.get("versionCodes",[])]]
        if len(new4)!=1:raise RuntimeError("Exactly one staged v4 release expected")
        if new4[0].get("status")=="completed":
            say(result="ALREADY_COMPLETED",app=APP,versionCode=4,previous=old,
                committed=False,verification="Existing Production release")
            return 0
        if new4[0].get("status")!="draft":
            raise RuntimeError("Expected v4 Production draft; found different status")
        for old_release in prod.get("releases",[]):
            if old_release is new4[0]:continue
            c=[str(v) for v in old_release.get("versionCodes",[])]
            if c!=["3"] or old_release.get("status") not in ("completed","draft"):
                raise RuntimeError("Unexpected existing Production release; refuse replace")
        verified={
            "name":new4[0].get("name") or RELEASE_NAME,
            "status":"completed",
            "versionCodes":[CODE],
            "releaseNotes":new4[0].get("releaseNotes") or [{"language":"en-US",
             "text":"Adds optional AdMob interstitials with UMP privacy controls and improved Android startup. No banner advertising."}]
        }
        # Replace only the old code 3 Production release with code 4. Retain every
        # other (Internal/Closed) track unchanged.
        edits.tracks().update(**a,track="production",
                              body={"track":"production","releases":[verified]}).execute()
        edits.validate(**a).execute()
        edits.commit(**a).execute()
        committed=True
        # Independently verify the COMMITTED Play result in a new edit.
        check_id=None
        try:
            check_id=edits.insert(packageName=APP,body={}).execute()["id"]
            updated=edits.tracks().get(packageName=APP,editId=check_id,track="production").execute()
            entries=summaries(updated)
            good=any(x["status"]=="completed" and x["versions"]==[CODE] for x in entries)
            say(result="PRODUCTION_COMMIT_VERIFIED" if good else "PRODUCTION_COMMITTED_STATE_NEEDS_REVIEW",
                app=APP,versionCode=4,committed=True,playProduction=entries,
                publicAvailabilityNotYetVerified=True)
            if not good:return 5
        finally:
            if check_id:
                try:edits.delete(packageName=APP,editId=check_id).execute()
                except Exception:print("PLAY_VERIFICATION_EDIT_CLEANUP_FAILED",flush=True)
        return 0
    except HttpError as e:
        msg=""
        try:msg=json.loads(e.content).get("error",{}).get("message","")[:500]
        except Exception:pass
        say(result="PLAY_REJECTED_PRODUCTION",app=APP,committed=committed,
            httpStatus=e.resp.status,message=msg)
        return 3
    except Exception as e:
        say(result="SAFE_PRODUCTION_GATE_BLOCKED",app=APP,committed=committed,
            reason=str(e)[:400],errorType=type(e).__name__)
        return 4
    finally:
        if eid and not committed:
            try:edits.delete(packageName=APP,editId=eid).execute()
            except Exception:print("PLAY_UNCOMMITTED_EDIT_CLEANUP_FAILED",flush=True)

if __name__=="__main__":
    sys.exit(main())
