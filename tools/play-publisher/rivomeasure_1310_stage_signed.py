#!/usr/bin/env python3
"""RivoMeasure 1.3.10 code14: library-only Google Play staging (no rollout).

This is a *new* isolated RivoMeasure-only publisher. It never changes any Play
track or listing, and explicitly refuses unexpected live state, newer version
codes or cancellations of an existing review. It does not touch RivoScan.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

import httplib2
from google_auth_httplib2 import AuthorizedHttp
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from publish import get_credentials

PACKAGE="com.ribhlab.ribhmeasure"
VERSION="14"
AAB=Path("signed-1310/RivoMeasure-v1.3.10-code14-original-SIGNED.aab")
CONFIRM="STAGE_ONLY_RIVOMEASURE_CODE14_ORIGINAL_KEY_KEEP_ALL_TRACKS"


def log(label, value):
    print(label+"="+json.dumps(value,sort_keys=True,ensure_ascii=False),flush=True)


def tracks_snapshot(tracks):
    return {
        x["track"]: [
            {"status":v.get("status"),
             "versionCodes":[str(c) for c in v.get("versionCodes",[])],
             "name":v.get("name")}
            for v in x.get("releases",[])
        ] for x in tracks
    }


def run():
    if os.environ.get("RIVOMEASURE_1310_STAGE_CONFIRM")!=CONFIRM:
        raise ValueError("Code14 stage-only authorization missing")
    if not AAB.is_file() or AAB.stat().st_size < 1_000_000:
        raise RuntimeError("Original-signed code14 AAB not available")
    with AAB.open("rb") as f: digest=hashlib.file_digest(f,"sha256").hexdigest()
    http=httplib2.Http(timeout=300)
    http.redirect_codes=http.redirect_codes-{308}
    edits=build("androidpublisher","v3",
                http=AuthorizedHttp(get_credentials(),http=http),
                cache_discovery=False).edits()
    eid=edits.insert(packageName=PACKAGE,body={}).execute()["id"]
    kw=dict(packageName=PACKAGE,editId=eid)
    committed=False
    try:
        tracks=edits.tracks().list(**kw).execute().get("tracks",[])
        before=tracks_snapshot(tracks)
        for name in ("production","alpha"):
            releases=before.get(name,[])
            if (len(releases)!=1 or
                releases[0]["status"]!="completed" or
                releases[0]["versionCodes"]!=["13"]):
                raise RuntimeError("RivoMeasure "+name+
                                   " no longer consists of one published code13 release")
        if any(int(v)>14 for releases in before.values()
               for r in releases for v in r["versionCodes"]):
            raise RuntimeError("A newer RivoMeasure track release exists")
        bundles={str(b["versionCode"])
                 for b in edits.bundles().list(**kw).execute().get("bundles",[])}
        if any(int(v)>14 for v in bundles):
            raise RuntimeError("Newer uploaded RivoMeasure bundle exists; do not downgrade")
        listing=edits.listings().get(**kw,language="en-US").execute()
        if "rivomeasure" not in listing.get("title","").casefold():
            raise RuntimeError("Unexpected Play application title, refusing edit")
        log("RIVOMEASURE_1310_STAGING_PREFLIGHT",{
            "package":PACKAGE,"versionCode":14,
            "oldProduction":before["production"],
            "oldClosedAlpha":before["alpha"],
            "bundleVersions":sorted(bundles),
            "signedAabSha256":digest,
            "trackChangesPermitted":False,
        })
        if VERSION not in bundles:
            req=edits.bundles().upload(
                **kw, media_body=MediaFileUpload(
                    str(AAB),mimetype="application/octet-stream",
                    chunksize=8*1024*1024,resumable=True))
            result=None
            while result is None:
                progress,result=req.next_chunk(num_retries=4)
                if progress is not None:
                    print("RIVOMEASURE_1310_UPLOAD_PROGRESS="+
                          str(round(progress.progress()*100))+"%",flush=True)
            if str(result.get("versionCode"))!=VERSION:
                raise RuntimeError("Google Play returned an incorrect bundle version")
        after=tracks_snapshot(edits.tracks().list(**kw).execute().get("tracks",[]))
        if before!=after:
            raise RuntimeError("Existing Play tracks changed, refusing commit")
        edits.validate(**kw).execute()
        edits.commit(**kw,changesInReviewBehavior="ERROR_IF_IN_REVIEW").execute()
        committed=True
        log("RIVOMEASURE_1310_STAGE_COMMITTED",{
            "package":PACKAGE,"versionCode":14,"signedAabSha256":digest,
            "bundleInPlayLibrary":True,"productionUnchanged":True,
            "closedAlphaUnchanged":True,"storeMediaUnchanged":True,
            "reviewAndWorldwideAvailabilityNotClaimed":True,
        })
    finally:
        if not committed:
            try:edits.delete(**kw).execute()
            except Exception:
                print("RIVOMEASURE_1310_UNCOMMITTED_EDIT_CLEANUP_WARNING",file=sys.stderr)


if __name__=="__main__":
    try:run()
    except HttpError as e:
        try:reason=json.loads(e.content.decode()).get("error",{}).get("message","")
        except Exception:reason=type(e).__name__
        log("RIVOMEASURE_1310_STAGE_PLAY_ERROR",{
            "httpStatus":int(e.resp.status),"reason":reason[:350]})
        sys.exit(2)
    except Exception as e:
        log("RIVOMEASURE_1310_STAGE_BLOCKED",{
            "type":type(e).__name__,"reason":str(e)[:350]})
        sys.exit(1)
