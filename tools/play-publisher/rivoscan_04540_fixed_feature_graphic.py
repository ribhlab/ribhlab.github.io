#!/usr/bin/env python3
"""Replace only RivoScan's en-US Play Store feature graphic with approved, crop-safe design.

The banner includes actual 0.45.40 app UI captures; it is not a fabricated app screen.
No changes to app title, descriptions, release name, notes, screenshots, icon, AAB, or tracks.
"""
import hashlib
import io
import json
import sys
import tempfile
from pathlib import Path
from urllib.request import Request, urlopen

from PIL import Image
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from publish import get_credentials

PACKAGE = "com.ribhlab.rivoscan"
LANGUAGE = "en-US"
IMAGE_TYPE = "featureGraphic"
SOURCE_VERSION = "0.45.40"
IMAGE_URL = "https://gcdn.picsart.com/picsart-mcp/0bb5fc4d-ec5c-489a-a03e-504bf2721e86.png"
EXPECTED_SHA256 = "7374bda99d56a9b1688b95a4786a3311e1c716245f1a70fb0308a8c9c21145f1"

def main():
    with urlopen(Request(IMAGE_URL, headers={"User-Agent": "RivoScan-FeatureGraphic-Publisher/1.0"}), timeout=60) as response:
        raw = response.read(2_000_001)
    actual = hashlib.sha256(raw).hexdigest()
    if actual != EXPECTED_SHA256:
        raise ValueError("Feature graphic bytes do not match the owner-approved image")
    with Image.open(io.BytesIO(raw)) as im:
        if im.format != "PNG" or im.size != (1024, 500):
            raise ValueError("Invalid Google Play feature graphic dimensions or format")
        im.verify()

    service = build("androidpublisher", "v3", credentials=get_credentials(), cache_discovery=False)
    edits = service.edits()
    edit_id = edits.insert(packageName=PACKAGE, body={}).execute()["id"]
    committed = False
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "RivoScan-04540-Feature-Graphic.png"
            path.write_bytes(raw)
            edits.images().deleteall(
                packageName=PACKAGE, editId=edit_id, language=LANGUAGE, imageType=IMAGE_TYPE
            ).execute()
            edits.images().upload(
                packageName=PACKAGE, editId=edit_id, language=LANGUAGE, imageType=IMAGE_TYPE,
                media_body=MediaFileUpload(str(path), mimetype="image/png", resumable=False)
            ).execute()
        images = edits.images().list(
            packageName=PACKAGE, editId=edit_id, language=LANGUAGE, imageType=IMAGE_TYPE
        ).execute().get("images", [])
        if len(images) != 1:
            raise RuntimeError("Expected exactly one new feature graphic in the Play edit")
        edits.validate(packageName=PACKAGE, editId=edit_id).execute()
        edits.commit(packageName=PACKAGE, editId=edit_id).execute()
        committed = True
        print("RIVOSCAN_04540_FEATURE_GRAPHIC_COMMITTED=" + json.dumps({
            "result": "COMMITTED",
            "package": PACKAGE,
            "language": LANGUAGE,
            "imageType": IMAGE_TYPE,
            "sourceVersion": SOURCE_VERSION,
            "sha256": EXPECTED_SHA256,
            "imageCount": 1,
            "dimensions": [1024, 500],
            "screenshotsChanged": False,
            "iconChanged": False,
            "aabChanged": False,
            "releaseTracksChanged": False,
            "listingTextChanged": False,
            "reviewMayBeRequired": True
        }), flush=True)
    finally:
        if not committed:
            try:
                edits.delete(packageName=PACKAGE, editId=edit_id).execute()
            except Exception:
                pass

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("RIVOSCAN_04540_FEATURE_GRAPHIC_FAILED=" + json.dumps({
            "type": type(exc).__name__,
            "message": str(exc)[:350],
            "httpStatus": getattr(getattr(exc, "resp", None), "status", None)
        }), file=sys.stderr, flush=True)
        raise SystemExit(1)
