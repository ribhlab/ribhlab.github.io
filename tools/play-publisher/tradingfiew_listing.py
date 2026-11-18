#!/usr/bin/env python3
"""Publish factual TradingFiew Play store metadata, without changing releases.

No fabricated policy declarations, app-content attestations, tester enrollment,
Data Safety claims or production rollout are performed here.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from publish import get_credentials

APP="com.ribhlab.tradingfiew"
SOURCE=Path(__file__).parent/"store-listings"/"tradingfiew.json"

def validate(doc):
    if doc.get("appId")!=APP:raise ValueError("App ID mismatch")
    loc=doc.get("locales")
    if not isinstance(loc,dict) or not {"en-US","fr-FR","ar"}.issubset(loc):
        raise ValueError("Required factual locales are missing")
    for lang,entry in loc.items():
        for field,limit in (("title",30),("shortDescription",80),("fullDescription",4000)):
            value=entry.get(field)
            if not isinstance(value,str) or not value.strip() or len(value)>limit:
                raise ValueError(f"{lang} {field} invalid: Google Play {limit}-character limit")
    privacy=doc.get("privacyPolicy","")
    if not privacy.startswith("https://tradingfiew.github.io/"):
        raise ValueError("Privacy policy must use the original public website")
    return loc

def apply(doc):
    api=build("androidpublisher","v3",credentials=get_credentials(),cache_discovery=False)
    edits=api.edits()
    edit=None
    committed=False
    try:
        edit=edits.insert(packageName=APP,body={}).execute()
        kwargs=dict(packageName=APP,editId=edit["id"])
        codes=[int(x["versionCode"]) for x in edits.bundles().list(**kwargs).execute().get("bundles",[])]
        if 3 not in codes:raise RuntimeError("Signed first AAB versionCode 3 not in Google Play")
        details=edits.details().get(**kwargs).execute()
        # Preserve the existing developer contact email as-is.
        body={"defaultLanguage":"en-US",
              "contactWebsite":doc["website"]}
        if details.get("contactEmail"):body["contactEmail"]=details["contactEmail"]
        edits.details().patch(**kwargs,body=body).execute()
        existing=edits.listings().list(**kwargs).execute().get("listings",[])
        known={x.get("language") for x in existing}
        for language,data in doc["locales"].items():
            record={"language":language,**{
              k:data[k] for k in ("title","shortDescription","fullDescription")}}
            if language in known:
                edits.listings().patch(**kwargs,language=language,body=record).execute()
            else:
                edits.listings().update(**kwargs,language=language,body=record).execute()
        edits.validate(**kwargs).execute()
        edits.commit(**kwargs).execute()
        committed=True
        result={"status":"PLAY_LISTING_COMMITTED","package":APP,
          "languages":list(doc["locales"].keys()),
          "website":doc["website"],"signedBundleCode":3}
        print(json.dumps(result,ensure_ascii=False),flush=True)
    finally:
        if edit and not committed:
            try:edits.delete(packageName=APP,editId=edit["id"]).execute()
            except Exception:print("INCOMPLETE_PLAY_EDIT_NOT_CLEANED",flush=True)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--apply",action="store_true")
    a=p.parse_args()
    try:
        doc=json.loads(SOURCE.read_text(encoding="utf-8"))
        validate(doc)
        if not a.apply:
            print(json.dumps({"status":"VALID_LISTING_LOCAL_ONLY",
                "locales":list(doc["locales"]), "package":APP}))
            return 0
        apply(doc)
        return 0
    except HttpError as e:
        msg=""
        try:msg=json.loads(e.content).get("error",{}).get("message","")[:240]
        except Exception:pass
        print(json.dumps({"status":"PLAY_LISTING_API_ERROR",
          "httpStatus":getattr(e.resp,"status",0),"message":msg}),file=sys.stderr)
    except Exception as e:
        print(json.dumps({"status":"PLAY_LISTING_BLOCKED",
          "errorType":type(e).__name__,"message":str(e)[:240]}),file=sys.stderr)
    return 1

if __name__=="__main__":
    raise SystemExit(main())
