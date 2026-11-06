#!/usr/bin/env python3
"""Replace RivoScan's Play feature graphic with the artwork supplied by the owner.

Only one image in en-US is touched, atomically through a Google Play Edit.
No release, App Content declaration or other asset is modified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

PACKAGE = "com.ribhlab.rivoscan"
SOURCE = Path(__file__).resolve().parent / "store-listings/assets/rivoscan-user-feature-1024x500.jpg"
EXPECTED_SHA256 = "e52f3849d0dff618b8a19ecb42b595d316e4f05c8520e6dd7cead425d5cd9bbd"
OUTPUT = Path(__file__).resolve().parent / "output/RivoScan_Feature_Graphic_1024x500.jpg"


def prepare(path: Path) -> dict:
    from PIL import Image

    data = SOURCE.read_bytes()
    actual_hash = hashlib.sha256(data).hexdigest()
    if actual_hash != EXPECTED_SHA256:
        raise ValueError("RivoScan owner-provided image hash mismatch")
    with Image.open(SOURCE) as im:
        if im.format != "JPEG" or im.mode != "RGB" or im.size != (1024, 500):
            raise ValueError("Feature graphic must be 1024x500 RGB JPEG without alpha")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.resolve() != SOURCE.resolve():
        shutil.copyfile(SOURCE, path)
    return {"file": str(path), "sha256": actual_hash, "size": len(data), "dimensions": "1024x500"}


def replace_image(path: Path) -> dict:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from publish import get_credentials

    edits = build("androidpublisher", "v3", credentials=get_credentials(),
                  cache_discovery=False).edits()
    edit = edits.insert(packageName=PACKAGE, body={}).execute()
    eid = edit["id"]
    committed = False
    try:
        previous = edits.images().list(
            packageName=PACKAGE, editId=eid, language="en-US",
            imageType="featureGraphic").execute().get("images", [])
        # Replace existing feature-graphic images ONLY, within an uncommitted edit.
        # The original listing remains unchanged if validation or upload fails.
        edits.images().deleteall(
            packageName=PACKAGE, editId=eid, language="en-US",
            imageType="featureGraphic").execute()
        edits.images().upload(
            packageName=PACKAGE, editId=eid, language="en-US",
            imageType="featureGraphic",
            media_body=MediaFileUpload(str(path), mimetype="image/jpeg",
                                      resumable=False)).execute()
        now = edits.images().list(
            packageName=PACKAGE, editId=eid, language="en-US",
            imageType="featureGraphic").execute().get("images", [])
        if len(now) != 1:
            raise RuntimeError("Google Play did not return exactly one replacement feature graphic")
        edits.validate(packageName=PACKAGE, editId=eid).execute()
        edits.commit(packageName=PACKAGE, editId=eid).execute()
        committed = True
        return {"result": "USER_FEATURE_GRAPHIC_REPLACED",
                "package": PACKAGE, "language": "en-US",
                "previousCount": len(previous), "newCount": len(now),
                "sha256": EXPECTED_SHA256}
    finally:
        if not committed:
            try:
                edits.delete(packageName=PACKAGE, editId=eid).execute()
            except Exception:
                print("WARNING: could not remove uncommitted Google Play edit",
                      file=sys.stderr)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm", default="")
    parser.add_argument("--output", default=str(OUTPUT))
    args = parser.parse_args(argv)
    try:
        data = prepare(Path(args.output))
        if not args.apply:
            print(json.dumps({"result": "USER_FEATURE_GRAPHIC_PREPARED", **data}))
            return 0
        if args.confirm != "UPLOAD_FEATURE_GRAPHIC":
            raise ValueError("Explicit UPLOAD_FEATURE_GRAPHIC confirmation required")
        print(json.dumps(replace_image(Path(args.output)), ensure_ascii=False))
        return 0
    except Exception as exc:
        status = getattr(getattr(exc, "resp", None), "status", None)
        print(f"USER_FEATURE_GRAPHIC_FAILED: {type(exc).__name__}; HTTP={status}",
              file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
