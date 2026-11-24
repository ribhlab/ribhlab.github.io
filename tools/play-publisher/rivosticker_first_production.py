#!/usr/bin/env python3
"""Publish original-key-signed RivoSticker 1.0.3 to production if Play prerequisites allow.

For RivoSticker ONLY. This never uploads a new artifact, changes signing keys,
deletes other releases, or changes unrelated apps. Requires a nonempty
production country target, and Google Play's own edit validation to pass.
An initial release may be held by Google for review after commit.
"""
from __future__ import annotations
import argparse
import json
import sys
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from publish import get_credentials

PACKAGE = "com.ribhlab.rivosticker"
CODE = "4"
CONFIRM = "PUBLISH_RIVOSTICKER_103_ORIGINAL_SIGNED_TO_PRODUCTION"

def apply():
    edits=build("androidpublisher","v3",credentials=get_credentials(),cache_discovery=False).edits()
    eid=edits.insert(packageName=PACKAGE,body={}).execute()["id"]
    args={"packageName":PACKAGE,"editId":eid}
    committed=False
    try:
        available=edits.countryavailability().get(**args,track="production").execute()
        countries={x.get("countryCode") for x in available.get("countries",[]) if x.get("countryCode")}
        rest=available.get("restOfWorld",False)
        if not countries and not rest:
            raise RuntimeError("PRODUCTION_COUNTRIES_NOT_SELECTED: Set countries/regions for RivoSticker in Google Play Console first")
        bundles=edits.bundles().list(**args).execute().get("bundles",[])
        codes={str(b["versionCode"]) for b in bundles}
        if codes != {CODE}:
            raise RuntimeError("Unexpected Google Play RivoSticker bundle version(s), refuse to override: "+str(sorted(codes)))
        track=edits.tracks().get(**args,track="production").execute()
        releases=track.get("releases",[])
        if len(releases)!=1 or releases[0].get("status")!="draft" or list(map(str,releases[0].get("versionCodes",[])))!=[CODE]:
            raise RuntimeError("Production is not the exact expected RivoSticker v4 draft; do not overwrite")
        listings=edits.listings().list(**args).execute().get("listings",[])
        if not any(x.get("language")=="en-US" and x.get("title") for x in listings):
            raise RuntimeError("RivoSticker English store listing not complete")
        counts={}
        for t in ("icon","featureGraphic","phoneScreenshots"):
            images=edits.images().list(**args,language="en-US",imageType=t).execute().get("images",[])
            counts[t]=len(images)
        if counts["icon"]!=1 or counts["featureGraphic"]!=1 or counts["phoneScreenshots"]<2:
            raise RuntimeError("Store imagery not complete: "+json.dumps(counts))
        rel=dict(releases[0])
        rel["status"]="completed"
        edits.tracks().update(**args,track="production",body={"track":"production","releases":[rel]}).execute()
        try:
            edits.validate(**args).execute()
        except HttpError as exc:
            raise RuntimeError("GOOGLE_PLAY_RELEASE_VALIDATION_REJECTED "+str(exc.resp.status)+" "+str(exc.reason)[:550]) from exc
        # All preconditions and Google API release validation succeeded.
        response=edits.commit(**args).execute()
        committed=True
        print("RIVOSTICKER_PRODUCTION_RELEASE_COMMITTED="+json.dumps({
          "package":PACKAGE,"versionCode":4,"release":"1.0.3",
          "countriesSelected":len(countries),"restOfWorld":rest,
          "mediaCounts":counts,"playEditCommitted":True,
          "googleReviewMayBeRequired":True,
          "notProofOfPublicListing":True,
          "editIDPresent":bool(response.get("id"))
        },sort_keys=True),flush=True)
    finally:
        if not committed:
            try:edits.delete(**args).execute()
            except Exception:print("WARNING: failed to clean temporary publisher edit",file=sys.stderr)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--apply",action="store_true")
    p.add_argument("--confirm",default="")
    args=p.parse_args()
    if not args.apply or args.confirm!=CONFIRM:
        raise ValueError("Both --apply and package-specific --confirm are required")
    apply()

if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("RIVOSTICKER_PRODUCTION_BLOCKED="+str(exc)[:700],file=sys.stderr,flush=True)
        sys.exit(1)
