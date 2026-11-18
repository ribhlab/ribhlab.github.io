#!/usr/bin/env python3
"""Upload only *real* TradingFiew Play imagery through an atomic Google Play edit."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from PIL import Image
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from publish import get_credentials

APP="com.ribhlab.tradingfiew"

def validate_media(directory:Path):
    report=json.loads((directory/"verification.json").read_text(encoding="utf-8"))
    if report.get("captureMethod")!="Real public web application rendered in mobile Chromium; no mocked data":
        raise RuntimeError("Image provenance missing")
    if not str(report.get("source","")).startswith("https://tradingfiew.github.io/"):
        raise RuntimeError("Unknown screenshot source")
    items=[("icon","icon.png",(512,512)),
           ("featureGraphic","feature-1024x500.png",(1024,500))]
    captures=report.get("screenshots",[])
    if len(captures)<2 or len(set(captures))!=len(captures):
        raise RuntimeError("Google Play needs genuine phone screenshots")
    for name in captures:items.append(("phoneScreenshots",name,(1080,1920)))
    for _,filename,dimensions in items:
        path=directory/filename
        if not path.is_file() or path.stat().st_size<1000:
            raise RuntimeError("Missing image: "+filename)
        with Image.open(path) as im:
            if im.format!="PNG" or im.size!=dimensions:
                raise RuntimeError("Invalid image format/size: "+filename)
    return items

def apply(folder:Path,files):
    api=build("androidpublisher","v3",credentials=get_credentials(),cache_discovery=False)
    edits=api.edits()
    current=None
    committed=False
    try:
        current=edits.insert(packageName=APP,body={}).execute()
        args={"packageName":APP,"editId":current["id"],"language":"en-US"}
        codes={int(x["versionCode"]) for x in edits.bundles().list(
            packageName=APP,editId=current["id"]).execute().get("bundles",[])}
        if 3 not in codes:raise RuntimeError("TradingFiew v1.0.2 not in Google Play; refuse unrelated media upload")
        kinds=["icon","featureGraphic","phoneScreenshots"]
        for kind in kinds:
            subset=[item for item in files if item[0]==kind]
            if not subset:continue
            edits.images().deleteall(**args,imageType=kind).execute()
            for _,filename,_ in subset:
                media=MediaFileUpload(str(folder/filename),mimetype="image/png",resumable=False)
                edits.images().upload(**args,imageType=kind,media_body=media).execute()
        edits.validate(packageName=APP,editId=current["id"]).execute()
        edits.commit(packageName=APP,editId=current["id"]).execute()
        committed=True
        print(json.dumps({"status":"PLAY_IMAGES_COMMITTED","package":APP,
              "imageCounts":{name:len([x for x in files if x[0]==name]) for name in kinds},
              "releaseTrackNotChanged":True}),flush=True)
    finally:
        if current and not committed:
            try:edits.delete(packageName=APP,editId=current["id"]).execute()
            except Exception:print("WARNING: MEDIA_EDIT_CLEANUP_FAILED",flush=True)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--media-dir",type=Path,required=True)
    parser.add_argument("--apply",action="store_true")
    args=parser.parse_args()
    try:
        files=validate_media(args.media_dir)
        if not args.apply:
            print("TRADINGFIEW_REAL_IMAGES_VALID="+str(len(files)))
            return 0
        apply(args.media_dir,files)
        return 0
    except HttpError as e:
        msg=""
        try:msg=json.loads(e.content).get("error",{}).get("message","")[:250]
        except Exception:pass
        print(json.dumps({"status":"PLAY_IMAGES_FAILED","httpStatus":e.resp.status,
                         "message":msg}),file=sys.stderr)
        return 1
    except Exception as e:
        print(json.dumps({"status":"REAL_MEDIA_BLOCKED","type":type(e).__name__,
                          "message":str(e)[:250]}),file=sys.stderr)
        return 1

if __name__=="__main__":sys.exit(main())
