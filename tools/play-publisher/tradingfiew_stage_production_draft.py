#!/usr/bin/env python3
"""Stage existing TradingFiew signed v1.0.2 in Production DRAFT only.

The Play app is not yet published; Google API explicitly rejected completed
production ("Only releases with status draft may be created on draft app").
This changes neither the app's public status nor availability. Fail closed.
"""
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from publish import get_credentials
import json

APP="com.ribhlab.tradingfiew"
def main():
    edits=build("androidpublisher","v3",credentials=get_credentials(),cache_discovery=False).edits()
    eid=None;committed=False
    outcome={"app":APP,"track":"production","versionCode":3,"status":"draft","committed":False}
    try:
        eid=edits.insert(packageName=APP,body={}).execute()["id"]
        a={"packageName":APP,"editId":eid}
        codes={str(b.get("versionCode")) for b in edits.bundles().list(**a).execute().get("bundles",[])}
        if codes!={"3"}:raise RuntimeError("Unexpected bundle versions")
        tracks=edits.tracks().list(**a).execute().get("tracks",[])
        prod=next((t for t in tracks if t.get("track")=="production"),{})
        old=prod.get("releases",[])
        if len(old)>1 or any(r.get("status")!="draft" for r in old):
            raise RuntimeError("Production is no longer an empty draft; refuse overwrite")
        if any(r.get("versionCodes") and [str(v) for v in r.get("versionCodes")]!=["3"] for r in old):
            raise RuntimeError("Production draft already contains a different version")
        if len(old)==1 and [str(v) for v in old[0].get("versionCodes",[])]==["3"]:
            outcome["result"]="ALREADY_STAGED";print("TF_PRODUCTION_DRAFT="+json.dumps(outcome),flush=True);return
        internal=next((t for t in tracks if t.get("track") in ("internal","qa")),{})
        if not any(r.get("status")=="completed" and [str(v) for v in r.get("versionCodes",[])]==["3"] for r in internal.get("releases",[])):
            raise RuntimeError("Version 3 not completed in internal testing")
        release={
            "name":"TradingFiew 1.0.2 — first production draft",
            "status":"draft",
            "versionCodes":["3"],
            "releaseNotes":[{"language":"en-US","text":"Initial release: market charts, drawing tools, local price alerts and educational SMC. Android startup fixes."}]
        }
        edits.tracks().update(**a,track="production",body={"track":"production","releases":[release]}).execute()
        edits.validate(**a).execute()
        edits.commit(**a).execute()
        committed=True
        outcome["result"]="PRODUCTION_DRAFT_COMMITTED_NOT_PUBLIC"
        outcome["committed"]=True
    except HttpError as err:
        outcome.update(result="GOOGLE_PLAY_BLOCKED",httpStatus=err.resp.status)
        try:outcome["message"]=json.loads(err.content).get("error",{}).get("message","")[:420]
        except Exception:pass
    except Exception as err:
        outcome.update(result="SAFE_STAGE_BLOCKED",exception=type(err).__name__,message=str(err)[:320])
    finally:
        if eid and not committed:
            try:edits.delete(packageName=APP,editId=eid).execute()
            except Exception:print("UNCOMMITTED_PRODUCTION_DRAFT_CLEANUP_FAILED",flush=True)
        print("TF_PRODUCTION_DRAFT="+json.dumps(outcome),flush=True)
if __name__=="__main__":main()
