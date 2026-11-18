#!/usr/bin/env python3
"""Upload owner-approved AdMob-enabled TradingFiew 1.0.3 AAB to Play inventory.
Never distribute unreviewed ads or modify active testing/production releases.
Requires exact v4, original RivoScan signing certificate and validated AAB
from the separate GitHub CI workflow (checked before this script).
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from publish import get_credentials

PACKAGE = "com.ribhlab.tradingfiew"
EXPECTED_VERSION = 4

def run(path: Path):
    if not path.is_file() or path.suffix != ".aab" or path.stat().st_size < 100_000:
        raise RuntimeError("Verified signed AAB is missing")
    service = build("androidpublisher","v3",credentials=get_credentials(),cache_discovery=False)
    edits = service.edits()
    edit_id = None
    committed = False
    try:
        edit_id = edits.insert(packageName=PACKAGE,body={}).execute()["id"]
        kwargs = dict(packageName=PACKAGE,editId=edit_id)
        old = edits.bundles().list(**kwargs).execute().get("bundles",[])
        codes = {int(x["versionCode"]) for x in old}
        if EXPECTED_VERSION in codes:
            print("TRADINGFIEW_PLAY_V4="+json.dumps({
                "status":"VERSION_ALREADY_UPLOADED", "versionCode":4,
                "package":PACKAGE,"tracksUnchanged":True}),flush=True)
            return
        if 3 not in codes or max(codes)!=3:
            raise RuntimeError("Unexpected bundle history; no update performed")
        media=MediaFileUpload(str(path),mimetype="application/octet-stream",
                              resumable=True,chunksize=8*1024*1024)
        uploaded=edits.bundles().upload(**kwargs,media_body=media).execute()
        received=int(uploaded.get("versionCode",0))
        if received!=EXPECTED_VERSION:
            raise RuntimeError("Google Play returned unexpected versionCode")
        edits.validate(**kwargs).execute()
        edits.commit(**kwargs).execute()
        committed=True
        print("TRADINGFIEW_PLAY_V4="+json.dumps({
            "status":"SIGNED_AAB_UPLOADED_AND_COMMITTED","package":PACKAGE,
            "versionCode":4,"tracksUnchanged":True,
            "productionPublished":False}),flush=True)
    except HttpError as exc:
        msg=""
        try:
            msg=str(json.loads(exc.content).get("error",{}).get("message",""))[:350]
        except Exception: pass
        print("TRADINGFIEW_PLAY_V4="+json.dumps({
            "status":"GOOGLE_PLAY_REJECTED","httpStatus":exc.resp.status,
            "message":msg,"committed":False}),flush=True)
        raise SystemExit(3)
    finally:
        if edit_id and not committed:
            try:edits.delete(packageName=PACKAGE,editId=edit_id).execute()
            except Exception: print("TRADINGFIEW_UNCOMMITTED_EDIT_CLEANUP_FAILED",flush=True)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--aab",type=Path,required=True)
    args=parser.parse_args()
    run(args.aab)
if __name__=="__main__":main()
