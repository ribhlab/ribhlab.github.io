#!/usr/bin/env python3
"""Replace only RivoScan en-US Google Play store graphics using verified owner images.

Source: owner's RivoScan Premium Blue v0.45.9 2026-11-13 ZIP, transferred
temporarily through a private Google Drive file shared only to Play's service
account. Requires exact ZIP and per-image SHA256 validation.
Does NOT upload AABs, change release tracks, listing text, Data Safety or ads.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

PACKAGE = "com.ribhlab.rivoscan"
LANGUAGE = "en-US"
DRIVE_FILE_ID = "16CZazPcj4HUIdOw4kXZv7kM8NEL96Ki_"
EXPECTED_ARCHIVE_SHA256 = "ce1ffed5dfeada53a8ba2be29b7519579de83db408ea92f40a1c3a10faab4a0c"
CONFIRM = "UPLOAD_RIVOSCAN_OWNER_PREMIUM_BLUE_STORE_IMAGES_ONLY"
ASSET_SHA256 = {
    "App_Icon_512x512.png": "251c061bce126e28290f296ca1abccbd75a764ac91d4de9dbc17883b6a2580ea",
    "Feature_Graphic_1024x500.png": "552ba63eb0a748059cc003c60ea847198c2818370eae016d81fda2c0501e606d",
    "Phone_01_Home_1080x1920.png": "11cabb56687ede9694bcc6e81d08fef5dd7bd941c0bb560215500335d4cd0f75",
    "Phone_02_Documents_1080x1920.png": "3f40dc3533786b4d1e223f1cc8f81f881e6b6892cb7d7377988a12cdb92cbfb3",
    "Phone_03_Tools_1080x1920.png": "5da14ba2ffa04064c0471f38b395ffabd9afd3f78615aa8d917a3b94f00167ae",
    "Phone_04_Book_Scan_1080x1920.png": "a61441f8e4e200dc21fe96f832271e6ae95f565b0484f87aba05a95c1681ff32",
    "Phone_05_Settings_1080x1920.png": "3ac7022b4bdaee48c0103ad12437cb582b1fc2d689bda13e807857b4a07ea272",
    "Phone_06_Photo_Translation_1080x1920.png": "6b668ccd0c1b1dce5a4d0b6f57bbb97bff047e1e4ba8a33678a6dcb82367a1e3",
    "Phone_07_Formula_OCR_1080x1920.png": "40df4fcfb74f4b2f3c4d3ac00962ecf7cba5337be21925dff8fde0848d0406bc",
    "Phone_08_ID_Photo_1080x1920.png": "69cce773ae774e31086b4142276832dd9c8f448acf475762958032ab429cdf7d",
}
SLOTS = {
    "icon": ("App_Icon_512x512.png",),
    "featureGraphic": ("Feature_Graphic_1024x500.png",),
    "phoneScreenshots": tuple(n for n in ASSET_SHA256 if n.startswith("Phone_")),
}


def inspect_archive(raw: bytes) -> dict[str, bytes]:
    from PIL import Image
    if hashlib.sha256(raw).hexdigest() != EXPECTED_ARCHIVE_SHA256:
        raise ValueError("Owner ZIP SHA-256 does not match approved attachment")
    with ZipFile(io.BytesIO(raw)) as z:
        allowed = set(ASSET_SHA256) | {"MANIFEST_SHA256.json"}
        if set(z.namelist()) != allowed or len(z.namelist()) != 11:
            raise ValueError("Unexpected files in approved store-only ZIP")
        manifest = json.loads(z.read("MANIFEST_SHA256.json").decode("utf-8"))
        if manifest != ASSET_SHA256:
            raise ValueError("Manifest disagrees with user-approved per-image hashes")
        images = {}
        for name, expected in ASSET_SHA256.items():
            data = z.read(name)
            if hashlib.sha256(data).hexdigest() != expected:
                raise ValueError("Image SHA-256 does not match user-supplied source: " + name)
            if len(data) > 10 * 1024 * 1024 or not data.startswith(b"\x89PNG\r\n\x1a\n"):
                raise ValueError("Invalid or oversized Play PNG: " + name)
            with Image.open(io.BytesIO(data)) as im:
                dimensions = (512, 512) if name.startswith("App_") else (
                    (1024, 500) if name.startswith("Feature_") else (1080, 1920))
                if im.format != "PNG" or im.size != dimensions:
                    raise ValueError("Invalid Play image type/dimensions for " + name)
                im.verify()
            images[name] = data
        return images


def download_from_private_drive() -> bytes:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    credential_json = json.loads(os.environ["GOOGLE_PLAY_SERVICE_ACCOUNT_JSON"])
    email = credential_json.get("client_email", "")
    if not email.endswith(".gserviceaccount.com"):
        raise ValueError("Google Play service account identity is missing")
    # Service account email is not a credential; used only to share a temporary
    # Drive file as 'reader', not 'anyone with link'.
    print("RIVOSCAN_PRIVATE_ASSET_READER_EMAIL=" + email, flush=True)
    creds = service_account.Credentials.from_service_account_info(
        credential_json,
        scopes=["https://www.googleapis.com/auth/drive.readonly"])
    service = build("drive", "v3", credentials=creds, cache_discovery=False)
    meta = service.files().get(fileId=DRIVE_FILE_ID, fields="id,size,mimeType").execute()
    if meta.get("mimeType") != "application/zip" or int(meta.get("size", "0")) != 3114337:
        raise ValueError("Unexpected Drive archive size/type")
    return service.files().get_media(fileId=DRIVE_FILE_ID).execute()


def apply_images(images: dict[str, bytes]) -> dict:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from publish import get_credentials

    edits = build("androidpublisher", "v3", credentials=get_credentials(),
                  cache_discovery=False).edits()
    edit = edits.insert(packageName=PACKAGE, body={}).execute()
    eid = edit["id"]
    committed = False
    try:
        with TemporaryDirectory(prefix="rivoscan-blue-play-store-") as tmp:
            for name, raw in images.items():
                (Path(tmp) / name).write_bytes(raw)
            # ONLY images, only three exact imageType categories for en-US.
            # One edit commit is atomic; failure leaves published images unchanged.
            for image_type, names in SLOTS.items():
                edits.images().deleteall(
                    packageName=PACKAGE, editId=eid,
                    language=LANGUAGE, imageType=image_type).execute()
                for name in names:
                    edits.images().upload(
                        packageName=PACKAGE, editId=eid,
                        language=LANGUAGE, imageType=image_type,
                        media_body=MediaFileUpload(str(Path(tmp) / name),
                                                  mimetype="image/png", resumable=False)
                    ).execute()
                now = edits.images().list(
                    packageName=PACKAGE, editId=eid,
                    language=LANGUAGE, imageType=image_type).execute().get("images", [])
                if len(now) != len(names):
                    raise RuntimeError("Google Play image count mismatch for " + image_type)
        edits.validate(packageName=PACKAGE, editId=eid).execute()
        edits.commit(packageName=PACKAGE, editId=eid).execute()
        committed = True
        return {"result": "RIVOSCAN_BLUE_STORE_IMAGES_COMMITTED",
                "package": PACKAGE, "language": LANGUAGE,
                "icon": 1, "featureGraphic": 1, "phoneScreenshots": 8,
                "aabChanged": False, "tracksChanged": False,
                "listingTextChanged": False, "note": "Google Play may review store listing edits"}
    finally:
        if not committed:
            try:
                edits.delete(packageName=PACKAGE, editId=eid).execute()
            except Exception:
                print("WARNING: Could not clean up uncommitted RivoScan image edit", file=sys.stderr)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--apply", action="store_true")
    p.add_argument("--confirm", default="")
    args = p.parse_args(argv)
    if not args.apply:
        print("RIVOSCAN_BLUE_STORE_IMAGES_PREFLIGHT=" + json.dumps({
            "result": "PACKAGE_AND_HASH_RULES_READY", "package": PACKAGE,
            "imageCount": len(ASSET_SHA256), "slots": {k:len(v) for k,v in SLOTS.items()},
            "archiveSha256": EXPECTED_ARCHIVE_SHA256}, sort_keys=True))
        return 0
    if args.confirm != CONFIRM:
        print("RIVOSCAN_BLUE_IMAGES_BLOCKED: explicit owner approval required", file=sys.stderr)
        return 2
    try:
        images = inspect_archive(download_from_private_drive())
        result = apply_images(images)
        print("RIVOSCAN_BLUE_STORE_IMAGES_RESULT=" + json.dumps(result, sort_keys=True))
        return 0
    except Exception as exc:
        status = getattr(getattr(exc, "resp", None), "status", None)
        print("RIVOSCAN_BLUE_STORE_IMAGES_FAILED=" + json.dumps({
            "error": type(exc).__name__, "httpStatus": status,
            "result": "NO_PLAY_EDIT_COMMITTED"}, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
