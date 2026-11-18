#!/usr/bin/env python3
"""Activate existing TradingFiew internal test v3 only with no enrolled testers.

This is NOT a public production rollout. Do not alter the production draft.
Fail-closed if testers, bundle codes, media or release state changed.
"""
from __future__ import annotations
import json,sys
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from publish import get_credentials
PACKAGE="com.ribhlab.tradingfiew"
def main():
    api=build("androidpublisher","v3",credentials=get_credentials(),cache_discovery=False)
    edits=api.edits()
    edit=None;committed=False
    try:
        edit=edits.insert(packageName=PACKAGE,body={}).execute()
        args={"packageName":PACKAGE,"editId":edit["id"]}
        bundles=edits.bundles().list(**args).execute().get("bundles",[])
        if {int(b["versionCode"]) for b in bundles}!={3}:
            raise RuntimeError("Bundle inventory no longer exactly versionCode 3; refuse")
        tracks=edits.tracks().list(**args).execute().get("tracks",[])
        production=next((t for t in tracks if t.get("track")=="production"),{})
        if any(x.get("status")=="completed" for x in production.get("releases",[])):
            raise RuntimeError("Production already serving; manual release review required")
        internal=next((t for t in tracks if t.get("track") in ("internal","qa")),None)
        if not internal:raise RuntimeError("No internal track")
        track=internal["track"]
        releases=internal.get("releases",[])
        if len(releases)!=1 or releases[0].get("status")!="draft" or \
             [str(x) for x in releases[0].get("versionCodes",[])]!=["3"]:
            raise RuntimeError("Internal track not exact v3 draft")
        testers=edits.testers().get(**args,track=track).execute()
        if testers.get("googleGroups") or testers.get("emailLists"):
            raise RuntimeError("Testers are already configured; stop because startup QA not proven")
        listings=edits.listings().list(**args).execute().get("listings",[])
        if not {"en-US","fr-FR","ar"}.issubset({x["language"] for x in listings}):
            raise RuntimeError("Full Play text not yet present")
        for kind,threshold in (("icon",1),("featureGraphic",1),("phoneScreenshots",2)):
            images=edits.images().list(**args,language="en-US",imageType=kind).execute().get("images",[])
            if len(images)<threshold:raise RuntimeError("Missing required original Play art: "+kind)
        release=dict(releases[0]);release["status"]="completed"
        edits.tracks().update(**args,track=track,body={"track":track,"releases":[release]}).execute()
        edits.validate(**args).execute()
        edits.commit(**args).execute()
        committed=True
        print(json.dumps({"result":"INTERNAL_TEST_TRACK_COMMITTED","app":PACKAGE,
                           "track":track,"versionCode":3,"releaseStatus":"completed",
                           "testersConfigured":False,"productionTouched":False}),flush=True)
    except HttpError as e:
        msg=""
        try:msg=json.loads(e.content).get("error",{}).get("message","")[:350]
        except Exception:pass
        print(json.dumps({"result":"GOOGLE_PLAY_BLOCKED_INTERNAL",
              "httpStatus":e.resp.status,"message":msg,"committed":False}),flush=True)
        return 3
    except Exception as e:
        print(json.dumps({"result":"SAFE_INTERNAL_PROMOTION_BLOCKED",
             "type":type(e).__name__,"message":str(e)[:300],"committed":False}),flush=True)
        return 4
    finally:
        if edit and not committed:
            try:edits.delete(packageName=PACKAGE,editId=edit["id"]).execute()
            except Exception:print("WARNING_UNCOMMITTED_EDIT_NOT_CLEANED",flush=True)
    return 0
if __name__=="__main__":sys.exit(main())
