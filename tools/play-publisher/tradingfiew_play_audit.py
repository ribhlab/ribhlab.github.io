#!/usr/bin/env python3
"""Inspect existing TradingFiew Play Console status without committing changes.
CAUTION: Google Play Edits API creates a temporary edit; it may invalidate
unsaved Play Console edits. No release is uploaded/published here.
"""
import json, sys
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from publish import get_credentials

PACKAGE="com.ribhlab.tradingfiew"

def main():
    try:
        creds=get_credentials()
        client=build("androidpublisher","v3",credentials=creds,cache_discovery=False)
        edits=client.edits()
        edit=None
        try:
            edit=edits.insert(packageName=PACKAGE,body={}).execute()
            editid=edit["id"]
            args={"packageName":PACKAGE,"editId":editid}
            details=edits.details().get(**args).execute()
            listing=edits.listings().list(**args).execute().get("listings",[])
            tracks=edits.tracks().list(**args).execute().get("tracks",[])
            bundles=edits.bundles().list(**args).execute().get("bundles",[])
            images={}
            for kind in ["icon","featureGraphic","phoneScreenshots","sevenInchScreenshots","tenInchScreenshots"]:
                try:
                    records=edits.images().list(**args,language="en-US",imageType=kind).execute().get("images",[])
                    images[kind]={"count":len(records)}
                except HttpError as e:
                    images[kind]={"errorStatus":e.resp.status}
            fields=["title","shortDescription","fullDescription"]
            result={
                "status":"APP_API_ACCESS_OK",
                "package":PACKAGE,
                "details":{key:details.get(key) for key in ["defaultLanguage","contactWebsite","contactEmail","contactPhone"]},
                "locales":{row.get("language"):{
                    "title":row.get("title"),
                    "shortDescription":row.get("shortDescription"),
                    "fullDescriptionChars":len(row.get("fullDescription","")),
                    "complete":all(bool(row.get(key)) for key in fields)}
                    for row in listing},
                "uploadedVersionCodes":[x.get("versionCode") for x in bundles],
                "tracks":[{"track":t.get("track"),"releases":[{
                    "status":r.get("status"),"name":r.get("name"),"versionCodes":r.get("versionCodes")
                } for r in t.get("releases",[])]} for t in tracks],
                "images":images,
                "appContentPolicies":"not accessible by Play Developer API; must inspect Console UI"
            }
            print("TRADINGFIEW_PLAY_AUDIT="+json.dumps(result,ensure_ascii=False),flush=True)
        finally:
            if edit:
                edits.delete(packageName=PACKAGE,editId=edit["id"]).execute()
                print("TEMP_EDIT_DELETED=true",flush=True)
        return 0
    except HttpError as e:
        print("TRADINGFIEW_PLAY_AUDIT_ERROR=HTTP_"+str(e.resp.status),flush=True)
        return 2
    except Exception as e:
        print("TRADINGFIEW_PLAY_AUDIT_ERROR="+type(e).__name__,flush=True)
        return 3

if __name__=="__main__":sys.exit(main())
