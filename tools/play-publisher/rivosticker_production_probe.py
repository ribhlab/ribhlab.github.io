#!/usr/bin/env python3
"""Probe RivoSticker's first production-release blockers without publishing anything.

Updates only a temporary Google Play edit, calls validate, and ALWAYS deletes
the edit. Does NOT commit, publish, submit for review, or change country targets.
"""
from __future__ import annotations
import json
import sys
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from publish import get_credentials

PACKAGE = "com.ribhlab.rivosticker"
VERSION = 4

def main():
    edits=build("androidpublisher","v3",credentials=get_credentials(),cache_discovery=False).edits()
    eid=edits.insert(packageName=PACKAGE,body={}).execute()["id"]
    args=dict(packageName=PACKAGE,editId=eid)
    try:
        codes={int(x["versionCode"]) for x in edits.bundles().list(**args).execute().get("bundles",[])}
        if VERSION not in codes or max(codes)>VERSION:
            raise RuntimeError("Unexpected RivoSticker signed bundle inventory")
        track=edits.tracks().get(**args,track="production").execute()
        releases=track.get("releases",[])
        if len(releases)!=1 or releases[0].get("status")!="draft" or list(map(int,releases[0].get("versionCodes",[]))) != [VERSION]:
            raise RuntimeError("Production is not expected single draft release 4; abort test")
        availability=edits.countryavailability().get(**args,track="production").execute()
        countries=sorted(x.get("countryCode","") for x in availability.get("countries",[]) if x.get("countryCode"))
        artwork={}
        for kind in ("icon","featureGraphic","phoneScreenshots"):
            artwork[kind]=len(edits.images().list(**args,language="en-US",imageType=kind).execute().get("images",[]))
        langs=sorted(x["language"] for x in edits.listings().list(**args).execute().get("listings",[]))
        report={"package":PACKAGE,"versionCode":VERSION,"productionStatusBefore":"draft",
                "countries":countries,"restOfWorld":availability.get("restOfWorld",False),
                "artworkCount":artwork,"languageCodes":langs}
        if not countries and not report["restOfWorld"]:
            report["publicAvailability"]="BLOCKED_ZERO_COUNTRIES"
        print("RIVOSTICKER_PRODUCTION_READINESS="+json.dumps(report,sort_keys=True,ensure_ascii=False),flush=True)
        # A temporary edit can test production status changes without rollout.
        draft=dict(releases[0]);draft["status"]="completed"
        try:
            edits.tracks().update(**args,track="production",body={"track":"production","releases":[draft]}).execute()
            print("RIVOSTICKER_TEST_RELEASE_UPDATE_ACCEPTED=TEMPORARY_ONLY",flush=True)
            try:
                edits.validate(**args).execute()
                print("RIVOSTICKER_PRODUCTION_API_VALIDATION=VALID_TEMPORARY_EDIT_ONLY",flush=True)
            except HttpError as ex:
                print("RIVOSTICKER_PRODUCTION_API_VALIDATION="+json.dumps({
                    "status":ex.resp.status,"reason":str(ex.reason)[:650]},ensure_ascii=False),flush=True)
        except HttpError as ex:
            print("RIVOSTICKER_TEST_RELEASE_UPDATE_REJECTED="+json.dumps({
                "status":ex.resp.status,"reason":str(ex.reason)[:650]},ensure_ascii=False),flush=True)
        print("RIVOSTICKER_PRODUCTION_COMMIT=false",flush=True)
    finally:
        edits.delete(**args).execute()
        print("RIVOSTICKER_TEMPORARY_EDIT_DISCARDED=true",flush=True)

if __name__=="__main__":
    try:main()
    except Exception as e:
        print("RIVOSTICKER_PRODUCTION_PROBE_ERROR="+str(e)[:200],file=sys.stderr)
        sys.exit(1)
