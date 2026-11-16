#!/usr/bin/env python3
"""Inspect RivoScan's real Google Play API state; never commit a Play edit.

An uncommitted temporary Play API edit is required to read some resources.
It is ALWAYS deleted after inspection. Does not fill/guess policy forms.
"""
import json
from googleapiclient.discovery import build
from publish import get_credentials

PACKAGE = "com.ribhlab.rivoscan"
EXPECTED_LOCALES = ("en-US", "ar", "fr-FR", "es-ES", "de-DE", "pt-BR", "it-IT")
IMAGE_TYPES = ("icon", "featureGraphic", "phoneScreenshots",
               "sevenInchScreenshots", "tenInchScreenshots")

def main():
    edits = build("androidpublisher", "v3", credentials=get_credentials(),
                  cache_discovery=False).edits()
    eid = edits.insert(packageName=PACKAGE, body={}).execute()["id"]
    try:
        args = {"packageName": PACKAGE, "editId": eid}
        details = edits.details().get(**args).execute()
        listings = edits.listings().list(**args).execute().get("listings", [])
        indexed = {l["language"]: l for l in listings if l.get("language")}
        tracks = edits.tracks().list(**args).execute().get("tracks", [])
        bundles = edits.bundles().list(**args).execute().get("bundles", [])
        images = {}
        missing = []
        for kind in IMAGE_TYPES:
            data = edits.images().list(
                **args, language="en-US", imageType=kind).execute().get("images", [])
            images[kind] = {
                "count": len(data),
                "ids": [im.get("id") for im in data]
            }
            if not data:
                missing.append("en-US image: " + kind)
        for key in ("defaultLanguage", "contactEmail", "contactWebsite"):
            if not str(details.get(key) or "").strip():
                missing.append("app details: " + key)
        for lang in EXPECTED_LOCALES:
            row = indexed.get(lang)
            if not row:
                missing.append("store listing locale: " + lang)
                continue
            for key in ("title", "shortDescription", "fullDescription"):
                if not str(row.get(key) or "").strip():
                    missing.append(lang + ": " + key)
        production = next((t for t in tracks if t.get("track") == "production"), {})
        result = {
            "package": PACKAGE,
            "details": {k: details.get(k) for k in (
                "defaultLanguage", "contactEmail", "contactWebsite", "contactPhone")},
            "locales": {
                lang: {"title": l.get("title"),
                       "shortDescription": l.get("shortDescription"),
                       "fullDescriptionChars": len(l.get("fullDescription") or ""),
                       "complete": all(bool(str(l.get(k) or "").strip())
                                       for k in ("title", "shortDescription", "fullDescription"))}
                for lang, l in indexed.items()},
            "images": images,
            "tracks": [
                {"track": t.get("track"), "releases": [
                    {"name": r.get("name"), "status": r.get("status"),
                     "versionCodes": r.get("versionCodes"), "userFraction": r.get("userFraction")}
                    for r in t.get("releases", [])]}
                for t in tracks],
            "productionStatus": production.get("releases", []),
            "uploadedBundleCodes": [b.get("versionCode") for b in bundles],
            "missingEditableFields": missing,
            "policyDeclarationStatus": "UNKNOWN: needs App content UI (IARC, audience, ads, access, Data Safety)",
            "privacyPolicyURLStatus": "UNKNOWN: needs App content UI",
            "appCategoryStatus": "UNKNOWN: needs Store settings UI",
            "developerVerificationAndPayments": "UNKNOWN: needs developer account UI",
        }
        print("RIVOSCAN_PLAY_COMPLETENESS_AUDIT=" +
              json.dumps(result, ensure_ascii=False, sort_keys=True), flush=True)
    finally:
        edits.delete(packageName=PACKAGE, editId=eid).execute()
        print("RIVOSCAN_AUDIT_EDIT_DELETED=true", flush=True)

if __name__ == "__main__":
    main()
