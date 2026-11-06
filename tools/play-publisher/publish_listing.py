#!/usr/bin/env python3
"""Prepare RivoScan multilingual store listings for Google Play Developer API.

--check (default) never connects to Google. --apply commits descriptions using
edits.listings, and must only run after the application's first Play Console
upload is saved. No images, AABs, policy declarations or testing tracks are modified.
"""
from __future__ import annotations
import argparse
import json
import re
import struct
import sys
import tempfile
from pathlib import Path
from publish import get_credentials

PACKAGE = "com.ribhlab.rivoscan"
# Developer contact shared with NovaGrid. App-specific website and privacy policy.
SUPPORT_EMAIL = "rachid022note4@gmail.com"
APP_WEBSITE = "https://ribhlab.github.io/rivoscan/"
PRIVACY_POLICY_URL = "https://ribhlab.github.io/rivoscan/privacy/"
ALLOWED_LOCALES = {"en-US", "fr-FR", "ar", "es-ES", "de-DE", "pt-BR", "it-IT"}


def load(path: Path) -> dict:
    doc = json.loads(path.read_text(encoding="utf-8"))
    if doc.get("appId") != PACKAGE:
        raise ValueError("Listing package mismatch")
    locales = doc.get("locales")
    if not isinstance(locales, dict) or set(locales) != ALLOWED_LOCALES:
        raise ValueError("Expected seven supported RivoScan app-language listings")
    for lang, value in locales.items():
        if not isinstance(value, dict):
            raise ValueError(f"Invalid listing body for {lang}")
        for field, max_len in [("title", 30), ("shortDescription", 80), ("fullDescription", 4000)]:
            s = value.get(field)
            if not isinstance(s, str) or not s.strip() or len(s) > max_len:
                raise ValueError(f"{lang} {field} violates Google Play {max_len} character limit")
        if re.search(r"https?://", value["fullDescription"]):
            raise ValueError(f"{lang}: URLs are not supported in listing descriptions")
    return doc


def verify_icon(path: Path) -> Path:
    """Only use the real source app icon; do not generate fake screenshots."""
    raw = path.read_bytes()
    if not 100 <= len(raw) <= 1024 * 1024 or raw[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Icon must be a non-empty PNG below 1 MiB")
    width, height = struct.unpack(">II", raw[16:24])
    if (width, height) != (512, 512):
        raise ValueError("Google Play app icon must be 512 x 512")
    return path


def apply_listings(doc: dict) -> dict:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    service = build("androidpublisher", "v3", credentials=get_credentials(), cache_discovery=False)
    edits = service.edits()
    edit = edits.insert(packageName=PACKAGE, body={}).execute()
    edit_id = edit["id"]
    committed = False
    try:
        # Use the shared RibhLab developer support contact already published
        # on NovaGrid, but never duplicate NovaGrid-specific data practices.
        edits.details().patch(
            packageName=PACKAGE, editId=edit_id,
            body={"defaultLanguage": "en-US", "contactEmail": SUPPORT_EMAIL,
                  "contactWebsite": APP_WEBSITE},
        ).execute()
        existing = edits.listings().list(packageName=PACKAGE, editId=edit_id).execute()
        existing_langs = {l.get("language") for l in existing.get("listings", [])}
        # Preserve optional video and any other fields if present; do not touch other locales.
        for language, listing in doc["locales"].items():
            payload = {"language": language, **listing}
            if language in existing_langs:
                edits.listings().patch(
                    packageName=PACKAGE, editId=edit_id, language=language,
                    body=payload,
                ).execute()
            else:
                edits.listings().update(
                    packageName=PACKAGE, editId=edit_id, language=language,
                    body=payload,
                ).execute()
        icon = verify_icon(Path(__file__).parent / "store-listings/assets/rivoscan-icon.png")
        current_icons = edits.images().list(
            packageName=PACKAGE, editId=edit_id, language="en-US", imageType="icon",
        ).execute().get("images", [])
        if not current_icons:
            from PIL import Image
            with tempfile.TemporaryDirectory() as directory:
                rgba_icon = Path(directory) / "rivoscan-play-icon-32bit.png"
                with Image.open(icon) as image:
                    image.convert("RGBA").save(rgba_icon)
                edits.images().upload(
                    packageName=PACKAGE, editId=edit_id, language="en-US", imageType="icon",
                    media_body=MediaFileUpload(str(rgba_icon), mimetype="image/png"),
                ).execute()
        # No screenshots are uploaded without genuine, checked UI captures.
        edits.validate(packageName=PACKAGE, editId=edit_id).execute()
        edits.commit(packageName=PACKAGE, editId=edit_id).execute()
        committed = True
        return {"result": "LISTINGS_COMMITTED", "appId": PACKAGE,
                "locales": sorted(doc["locales"].keys()),
                "icon": "checked_existing_or_uploaded_from_source",
                "developerContact": SUPPORT_EMAIL, "appWebsite": APP_WEBSITE,
                "privacyPolicyUrl": PRIVACY_POLICY_URL + " (must be entered in Console App content)"}
    finally:
        if not committed:
            try:
                edits.delete(packageName=PACKAGE, editId=edit_id).execute()
            except Exception:
                print("WARNING: uncommitted listing edit cleanup failed", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--file", default=str(Path(__file__).parent / "store-listings/rivoscan.json"))
    p.add_argument("--apply", action="store_true", help="Commit store listing text to Google Play")
    p.add_argument("--confirm", default="", help="Must equal APPLY_LISTING when --apply is set")
    args = p.parse_args(argv)
    try:
        doc = load(Path(args.file))
        if not args.apply:
            print(json.dumps({"result": "LISTINGS_PREPARED_ONLY", "appId": PACKAGE,
                              "locales": {lang: {"title": data["title"],
                                  "shortDescription": data["shortDescription"]}
                                  for lang, data in doc["locales"].items()}},
                             ensure_ascii=False))
            return 0
        if args.confirm != "APPLY_LISTING":
            raise ValueError("Explicit --confirm APPLY_LISTING required")
        print(json.dumps(apply_listings(doc), ensure_ascii=False))
        return 0
    except Exception as exc:
        status = getattr(getattr(exc, "resp", None), "status", None)
        if isinstance(exc, ValueError):
            print(f"LISTING_BLOCKED: {exc}", file=sys.stderr)
        elif status in (401, 403, 404):
            print(f"LISTING_BLOCKED: Play API status {status}; check app creation and Play Console access", file=sys.stderr)
        else:
            print(f"LISTING_FAILED: {type(exc).__name__}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
