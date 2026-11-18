#!/usr/bin/env python3
"""Nonpublishing Google Play preflight of existing TradingFiew v4 Production draft.

Edit is ALWAYS deleted without commit. Checks whether Play API would accept
promoting code4 to completed today. Does NOT answer App Content declarations.
"""
from __future__ import annotations
import json
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from publish import get_credentials

APP="com.ribhlab.tradingfiew"
def main():
    edits=build("androidpublisher","v3",credentials=get_credentials(),cache_discovery=False).edits()
    eid=None
    result={"package":APP,"versionCode":4,"from":"draft","to":"completed",
            "simulationOnly":True,"committed":False}
    try:
        eid=edits.insert(packageName=APP,body={}).execute()["id"]
        args={"packageName":APP,"editId":eid}
        releaseVersions={str(x["versionCode"]) for x in edits.bundles().list(**args).execute().get("bundles",[])}
        if not {"3","4"}.issubset(releaseVersions):
            raise RuntimeError("Source bundle history mismatched")
        tracks=edits.tracks().list(**args).execute().get("tracks",[])
        prod=next((x for x in tracks if x.get("track")=="production"),None)
        if not prod:raise RuntimeError("Production track missing")
        existing=prod.get("releases",[])
        v4=[x for x in existing if "4" in [str(v) for v in x.get("versionCodes",[])]]
        if len(v4)!=1 or v4[0].get("status")!="draft":
            raise RuntimeError("Version 4 not in exactly one Production draft")
        updated=[]
        for release in existing:
            if release is v4[0]:
                release=dict(release)
                release["status"]="completed"
            updated.append(release)
        edits.tracks().update(**args,track="production",
                               body={"track":"production","releases":updated}).execute()
        edits.validate(**args).execute()
        result["playValidation"]="GOOGLE_PLAY_ACCEPTS_RELEASE_EDIT_ONLY"
    except HttpError as e:
        result.update(playValidation="GOOGLE_PLAY_REJECTED",httpStatus=e.resp.status)
        try:result["message"]=json.loads(e.content).get("error",{}).get("message","")[:450]
        except Exception:pass
    except Exception as e:
        result.update(playValidation="NOT_READY",reason=str(e)[:400])
    finally:
        print("TF_V4_PRODUCTION_READINESS="+json.dumps(result),flush=True)
        if eid:
            try:
                edits.delete(packageName=APP,editId=eid).execute()
                print("TF_V4_UNCOMMITTED_EDIT_DELETED=true",flush=True)
            except Exception:
                print("TF_V4_UNCOMMITTED_EDIT_DELETE_FAILED",flush=True)
if __name__=="__main__":main()
