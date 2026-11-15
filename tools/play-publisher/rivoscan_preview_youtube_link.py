#!/usr/bin/env python3
"""Set the RivoScan Play Store PREVIEW VIDEO only after YouTube publishes it.
Safe default is no write. Never upload APK/AAB, change releases, or overwrite text.
"""
from __future__ import annotations
import argparse
import json
import re
from urllib.parse import urlparse, parse_qs

PACKAGE="com.ribhlab.rivoscan"
LANGUAGE="en-US"
EXPECTED_VERSION="129"
ID=re.compile(r"^[A-Za-z0-9_-]{11}$")

def parse_youtube_url(raw:str)->str:
    parsed=urlparse(raw.strip())
    if parsed.scheme!="https":
        raise ValueError("YouTube URL must use HTTPS")
    host=(parsed.hostname or "").lower()
    if host in ("youtube.com","www.youtube.com","m.youtube.com"):
        if parsed.path=="/watch":
            vid=parse_qs(parsed.query).get("v",[""])[0]
        elif parsed.path.startswith("/shorts/") or parsed.path.startswith("/embed/"):
            vid=parsed.path.split("/")[2] if len(parsed.path.split("/"))>2 else ""
        else:
            raise ValueError("Use a single YouTube video URL, not a playlist/channel")
    elif host=="youtu.be":
        vid=parsed.path.lstrip("/").split("/")[0]
    else:
        raise ValueError("Not a YouTube video host")
    if not ID.fullmatch(vid):
        raise ValueError("Invalid YouTube video ID")
    return "https://www.youtube.com/watch?v="+vid

def publish(url:str):
    from googleapiclient.discovery import build
    from publish import get_credentials
    service=build("androidpublisher","v3",credentials=get_credentials(),cache_discovery=False)
    edits=service.edits()
    edit=edits.insert(packageName=PACKAGE,body={}).execute()
    eid=edit["id"]
    committed=False
    try:
        tracks=edits.tracks().list(packageName=PACKAGE,editId=eid).execute().get("tracks",[])
        version_seen=any(EXPECTED_VERSION in [str(v) for v in release.get("versionCodes",[])]
                         for track in tracks for release in track.get("releases",[]))
        if not version_seen:
            raise RuntimeError("Expected Play version 129 not found; refusing to change a different app release")
        current=edits.listings().get(packageName=PACKAGE,editId=eid,language=LANGUAGE).execute()
        if current.get("video","")==url:
            print("RIVOSCAN_VIDEO_RESULT="+json.dumps({"result":"UNCHANGED",
                "package":PACKAGE,"language":LANGUAGE,"video":url}))
            return
        patch=edits.listings().patch(packageName=PACKAGE,editId=eid,language=LANGUAGE,body={"video":url}).execute()
        if patch.get("video")!=url:
            raise RuntimeError("YouTube link mismatch in Play edit")
        # The Android Publisher listing patch must not modify any other existing fields.
        for field in ("title","shortDescription","fullDescription"):
            if current.get(field)!=patch.get(field):
                raise RuntimeError("Unexpected Play listing text change: "+field)
        edits.validate(packageName=PACKAGE,editId=eid).execute()
        edits.commit(packageName=PACKAGE,editId=eid).execute()
        committed=True
        print("RIVOSCAN_VIDEO_RESULT="+json.dumps({"result":"COMMITTED",
            "package":PACKAGE,"language":LANGUAGE,"versionCode":EXPECTED_VERSION,
            "video":url,"imagesChanged":False,"listingTextChanged":False,
            "aabChanged":False,"releaseTracksChanged":False}))
    finally:
        if not committed:
            try:
                edits.delete(packageName=PACKAGE,editId=eid).execute()
            except Exception:
                pass

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--youtube-url",required=True)
    p.add_argument("--apply",action="store_true")
    p.add_argument("--confirm",default="")
    args=p.parse_args()
    url=parse_youtube_url(args.youtube_url)
    if not args.apply:
        print("DRY_RUN="+json.dumps({"package":PACKAGE,"language":LANGUAGE,"normalized":url}))
        return
    if args.confirm!="RIVOSCAN_04525_VIDEO_ONLY":
        p.error("Exact confirmation required")
    publish(url)

if __name__=="__main__":
    main()
