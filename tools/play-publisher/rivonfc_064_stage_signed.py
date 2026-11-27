#!/usr/bin/env python3
"""Safe code-11 RivoNFC AAB upload to Play's bundle library only.

Never changes track assignments, store listing, data safety or declarations.
The intended first rollout of Ads SDK 0.6.4 must wait until Play Console
'Contains ads' and Data safety declarations are accurately updated.
"""
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

PKG="com.ribhlab.rivonfc"
CODE="11"
EXPECTED_SHA256=os.getenv("RIVONFC_064_SIGNED_SHA256", "").lower()
EXPECTED_SIZE=int(os.getenv("RIVONFC_064_SIGNED_BYTES", "0"))
AAB=Path("signed/RivoNFC-0.6.4-RivoScan-SIGNED.aab")
APPROVAL="STAGE_ONLY_RIVONFC_064_SIGNED_AAB_NO_TRACK_UPDATES"

def report(key,x):
    print(key+"="+json.dumps(x,sort_keys=True,ensure_ascii=False),flush=True)

def checks():
    if os.getenv("RIVONFC_064_STAGE_APPROVAL")!=APPROVAL:
        raise RuntimeError("Exact stage-only authorization missing")
    if len(EXPECTED_SHA256)!=64 or any(c not in "0123456789abcdef" for c in EXPECTED_SHA256) or EXPECTED_SIZE<1000000:
        raise RuntimeError("Pinned signed GitHub release SHA256/size receipt missing")
    if not AAB.is_file() or AAB.stat().st_size!=EXPECTED_SIZE:
        raise RuntimeError("Expected signed RivoNFC 0.6.4 AAB exact file/size missing")
    actual=hashlib.sha256(AAB.read_bytes()).hexdigest()
    if actual!=EXPECTED_SHA256:
        raise RuntimeError("Signed AAB checksum mismatch")
    return actual

def api():
    h=httplib2.Http(timeout=300)
    h.redirect_codes=h.redirect_codes-{308}
    return build("androidpublisher","v3",
                 http=AuthorizedHttp(get_credentials(),http=h),
                 cache_discovery=False).edits()

def summarize(tracks):
    return {t.get("track"): [dict(status=r.get("status"),
                                      versionCodes=[str(v) for v in r.get("versionCodes",[])],
                                      name=r.get("name"))
                                for r in t.get("releases",[])]
            for t in tracks}

def run():
    digest=checks()
    edits=api()
    editid=edits.insert(packageName=PKG,body={}).execute()["id"]
    kw=dict(packageName=PKG,editId=editid)
    committed=False
    try:
        tracks=edits.tracks().list(**kw).execute().get("tracks",[])
        before=summarize(tracks)
        prod=before.get("production",[])
        internal=before.get("internal",[])
        if len(prod)!=1 or len(internal)!=1:
            raise RuntimeError("Expected existing single Production and Internal tracks")
        if (prod[0]["versionCodes"]!=["9"]
            or internal[0]["versionCodes"]!=["9"]
            or prod[0]["status"]!="completed"
            or internal[0]["status"]!="completed"):
            raise RuntimeError("Unexpected existing release(s), refusing risk of concurrent update: "+str(before)[:500])
        if any(int(v)>=11 for releases in before.values() for rel in releases for v in rel["versionCodes"]):
            raise RuntimeError("Code 11 or higher already used on a track; another publisher may be active")
        bundles={str(x["versionCode"]) for x in edits.bundles().list(**kw).execute().get("bundles",[])}
        if any(int(x)>11 for x in bundles):
            raise RuntimeError("Newer bundle exists; do not regress")
        listing=edits.listings().get(**kw,language="en-US").execute()
        if "RivoNFC" not in listing.get("title",""):
            raise RuntimeError("Wrong app listing, refusing write")
        report("RIVONFC_064_STAGE_PREFLIGHT",{"package":PKG,"tracks":before,"bundles":sorted(bundles),
                                               "aabSha256":digest,"aabBytes":EXPECTED_SIZE})
        if CODE not in bundles:
            req=edits.bundles().upload(
                **kw,
                media_body=MediaFileUpload(str(AAB),mimetype="application/octet-stream",
                                          chunksize=8*1024*1024,resumable=True))
            result=None
            while result is None:
                progress,result=req.next_chunk(num_retries=4)
                if progress:
                    print("RIVONFC_064_UPLOAD_PROGRESS="+str(round(progress.progress()*100))+"%",flush=True)
            if str(result.get("versionCode"))!=CODE:
                raise RuntimeError("Play returned incorrect uploaded bundle version")
        if summarize(edits.tracks().list(**kw).execute().get("tracks",[]))!=before:
            raise RuntimeError("Unexpected track change in transaction; refusing commit")
        edits.validate(**kw).execute()
        edits.commit(**kw).execute()
        committed=True
        report("RIVONFC_064_STAGE_COMMITTED",{"package":PKG,"versionCode":11,
                "aabSha256":digest,"uploadedToBundleLibrary":True,
                "productionUnchanged":True,"internalUnchanged":True,
                "requiresPlayAdsAndDataSafetyDeclarations":True})
    finally:
        if not committed:
            try:edits.delete(**kw).execute()
            except Exception:print("RIVONFC_064_STAGE_EDIT_CLEANUP_FAILED",file=sys.stderr)

if __name__=="__main__":
    try:run()
    except HttpError as exc:
        try:why=json.loads(exc.content.decode()).get("error",{}).get("message","")
        except Exception:why=str(exc)
        report("RIVONFC_064_STAGE_PLAY_ERROR",{"status":int(exc.resp.status),"reason":why[:500]})
        sys.exit(2)
    except Exception as exc:
        report("RIVONFC_064_STAGE_BLOCKED",{"error":type(exc).__name__,"reason":str(exc)[:500]})
        sys.exit(1)
