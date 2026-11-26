#!/usr/bin/env python3
"""Replace only RivoCaption 0.4.3 Play images with genuine emulator captures.

The original production-signed app must be installed and captured by
rivocaption_043_real_media.py. No synthetic Android UI or picker screenshots.
All changes are one validated, committed Play edit; failure aborts without commit.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path

from PIL import Image, ImageStat

PACKAGE = "com.rivocaption.editor"
VERSION_CODE = 17
FILES = [
    "phone-01-home.png",
    "phone-02-ai.png",
    "phone-03-styles.png",
    "phone-04-captions.png",
    "phone-05-export.png",
]
CONFIRM = "REPLACE_RIVOCAPTION_043_REAL_IMAGES"


def inspect_source(src: Path) -> dict[str, list[str]]:
    if not src.is_dir():
        raise ValueError("Genuine Android screenshot source folder missing")
    if not (src / "home.xml").is_file() or not (src / "after-import.xml").is_file():
        raise ValueError("Actual Android hierarchy evidence is missing")
    if "Your creative studio" not in (src / "home.xml").read_text(encoding="utf-8"):
        raise ValueError("Home hierarchy does not identify the genuine RivoCaption app")
    if not any(x in (src / "after-import.xml").read_text(encoding="utf-8")
               for x in ("Captions", "Styles", "Export")):
        raise ValueError("Video-editor hierarchy evidence missing")
    unique = set()
    for name in FILES:
        path = src / name
        raw = path.read_bytes()
        if len(raw) < 18000 or not raw.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError("Not a genuine full-resolution PNG screenshot: " + name)
        with Image.open(io.BytesIO(raw)) as im:
            if im.format != "PNG" or im.size != (1080, 1920):
                raise ValueError("Screenshot resolution mismatch: " + name)
            variation = max(ImageStat.Stat(im.convert("RGB").resize((120, 180))).stddev)
            if variation < 10:
                raise ValueError("Blank or uniform Android screenshot: " + name)
        digest = hashlib.sha256(raw).hexdigest()
        if digest in unique:
            raise ValueError("Duplicate screenshots are not allowed")
        unique.add(digest)
    for name, expected in [("icon.png", (512, 512)), ("feature.png", (1024, 500))]:
        with Image.open(src / name) as im:
            if im.format != "PNG" or im.size != expected:
                raise ValueError("Invalid approved store visual: " + name)
        if (src / name).stat().st_size > 1000000 and name == "icon.png":
            raise ValueError("App icon exceeds Play's 1MB limit")
    return {"icon": ["icon.png"], "featureGraphic": ["feature.png"], "phoneScreenshots": FILES}


def replace_images(src: Path, groups: dict[str, list[str]]) -> dict:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from publish import get_credentials

    api = build("androidpublisher", "v3", credentials=get_credentials(), cache_discovery=False)
    edits = api.edits()
    edit_id = edits.insert(packageName=PACKAGE, body={}).execute()["id"]
    common = {"packageName": PACKAGE, "editId": edit_id}
    committed = False
    try:
        bundles = edits.bundles().list(**common).execute().get("bundles", [])
        if VERSION_CODE not in {int(b["versionCode"]) for b in bundles}:
            raise RuntimeError("RivoCaption v0.4.3 AAB not present on Google Play")
        tracks = edits.tracks().list(**common).execute().get("tracks", [])
        production = next((t for t in tracks if t.get("track") == "production"), None)
        if not production or not any(
            str(VERSION_CODE) in r.get("versionCodes", []) and r.get("status") == "completed"
            for r in production.get("releases", [])
        ):
            raise RuntimeError("RivoCaption 0.4.3 is not the completed production release")
        listings = edits.listings().list(**common).execute().get("listings", [])
        locales = sorted({x["language"] for x in listings if x.get("language")})
        if "en-US" not in locales:
            raise RuntimeError("English store listing not available")
        print("PLAY_IMAGE_TARGET_LOCALES=" + json.dumps(locales), flush=True)
        for locale in locales:
            for kind, names in groups.items():
                edits.images().deleteall(**common, language=locale, imageType=kind).execute()
                for filename in names:
                    uploaded = edits.images().upload(
                        **common, language=locale, imageType=kind,
                        media_body=MediaFileUpload(
                            str(src / filename), mimetype="image/png", resumable=False
                        ),
                    ).execute(num_retries=3)
                    if not uploaded.get("image", {}).get("id"):
                        raise RuntimeError("Google Play did not confirm " + locale + "/" + filename)
                stored = edits.images().list(
                    **common, language=locale, imageType=kind
                ).execute().get("images", [])
                if len(stored) != len(names):
                    raise RuntimeError("Mismatched Play images: " + locale + "/" + kind)
                print("STORED=" + locale + " " + kind + " " + str(len(stored)), flush=True)
        edits.validate(**common).execute()
        edits.commit(**common).execute()
        committed = True
        return {"package": PACKAGE, "versionCode": VERSION_CODE,
                "locales": locales, "totalImages": len(locales) * sum(map(len, groups.values())),
                "productionReleased": True}
    finally:
        if not committed:
            try:
                edits.delete(**common).execute()
            except Exception:
                print("Warning: uncommitted images edit cleanup unsuccessful", flush=True)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--source", required=True, type=Path)
    p.add_argument("--apply", action="store_true")
    p.add_argument("--confirm", default="")
    args = p.parse_args()
    groups = inspect_source(args.source)
    print("REAL_MEDIA_VALIDATED=" + json.dumps(groups), flush=True)
    if args.apply:
        if args.confirm != CONFIRM:
            raise RuntimeError("Specific owner approval not provided")
        result = replace_images(args.source, groups)
        print("RIVOCAPTION_043_PLAY_IMAGES_COMMITTED=" + json.dumps(result), flush=True)
    else:
        print("DRY_RUN_ONLY: no Play image changes", flush=True)


if __name__ == "__main__":
    main()
