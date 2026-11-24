#!/usr/bin/env python3
"""Commit RivoSticker localized Play listing text only, without touching release tracks."""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path
from publish import get_credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

PACKAGE = "com.ribhlab.rivosticker"
FILE = Path(__file__).parent / "store-listings/rivosticker-locales-2026-11-24.json"
REQUIRED = {"ar", "fr-FR", "es-ES", "pt-BR", "hi-IN", "tr-TR", "id"}
CONFIRM = "LOCALIZE_RIVOSTICKER_EXISTING_PLAY_LISTING"

def load():
    d = json.loads(FILE.read_text("utf-8"))
    if d.get("appId") != PACKAGE or d.get("sourceVersionCode") != 4:
        raise ValueError("RivoSticker package and Play version must match")
    if set(d.get("locales", {})) != REQUIRED:
        raise ValueError("Unexpected locale set")
    for tag, values in d["locales"].items():
        for key, cap in (("title", 30), ("shortDescription", 80), ("fullDescription", 4000)):
            text = values.get(key)
            if not isinstance(text, str) or not (0 < len(text) <= cap):
                raise ValueError(f"{tag}:{key} exceeds Play listing limit")
        if re.search(r"https?://", values["fullDescription"]):
            raise ValueError(f"{tag} should not put URL in listing body")
    return d

def apply(doc):
    service = build("androidpublisher", "v3", credentials=get_credentials(), cache_discovery=False)
    edits = service.edits()
    result = edits.insert(packageName=PACKAGE, body={}).execute()
    args = {"packageName": PACKAGE, "editId": result["id"]}
    committed = False
    try:
        releases = edits.tracks().list(**args).execute().get("tracks", [])
        if any(int(c) > 4 for t in releases for r in t.get("releases", []) for c in r.get("versionCodes", [])):
            raise RuntimeError("More recent RivoSticker release exists; refuse stale listing update")
        codes = {int(b["versionCode"]) for b in edits.bundles().list(**args).execute().get("bundles", [])}
        if 4 not in codes:
            raise RuntimeError("Expected RivoSticker signed AAB version 4 is absent")
        langs = {x["language"] for x in edits.listings().list(**args).execute().get("listings", [])}
        if "en-US" not in langs:
            raise RuntimeError("Official English listing is missing")
        for tag, text in doc["locales"].items():
            body = {"language": tag, **text}
            if tag in langs:
                edits.listings().patch(**args, language=tag, body=body).execute()
            else:
                edits.listings().update(**args, language=tag, body=body).execute()
        edits.validate(**args).execute()
        edits.commit(**args).execute()
        committed = True
        print("RIVOSTICKER_LOCALES_COMMITTED="+json.dumps({
            "package":PACKAGE, "versionCode":4, "locales":sorted(REQUIRED),
            "productionReleaseChanged":False, "countryAvailabilityChanged":False,
            "screenShotsChanged":False,
        },ensure_ascii=False),flush=True)
    finally:
        if not committed:
            try: edits.delete(**args).execute()
            except Exception: print("WARNING: unable to discard uncommitted Play edit",file=sys.stderr)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--apply",action="store_true")
    p.add_argument("--confirm",default="")
    args=p.parse_args()
    d=load()
    print("RIVOSTICKER_LOCALES_PREFLIGHT="+json.dumps({
        "package":PACKAGE, "languageCodes":sorted(d["locales"]),
        "titleLengths":{k:len(v["title"]) for k,v in d["locales"].items()},
    },sort_keys=True),flush=True)
    if args.apply:
        if args.confirm!=CONFIRM:
            raise ValueError("Package-specific authorization string missing")
        apply(d)
if __name__=="__main__":
    main()
