#!/usr/bin/env python3
"""Add the owner's verified 7/10-inch RivoScan screenshots to Google Play (en-US).

Images are from the owner-provided 16-PNG ZIP. Writes ONLY two tablet image
types; never touches phone screenshots, icon, graphics, AAB, track or text.
Fails without a Play edit commit if either tablet slot is already occupied.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from zipfile import ZipFile

PACKAGE = "com.ribhlab.rivoscan"
LANGUAGE = "en-US"
ZIP_URL = "https://gcdn.picsart.com/picsart-mcp/b5289558-0299-46d9-8467-92907662e1cb.zip"
ZIP_SHA256 = "db2c127f99bf08176aba0bcf7bed02e5f04b47757cd543374c85753414edbdfe"
CONFIRM = "UPLOAD_RIVOSCAN_TABLET_IMAGES_ONLY"
ASSET_SHA256 = {
    "7-inch/01_Home.png": "22211a430a86b494e51862a5645fe2e498884de44388dc376ec35f0a49819f6f",
    "7-inch/02_Documents.png": "1a43a1593bcdcc89933ee0bf7ea76e1ad0a887955c90893b4c433c08f9045d00",
    "7-inch/03_Tools.png": "fa59fc34a9a977b1b9fbb2d30b3fbfc51133bdef4edf7ec5f086ecf3411d2fa2",
    "7-inch/04_Book_Scan.png": "f8ce4a154cd233cfa5eebeb104d77a7f0825a39431ad67b8814094ad63ea92cb",
    "7-inch/05_Formula_OCR.png": "23e1962af01b5361381b0c5186da1ba1b8c635fb2b6ad5106f8144d040fb4435",
    "7-inch/06_Photo_Translation.png": "c3c900175f202a5b139f3a7d0ecc007e09a4bbb94914a18e034c04a853d3e385",
    "7-inch/07_ID_Photo.png": "1290b76c4b07e0a683907b568b6888aaae50707e044b10e469bd852059caf041",
    "7-inch/08_Settings.png": "3caa87b722efdd6caeff71e41415a658726e3cfdd4ce5020106fe5375c963dba",
    "10-inch/01_Home.png": "0e2ca72247e67ede88d73c62b831dc28c39a493daecdb87ca1a626cf767474ea",
    "10-inch/02_Documents.png": "c47727a3dec8431d2b3fe207bd5b3d98d140a635fffdbbe67383e9f16bc86275",
    "10-inch/03_Tools.png": "fd2f2857e20de2bdec0adee319842f659ab1cba1a3ec2e0185ac2e6b51abdf18",
    "10-inch/04_Book_Scan.png": "12fe7d09dc75d9456598cb09423730be19d110f96e7b2b04eb86a3938e18ba4f",
    "10-inch/05_Formula_OCR.png": "809861d20cbd6e42f37ce4a8b0bac1c3fd4512f308091647d2e27a1ce4ded0ec",
    "10-inch/06_Photo_Translation.png": "d5d97879159be402b56617a369a0369184c7c1b7256fb144b8dae1a1c65f185e",
    "10-inch/07_ID_Photo.png": "5bca5bf5e9529125469e2149a1a4dc3c16224c400731780252fd362d76255cc4",
    "10-inch/08_Settings.png": "37a4d22d76ec627e83e72f97361a57fc1a269b53571a43f4ba33df2ad1fed753",
}
SLOTS = {
    "sevenInchScreenshots": [p for p in ASSET_SHA256 if p.startswith("7-inch/")],
    "tenInchScreenshots": [p for p in ASSET_SHA256 if p.startswith("10-inch/")],
}


def verify_zip(data: bytes) -> dict[str, bytes]:
    from PIL import Image

    if hashlib.sha256(data).hexdigest() != ZIP_SHA256:
        raise ValueError("Uploaded owner ZIP SHA-256 mismatch")
    with ZipFile(io.BytesIO(data)) as archive:
        if set(archive.namelist()) != set(ASSET_SHA256) | {"README.txt", "audit.json"}:
            raise ValueError("Unexpected items in owner tablet ZIP")
        approved: dict[str, bytes] = {}
        for name, sha in ASSET_SHA256.items():
            raw = archive.read(name)
            if len(raw) > 5_000_000 or hashlib.sha256(raw).hexdigest() != sha:
                raise ValueError("Owner image bytes/hash mismatch: " + name)
            if not raw.startswith(b"\x89PNG\r\n\x1a\n"):
                raise ValueError("Invalid PNG: " + name)
            with Image.open(io.BytesIO(raw)) as img:
                expected = (1080, 1920) if name.startswith("7-inch/") else (1440, 2560)
                if img.format != "PNG" or img.mode != "RGB" or img.size != expected:
                    raise ValueError("Invalid PNG dimensions/color: " + name)
                img.verify()
            approved[name] = raw
        return approved


def retrieve_verified_owner_assets() -> dict[str, bytes]:
    parsed = urlparse(ZIP_URL)
    if parsed.scheme != "https" or parsed.hostname != "gcdn.picsart.com" or parsed.query:
        raise ValueError("Unapproved asset delivery host")
    req = Request(ZIP_URL, headers={"User-Agent": "RivoScan-Tablet-Play-Asset-Check/1.0"})
    with urlopen(req, timeout=55) as response:
        data = response.read(12_000_001)
    if len(data) > 12_000_000:
        raise ValueError("ZIP unexpectedly large")
    return verify_zip(data)


def add_tablet_screenshots(images: dict[str, bytes]) -> dict:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from publish import get_credentials

    edits = build("androidpublisher", "v3", credentials=get_credentials(),
                  cache_discovery=False).edits()
    edit_id = edits.insert(packageName=PACKAGE, body={}).execute()["id"]
    committed = False
    try:
        # Never replace any user-existing tablet screenshots. Both slots must be empty.
        for image_type in SLOTS:
            current = edits.images().list(
                packageName=PACKAGE, editId=edit_id, language=LANGUAGE,
                imageType=image_type).execute().get("images", [])
            if current:
                raise RuntimeError(
                    f"{image_type} already contains {len(current)} images; refusing to replace/duplicate")
        with TemporaryDirectory(prefix="rivoscan-tablet-play-") as tmp:
            for image_type, names in SLOTS.items():
                for name in names:
                    local = Path(tmp) / Path(name).name
                    local.write_bytes(images[name])
                    edits.images().upload(
                        packageName=PACKAGE, editId=edit_id, language=LANGUAGE,
                        imageType=image_type,
                        media_body=MediaFileUpload(
                            str(local), mimetype="image/png", resumable=False)).execute()
                observed = edits.images().list(
                    packageName=PACKAGE, editId=edit_id, language=LANGUAGE,
                    imageType=image_type).execute().get("images", [])
                if len(observed) != 8:
                    raise RuntimeError(f"Wrong uploaded image count for {image_type}: {len(observed)}")
        edits.validate(packageName=PACKAGE, editId=edit_id).execute()
        edits.commit(packageName=PACKAGE, editId=edit_id).execute()
        committed = True
        return {
            "result": "RIVOSCAN_TABLET_IMAGES_COMMITTED", "package": PACKAGE,
            "language": LANGUAGE, "sevenInchScreenshots": 8, "tenInchScreenshots": 8,
            "phoneImagesChanged": False, "appIconChanged": False, "featureGraphicChanged": False,
            "aabChanged": False, "releaseTracksChanged": False, "listingTextChanged": False,
            "note": "Google Play listing updates may require review",
        }
    finally:
        if not committed:
            try:
                edits.delete(packageName=PACKAGE, editId=edit_id).execute()
            except Exception:
                print("WARNING: failed to discard uncommitted Play edit", file=sys.stderr)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm", default="")
    args = parser.parse_args(argv)
    if not args.apply:
        print("RIVOSCAN_TABLET_PREFLIGHT=" + json.dumps({
            "result": "READY", "package": PACKAGE, "count": len(ASSET_SHA256),
            "zipSha256": ZIP_SHA256, "slots": {k: len(v) for k, v in SLOTS.items()},
        }, sort_keys=True))
        return 0
    if args.confirm != CONFIRM:
        print("RIVOSCAN_TABLET_BLOCKED=missing explicit owner confirmation", file=sys.stderr)
        return 2
    try:
        images = retrieve_verified_owner_assets()
        print("RIVOSCAN_TABLET_VERIFIED_IMAGES=16", flush=True)
        result = add_tablet_screenshots(images)
        print("RIVOSCAN_TABLET_RESULT=" + json.dumps(result, sort_keys=True))
        return 0
    except Exception as exc:
        status = getattr(getattr(exc, "resp", None), "status", None)
        print("RIVOSCAN_TABLET_FAILED=" + json.dumps({
            "reason": type(exc).__name__, "description": str(exc)[:240],
            "httpStatus": status, "result": "NO_SUCCESSFUL_PLAY_COMMIT",
        }, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
