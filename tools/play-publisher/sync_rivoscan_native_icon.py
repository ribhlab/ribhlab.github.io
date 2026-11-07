#!/usr/bin/env python3
"""Synchronize the REAL Android launcher icon with the RivoScan Play Store icon.

The associated workflow generates this icon from
univcours/ribhlab:apps/rivoscan/scripts/create-turquoise-icon.mjs,
which is also called by the Android release branding script.

Only en-US and *existing explicitly localized* app icons can be touched.
No AAB, screenshots, descriptions, feature graphics or tracks are changed.
Run without --apply for an entirely offline validation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

PACKAGE = "com.ribhlab.rivoscan"
LOCALES = ("en-US", "fr-FR", "ar", "es-ES", "de-DE", "pt-BR", "it-IT")
CONFIRM = "SYNC_NATIVE_ICON"


def inspect_icon(path: Path) -> dict:
    blob = path.read_bytes()
    if not 100 <= len(blob) <= 1024 * 1024 or blob[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Native icon must be a PNG smaller than 1 MiB")
    width, height = struct.unpack(">II", blob[16:24])
    if (width, height) != (512, 512):
        raise ValueError("Native icon must be 512 x 512 pixels")
    if blob[24] != 8 or blob[25] != 6:
        raise ValueError("Native icon must use 8-bit RGBA PNG")
    return {"pixels": "512x512", "bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest()}


def is_matching(images: list[dict], sha256: str) -> bool:
    return len(images) == 1 and images[0].get("sha256", "").casefold() == sha256.casefold()


def select_locales(existing: set[str], icons_by_locale: dict[str, list]) -> list[str]:
    """Only add/replace the default icon and existing custom localized icons."""
    if "en-US" not in existing:
        raise ValueError("Default en-US Play Store listing is unavailable")
    return [locale for locale in LOCALES
            if locale in existing and (locale == "en-US" or bool(icons_by_locale.get(locale)))]


def upload_icon(path: Path, sha256: str, service) -> dict:
    from googleapiclient.http import MediaFileUpload
    edits = service.edits()
    edit_id = edits.insert(packageName=PACKAGE, body={}).execute()["id"]
    committed = False
    try:
        present = edits.listings().list(packageName=PACKAGE, editId=edit_id).execute()
        existing = {listing.get("language") for listing in present.get("listings", [])}
        images_by_locale: dict[str, list] = {}
        for locale in LOCALES:
            if locale not in existing:
                continue
            images_by_locale[locale] = edits.images().list(
                packageName=PACKAGE, editId=edit_id, language=locale,
                imageType="icon").execute().get("images", [])
        locales = select_locales(existing, images_by_locale)
        changed = []
        for locale in locales:
            images = images_by_locale.get(locale, [])
            if is_matching(images, sha256):
                continue
            # Both operations take place inside ONE uncommitted Play edit.
            # A failure leaves the previously committed image untouched.
            if images:
                edits.images().deleteall(
                    packageName=PACKAGE, editId=edit_id, language=locale,
                    imageType="icon").execute()
            edits.images().upload(
                packageName=PACKAGE, editId=edit_id, language=locale,
                imageType="icon",
                media_body=MediaFileUpload(str(path), mimetype="image/png")).execute()
            after = edits.images().list(
                packageName=PACKAGE, editId=edit_id, language=locale,
                imageType="icon").execute().get("images", [])
            if len(after) != 1:
                raise RuntimeError("Google Play did not retain exactly one icon for " + locale)
            changed.append(locale)
        if not changed:
            return {"result": "ALREADY_MATCHING", "package": PACKAGE,
                    "iconSha256": sha256, "localesChecked": locales}
        edits.validate(packageName=PACKAGE, editId=edit_id).execute()
        edits.commit(packageName=PACKAGE, editId=edit_id).execute()
        committed = True
        return {"result": "NATIVE_ICON_COMMITTED", "package": PACKAGE,
                "iconSha256": sha256, "updatedLocales": changed,
                "localesChecked": locales}
    finally:
        if not committed:
            try:
                edits.delete(packageName=PACKAGE, editId=edit_id).execute()
            except Exception:
                print("WARNING: uncommitted Google Play edit cleanup failed", file=sys.stderr)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--icon", required=True, type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm", default="")
    args = parser.parse_args(argv)
    try:
        metadata = inspect_icon(args.icon)
        if not args.apply:
            print(json.dumps({"result": "NATIVE_ICON_PREPARED_ONLY",
                              "package": PACKAGE, **metadata}))
            return 0
        if args.confirm != CONFIRM:
            raise ValueError("Google Play update requires --confirm SYNC_NATIVE_ICON")
        from googleapiclient.discovery import build
        from publish import get_credentials
        result = upload_icon(args.icon, metadata["sha256"],
                             build("androidpublisher", "v3",
                                   credentials=get_credentials(), cache_discovery=False))
        print(json.dumps(result, sort_keys=True))
        return 0
    except Exception as exc:
        status = getattr(getattr(exc, "resp", None), "status", None)
        if isinstance(exc, ValueError):
            print("ICON_BLOCKED: " + str(exc), file=sys.stderr)
        elif status in (401, 403, 404, 409):
            print(f"ICON_BLOCKED: Play API HTTP {status}", file=sys.stderr)
        else:
            print("ICON_FAILED: " + type(exc).__name__, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
