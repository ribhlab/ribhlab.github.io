#!/usr/bin/env python3
"""Place verified TradingFiew 1.0.3/v4 into Production DRAFT, never live.

Preserves any active v3 production release and all existing test releases.
Requires v4 in bundle inventory; fails closed if unexpected tracks exist.
This is NOT permission to distribute AdMob before truthful Play policy declarations.
"""
from __future__ import annotations
import json
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from publish import get_credentials

PKG="com.ribhlab.tradingfiew"
CODE="4"
def main():
    api=build("androidpublisher","v3",credentials=get_credentials(),cache_discovery=False)
    edits=api.edits()
    eid=None
    committed=False
    outcome={"package":PKG,"versionCode":4,"track":"production","targetStatus":"draft",
             "committed":False,"productionDistributed":False}
    try:
        eid=edits.insert(packageName=PKG,body={}).execute()["id"]
        kwargs=dict(packageName=PKG,editId=eid)
        codes={str(x["versionCode"]) for x in edits.bundles().list(**kwargs).execute().get("bundles",[])}
        if CODE not in codes or "3" not in codes:
            raise RuntimeError("Expected signed versionCodes 3 and 4 are not both in Google Play")
        tracks=edits.tracks().list(**kwargs).execute().get("tracks",[])
        prod=next((t for t in tracks if t.get("track")=="production"),{})
        releases=prod.get("releases",[])
        if len(releases)>2:
            raise RuntimeError("Unexpected multiple Production releases; refuse to modify")
        if any(str(v)==CODE for r in releases for v in r.get("versionCodes",[])):
            outcome.update(status="ALREADY_PRESENT",releases=[
                {"name":r.get("name"),"status":r.get("status"),
                 "versionCodes":r.get("versionCodes")} for r in releases])
            print("TF_PRODUCTION_V4_STAGE="+json.dumps(outcome),flush=True)
            return
        if any(any(str(v)!="3" for v in r.get("versionCodes",[])) for r in releases):
            raise RuntimeError("Production already has an unrelated version")
        if any(r.get("status") not in ("completed","draft") for r in releases):
            raise RuntimeError("Production track has staged/halted/in-progress changes")
        draft={"name":"TradingFiew 1.0.3 — AdMob Interstitial only (review draft)",
               "versionCodes":[CODE],"status":"draft",
               "releaseNotes":[{"language":"en-US",
                  "text":"Adds optional AdMob interstitials at intentional navigation pauses, UMP privacy controls and Android stability fixes. No banner ads."}]}
        edits.tracks().update(**kwargs,track="production",
          body={"track":"production","releases":[*releases,draft]}).execute()
        edits.validate(**kwargs).execute()
        edits.commit(**kwargs).execute()
        committed=True
        outcome.update(status="PRODUCTION_V4_DRAFT_COMMITTED_NOT_PUBLIC",
                       committed=True,preservedPreviousReleases=True)
        print("TF_PRODUCTION_V4_STAGE="+json.dumps(outcome),flush=True)
    except HttpError as error:
        msg=""
        try:msg=json.loads(error.content).get("error",{}).get("message","")[:440]
        except Exception:pass
        outcome.update(status="PLAY_API_REJECTED_DRAFT",httpStatus=error.resp.status,message=msg)
        print("TF_PRODUCTION_V4_STAGE="+json.dumps(outcome),flush=True)
    except Exception as error:
        outcome.update(status="SAFE_STAGE_BLOCKED",errorType=type(error).__name__,message=str(error)[:340])
        print("TF_PRODUCTION_V4_STAGE="+json.dumps(outcome),flush=True)
    finally:
        if eid and not committed:
            try:edits.delete(packageName=PKG,editId=eid).execute()
            except Exception:print("TF_V4_EDIT_CLEANUP_FAILED=true",flush=True)
if __name__=="__main__":
    main()
