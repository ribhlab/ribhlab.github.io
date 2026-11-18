#!/usr/bin/env python3
"""Read/write/validate Google Play Production *draft edit* but never commit.

Checks app/version identity, existing Production state and mandatory Play
validation response. This does not publish or roll out to any users.
"""
import json
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from publish import get_credentials

APP="com.ribhlab.tradingfiew"
def main():
    api=build("androidpublisher","v3",credentials=get_credentials(),cache_discovery=False)
    edits=api.edits()
    eid=None
    output={"package":APP,"versionCode":3,"target":"production","committed":False}
    try:
        eid=edits.insert(packageName=APP,body={}).execute()["id"]
        a={"packageName":APP,"editId":eid}
        inventory=edits.bundles().list(**a).execute().get("bundles",[])
        if {str(x.get("versionCode")) for x in inventory}!={"3"}:
            raise RuntimeError("Uploaded AAB inventory changed; refusing to use stale version")
        tracks=edits.tracks().list(**a).execute().get("tracks",[])
        current_prod=next((x for x in tracks if x.get("track")=="production"),{})
        output["existingProductionStatuses"]=[r.get("status") for r in current_prod.get("releases",[])]
        output["existingProductionCodes"]=[r.get("versionCodes") for r in current_prod.get("releases",[])]
        existing=current_prod.get("releases",[])
        if len(existing)>1 or any(r.get("status") not in ("draft",) or r.get("versionCodes") for r in existing):
            raise RuntimeError("Unexpected Production release changed; not overwriting")
        internal=next((x for x in tracks if x.get("track") in ("internal","qa")),{})
        if not any(r.get("status")=="completed" and [str(v) for v in r.get("versionCodes",[])]==["3"] for r in internal.get("releases",[])):
            raise RuntimeError("Signed v3 not completed in Internal testing")
        proposed={"track":"production","releases":[{
            "name":"TradingFiew 1.0.2 — first public release",
            "status":"completed","versionCodes":["3"],
            "releaseNotes":[{"language":"en-US","text":
                "First release: interactive charts, market alerts, drawing tools and educational SMC analysis. Android launcher startup fixes."}]
        }]}
        edits.tracks().update(**a,track="production",body=proposed).execute()
        try:
            edits.validate(**a).execute()
            output["validation"]="GOOGLE_PLAY_EDIT_VALIDATED"
        except HttpError as error:
            output["validation"]="GOOGLE_PLAY_REJECTED_PRODUCTION_EDIT"
            output["httpStatus"]=error.resp.status
            try:output["message"]=json.loads(error.content).get("error",{}).get("message","")[:500]
            except Exception:pass
        print("TRADINGFIEW_PROD_PREFLIGHT="+json.dumps(output),flush=True)
    except HttpError as error:
        output["validation"]="PROD_PREFLIGHT_API_ERROR"
        output["httpStatus"]=error.resp.status
        try:output["message"]=json.loads(error.content).get("error",{}).get("message","")[:450]
        except Exception:pass
        print("TRADINGFIEW_PROD_PREFLIGHT="+json.dumps(output),flush=True)
    except Exception as error:
        output.update(validation="PRECHECK_BLOCKED",errorType=type(error).__name__,reason=str(error)[:400])
        print("TRADINGFIEW_PROD_PREFLIGHT="+json.dumps(output),flush=True)
    finally:
        if eid:
            try:
                edits.delete(packageName=APP,editId=eid).execute()
                print("PRODUCTION_EDIT_NOT_COMMITTED_AND_DELETED=true",flush=True)
            except Exception:
                print("PRODUCTION_EDIT_CLEANUP_FAILED",flush=True)
if __name__=="__main__":main()
