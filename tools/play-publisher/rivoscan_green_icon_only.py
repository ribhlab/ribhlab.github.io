#!/usr/bin/env python3
"""Replace ONLY the RivoScan Play Store icon with the owner-approved green icon.

This does not modify the feature graphic (already green), any screenshots, AAB,
testing track, store listing text, or legal declarations. It does not require a
saved AAB, but Google Play may reject edits before first Play release setup.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
import tempfile
from pathlib import Path

PACKAGE = "com.ribhlab.rivoscan"
LANGUAGE = "en-US"
SOURCE = Path(__file__).resolve().parent / "store-listings/assets/rivoscan-icon.png"
EXPECTED_HASH = "67cd03f1d7e91e50ed398cc03c0a77482721e23053831df13984dbe3dffd9ce3"
CONFIRM = "REPLACE_RIVOSCAN_BLUE_ICON_WITH_OWNER_GREEN"


def verify_icon(path: Path = SOURCE) -> dict:
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED_HASH:
        raise ValueError("Unexpected icon: owner-approved green source SHA256 mismatch")
    if len(raw) > 1024 * 1024 or raw[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Play icon must be PNG and <=1MiB")
    width, height = struct.unpack(">II", raw[16:24])
    if (width, height) != (512, 512):
        raise ValueError("Play icon must be 512 x 512")
    return {"package": PACKAGE, "language": LANGUAGE, "dimensions": "512x512",
            "sha256": EXPECTED_HASH, "bytes": len(raw)}


def apply_icon():
    from PIL import Image
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from publish import get_credentials

    verified = verify_icon()
    service = build("androidpublisher", "v3", credentials=get_credentials(), cache_discovery=False)
    edits = service.edits()
    edit = edits.insert(packageName=PACKAGE, body={}).execute()
    eid = edit["id"]
    committed = False
    try:
        with tempfile.TemporaryDirectory() as tmp:
            # RGBA PNG is accepted by Google Play image handling.
            converted = Path(tmp) / "RivoScan_owner_green_512x512.png"
            with Image.open(SOURCE) as source_image:
                if source_image.size != (512, 512):
                    raise ValueError("Owner source dimensions changed during conversion")
                source_image.convert("RGBA").save(converted, format="PNG")
            before = edits.images().list(
                packageName=PACKAGE, editId=eid,
                language=LANGUAGE, imageType="icon"
            ).execute().get("images", [])
            edits.images().deleteall(
                packageName=PACKAGE, editId=eid,
                language=LANGUAGE, imageType="icon"
            ).execute()
            edits.images().upload(
                packageName=PACKAGE, editId=eid,
                language=LANGUAGE, imageType="icon",
                media_body=MediaFileUpload(str(converted), mimetype="image/png",
                                           resumable=False),
            ).execute()
            after = edits.images().list(
                packageName=PACKAGE, editId=eid,
                language=LANGUAGE, imageType="icon"
            ).execute().get("images", [])
            if len(after) != 1:
                raise RuntimeError("Unexpected Play icon count after upload")
            edits.validate(packageName=PACKAGE, editId=eid).execute()
            edits.commit(packageName=PACKAGE, editId=eid).execute()
            committed = True
            return {"result": "GREEN_ICON_COMMITTED", **verified,
                    "previousIconCount": len(before), "currentIconCount": len(after),
                    "note": "Console may require review and refreshing saved listing page."}
    finally:
        if not committed:
            try:
                edits.delete(packageName=PACKAGE, editId=eid).execute()
            except Exception:
                print("WARNING: uncommitted Google Play icon edit could not be discarded",
                      file=sys.stderr)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--apply", action="store_true", help="Publish icon edit through Play API")
    p.add_argument("--confirm", default="")
    args = p.parse_args(argv)
    try:
        verified = verify_icon()
        if not args.apply:
            print("RIVOSCAN_GREEN_ICON=" + json.dumps(
                {"result": "VALIDATED_OFFLINE", **verified}, sort_keys=True))
            return 0
        if args.confirm != CONFIRM:
            raise ValueError("Explicit owner green icon confirmation required")
        print("RIVOSCAN_GREEN_ICON=" + json.dumps(apply_icon(), sort_keys=True))
        return 0
    except Exception as exc:
        status = getattr(getattr(exc, "resp", None), "status", None)
        print("RIVOSCAN_GREEN_ICON_BLOCKED=" + json.dumps({
            "error": type(exc).__name__, "httpStatus": status,
            "note": "No Play edit committed on failure; check first upload, permissions, and pending Console edit."
        }, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
