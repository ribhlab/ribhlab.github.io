#!/usr/bin/env python3
"""Safely attempt first-ever TradingFiew signed AAB upload into Internal Testing DRAFT.

Uses Google Play's official Developer Publishing API. A first upload can be
rejected until Play App Signing is configured in the Console by its owner.
Never touches Production, never publishes to testers, and never commits a
partially failed edit. Logs only non-secret status codes.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from publish import get_credentials

PACKAGE = "com.ribhlab.tradingfiew"
EXPECTED_CODE = 3
TRACK = "internal"

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--aab", type=Path, required=True)
    p.add_argument("--apply", action="store_true")
    args = p.parse_args()
    if not args.aab.is_file() or args.aab.stat().st_size < 100_000 or args.aab.suffix != ".aab":
        raise SystemExit("INVALID_SIGNED_AAB")
    if not args.apply:
        print(json.dumps({"status":"PREFLIGHT_ONLY","package":PACKAGE,"versionCode":EXPECTED_CODE,
                          "track":TRACK,"releaseStatus":"draft"}))
        return
    api = build("androidpublisher","v3",credentials=get_credentials(),cache_discovery=False)
    edits = api.edits()
    edit = None
    committed = False
    try:
        edit = edits.insert(packageName=PACKAGE,body={}).execute()
        args0 = {"packageName":PACKAGE,"editId":edit["id"]}
        existing_bundles = edits.bundles().list(**args0).execute().get("bundles",[])
        known_codes = [int(x["versionCode"]) for x in existing_bundles if str(x.get("versionCode","")).isdigit()]
        if known_codes:
            print(json.dumps({"status":"EXISTING_BUNDLE_FOUND_NO_FIRST_UPLOAD",
                  "uploadedVersionCodes": known_codes[:15],"package":PACKAGE}))
            return
        tracks = edits.tracks().list(**args0).execute().get("tracks",[])
        track_data = next((t for t in tracks if t.get("track") in ("qa","internal")),None)
        track = track_data["track"] if track_data else "internal"
        releases = (track_data or {}).get("releases",[])
        if any(r.get("status") not in ("completed",) for r in releases):
            raise RuntimeError("Internal track already has a draft/staged/halted release; refusing overwrite")
        media=MediaFileUpload(str(args.aab),mimetype="application/octet-stream",resumable=True)
        uploaded=edits.bundles().upload(**args0,media_body=media).execute()
        code=int(uploaded.get("versionCode",0))
        if code != EXPECTED_CODE:
            raise RuntimeError("Unexpected versionCode returned by Google Play; edit NOT committed")
        release={
          "name":"TradingFiew 1.0.2 — first internal quality check",
          "versionCodes":[str(code)],
          "status":"draft",
          "releaseNotes":[{"language":"en-US","text":
            "First test build: interactive financial charts, drawing tools, educational SMC analysis and locally saved price alerts. Android startup compatibility fixes."}]
        }
        edits.tracks().update(**args0,track=track,
                              body={"track":track,"releases":[*releases,release]}).execute()
        edits.validate(**args0).execute()
        edits.commit(**args0).execute()
        committed=True
        print(json.dumps({"status":"INTERNAL_DRAFT_COMMITTED","package":PACKAGE,
              "track":track,"versionCode":code,"releaseStatus":"draft"}),flush=True)
    except HttpError as error:
        status=getattr(error.resp,"status",0)
        # Play's specific error reason is safe to report after removing any
        # accidental credentials. Do not print HTTP authorization headers.
        detail=""
        try:
            payload=json.loads(error.content.decode("utf-8"))
            detail=str(payload.get("error",{}).get("message",""))[:240]
        except Exception:
            pass
        print(json.dumps({"status":"PLAY_API_BLOCKED","httpStatus":status,
                          "message":detail,"releaseCommitted":False}),flush=True)
        raise SystemExit(3)
    except Exception as error:
        print(json.dumps({"status":"PREFLIGHT_OR_RELEASE_BLOCKED",
                          "kind":type(error).__name__,"message":str(error)[:240],
                          "releaseCommitted":False}),flush=True)
        raise SystemExit(4)
    finally:
        if edit and not committed:
            try:edits.delete(packageName=PACKAGE,editId=edit["id"]).execute()
            except Exception:print("UNCOMMITTED_EDIT_CLEANUP_FAILED",flush=True)

if __name__=="__main__":
    main()
