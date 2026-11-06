#!/usr/bin/env python3
"""Safely upload screenshots captured from the actual Android RivoScan emulator.

The release screenshot archive is separately reviewed. This tool neither
generates mock screenshots nor modifies binaries, ads or legal declarations.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path
from zipfile import ZipFile

PACKAGE = "com.ribhlab.rivoscan"
ARCHIVE = Path(__file__).parent / "store-listings/assets/rivoscan-real-screenshots.zip"
SELECTED = (
    "01-rivoscan-home.png",
    "02-rivoscan-tools.png",
    "03-rivoscan-more-tools.png",
    "04-rivoscan-documents.png",
)


def prepare(directory: Path) -> list[Path]:
    from PIL import Image, ImageChops, ImageStat

    if not ARCHIVE.exists():
        raise ValueError("Missing source archive of real Android emulator screenshots")
    outputs = []
    fingerprints = set()
    with ZipFile(ARCHIVE) as z:
        available = {Path(n).name: n for n in z.namelist() if n.endswith(".png")}
        for name in SELECTED:
            if name not in available:
                raise ValueError("Required Android emulator screenshot missing: " + name)
            data = z.read(available[name])
            fingerprint = hashlib.sha256(data).hexdigest()
            if fingerprint in fingerprints:
                raise ValueError("Duplicate screenshot content: " + name)
            fingerprints.add(fingerprint)
            target = directory / name.replace(".png", ".jpg")
            from io import BytesIO
            with Image.open(BytesIO(data)) as im:
                if im.format != "PNG" or im.size != (1080, 1920):
                    raise ValueError("Unexpected screenshot dimensions/formats for " + name)
                rgb = im.convert("RGB")
                extrema = rgb.getextrema()
                if all(low == high for low, high in extrema):
                    raise ValueError("Blank screenshot " + name)
                rgb.save(target, "JPEG", quality=94, optimize=True, subsampling=0)
            outputs.append(target)
    return outputs


def upload(images: list[Path]) -> dict:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from publish import get_credentials

    edits = build("androidpublisher", "v3", credentials=get_credentials(),
                  cache_discovery=False).edits()
    edit = edits.insert(packageName=PACKAGE, body={}).execute()
    eid = edit["id"]
    committed = False
    try:
        existing = edits.images().list(packageName=PACKAGE, editId=eid,
                 language="en-US", imageType="phoneScreenshots").execute().get("images", [])
        if existing:
            return {"result": "EXISTING_SCREENSHOTS_PRESERVED", "count": len(existing)}
        for pic in images:
            edits.images().upload(
                packageName=PACKAGE, editId=eid,
                language="en-US", imageType="phoneScreenshots",
                media_body=MediaFileUpload(str(pic), mimetype="image/jpeg",
                                           resumable=False)).execute()
        after = edits.images().list(packageName=PACKAGE, editId=eid,
                 language="en-US", imageType="phoneScreenshots").execute().get("images", [])
        if len(after) != len(images):
            raise RuntimeError("Google Play did not return expected screenshot count")
        edits.validate(packageName=PACKAGE, editId=eid).execute()
        edits.commit(packageName=PACKAGE, editId=eid).execute()
        committed = True
        return {"result": "REAL_ANDROID_SCREENSHOTS_COMMITTED", "count": len(after),
                "package": PACKAGE, "language": "en-US",
                "source": "RivoScan Android 14 emulator, 1080x1920"}
    finally:
        if not committed:
            try:
                edits.delete(packageName=PACKAGE, editId=eid).execute()
            except Exception:
                print("WARNING: uncommitted Play edit cleanup failed", file=sys.stderr)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--apply", action="store_true")
    p.add_argument("--confirm", default="")
    args = p.parse_args(argv)
    try:
        with tempfile.TemporaryDirectory() as d:
            screenshots = prepare(Path(d))
            if not args.apply:
                print(json.dumps({"result": "REAL_SCREENSHOTS_PREPARED_ONLY",
                                  "count": len(screenshots),
                                  "names": [p.name for p in screenshots]}))
                return 0
            if args.confirm != "UPLOAD_REAL_SCREENSHOTS":
                raise ValueError("Explicit UPLOAD_REAL_SCREENSHOTS confirmation required")
            print(json.dumps(upload(screenshots)))
            return 0
    except Exception as exc:
        status = getattr(getattr(exc, "resp", None), "status", None)
        print(f"REAL_SCREENSHOT_UPLOAD_FAILED: {type(exc).__name__}, HTTP={status}",
              file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
