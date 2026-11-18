#!/usr/bin/env python3
"""Validate possible TradingFiew Internal rollout without committing any changes."""
from __future__ import annotations
import json
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from publish import get_credentials

PACKAGE="com.ribhlab.tradingfiew"
def main():
    api=build("androidpublisher","v3",credentials=get_credentials(),cache_discovery=False)
    edits=api.edits()
    edit=None
    result={"package":PACKAGE,"track":"internal","versionCode":3,
            "committed":False,"purpose":"PREVIEW_ONLY"}
    try:
        edit=edits.insert(packageName=PACKAGE,body={}).execute()
        opts={"packageName":PACKAGE,"editId":edit["id"]}
        listed=edits.tracks().list(**opts).execute().get("tracks",[])
        known=next((t for t in listed if t.get("track") in ("internal","qa")),None)
        if not known:raise RuntimeError("No internal testing track")
        track=known["track"]
        releases=known.get("releases",[])
        if len(releases)!=1 or releases[0].get("status")!="draft" or                 [str(x) for x in releases[0].get("versionCodes",[])]!=["3"]:
            raise RuntimeError("Current track not exactly the known v3 draft; do not change it")
        proposed=dict(releases[0]);proposed["status"]="completed"
        edits.tracks().update(**opts,track=track,body={"track":track,"releases":[proposed]}).execute()
        try:
            edits.validate(**opts).execute()
            result["validation"]="API_EDIT_VALIDATION_PASSED_NOT_PUBLISHED"
        except HttpError as e:
            result["validation"]="API_VALIDATION_BLOCKED"
            result["httpStatus"]=e.resp.status
            try:result["message"]=json.loads(e.content).get("error",{}).get("message","")[:400]
            except Exception:pass
        # Check testing audience without returning personal email addresses.
        try:
            testers=edits.testers().get(**opts,track=track).execute()
            result["testersConfigured"]=bool(testers.get("googleGroups") or testers.get("googleGroups") or testers.get("emailLists"))
            result["testerListGroupCount"]=len(testers.get("googleGroups",[]))
        except HttpError as e:
            result["testersInspectionHttpStatus"]=e.resp.status
        result["track"]=track
        print("TRADINGFIEW_INTERNAL_PREFLIGHT="+json.dumps(result),flush=True)
    except Exception as e:
        result.update(validation="PREFLIGHT_BLOCKED",exception=type(e).__name__,message=str(e)[:300])
        print("TRADINGFIEW_INTERNAL_PREFLIGHT="+json.dumps(result),flush=True)
    finally:
        if edit:
            try:
                edits.delete(packageName=PACKAGE,editId=edit["id"]).execute()
                print("UNCOMMITTED_EDIT_DELETED=true",flush=True)
            except Exception:print("UNCOMMITTED_EDIT_DELETE_FAILED",flush=True)
if __name__=="__main__":main()
