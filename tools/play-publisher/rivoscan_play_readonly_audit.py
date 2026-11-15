#!/usr/bin/env python3
"""Read-only Google Play release and store-media inventory for RivoScan."""
import json
from googleapiclient.discovery import build
from publish import get_credentials
PACKAGE="com.ribhlab.rivoscan"
def main():
    edits=build("androidpublisher","v3",credentials=get_credentials(),cache_discovery=False).edits()
    eid=edits.insert(packageName=PACKAGE,body={}).execute()["id"]
    try:
        tracks=edits.tracks().list(packageName=PACKAGE,editId=eid).execute().get("tracks",[])
        images={}
        for kind in ("icon","featureGraphic","phoneScreenshots","sevenInchScreenshots","tenInchScreenshots"):
            data=edits.images().list(packageName=PACKAGE,editId=eid,language="en-US",imageType=kind).execute().get("images",[])
            images[kind]={"count":len(data),"ids":[x.get("id") for x in data]}
        bundles=edits.bundles().list(packageName=PACKAGE,editId=eid).execute().get("bundles",[])
        print("RIVOSCAN_PLAY_AUDIT="+json.dumps({"package":PACKAGE,
            "tracks":[{"track":x.get("track"),"releases":[{"name":r.get("name"),"status":r.get("status"),"versionCodes":r.get("versionCodes"),"rollout":r.get("userFraction")} for r in x.get("releases",[])]} for x in tracks],
            "images":images,"uploadedBundleCodes":[x.get("versionCode") for x in bundles]},ensure_ascii=False),flush=True)
    finally:
        edits.delete(packageName=PACKAGE,editId=eid).execute()
if __name__=="__main__":main()
