#!/usr/bin/env python3
"""Atomic, brand-specific NovaGrid store listing update.

Store graphics and locale texts are supplied by the app owner in the 2026-11-08
Play Publishing Kit. Never uploads an AAB or changes a release track.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import sys
import tempfile
from pathlib import Path

from publish import get_credentials

PACKAGE = "com.novagrid.cosmicpuzzle"
ROOT = Path(__file__).resolve().parent / "store-listings"
LOCALES = {"en-US", "fr-FR", "ar"}
CONFIRM = "APPLY_OWNER_NOVAGRID_LISTING"
SHA256 = {
    "icon": "0032b482048561ff0199d8cc3eec1106219ad78e59c5c7f4bda07e3339a2f3ea",
    "feature": "5a179bb3736f4e73cffe1630fb643264d574683cff9435ccc7d5a669dd738b3d",
    "screen1": "09f00ff6adeb2fffcbc465ca4ff7a43cfc5bf28d72044c4b24ca2d6c62dd0435",
    "screen2": "437a2fa1e560307645eac3c6e5f9597c6c6e7118fc6a588ad51464e3684d5bab",
    "screen3": "fa04f4baf2e54d146aa61df951a7301f300f4e5e64e42ed93c9822f974355704",
    "screen4": "09edbb7a42c0575647470b2580b33e3c8274c735bba2fbeda0dfd7e46d960a15",
    "screen5": "deae6c664dd2d400498c6f4bdd4b664b3c04eda3ca7eaa32119576563b82f4b3",
    "screen6": "2cf9bad85c53d9930065dc4c682cf782b6ca0cedaedf15f63a168f74ff376da3",
    "screen7": "02313e431ce9bc3b17e13a9fa76415f3071c3cd25bca35c80a70d7b9af204e33",
}
SUPPORT_EMAIL = "rachid022note4@gmail.com"
APP_WEBSITE = "https://ribhlab.github.io/novagrid/"


def load_metadata():
    data = json.loads((ROOT / "novagrid.json").read_text(encoding="utf-8"))
    if data.get("appId") != PACKAGE or set(data.get("locales", {})) != LOCALES:
        raise ValueError("Unexpected NovaGrid application or language list")
    for language, listing in data["locales"].items():
        for field, limit in (("title", 30), ("shortDescription", 80), ("fullDescription", 4000)):
            value = listing.get(field)
            if not isinstance(value, str) or not value.strip() or len(value) > limit:
                raise ValueError(f"{language}: invalid {field}")
    return data


def verified_artwork():
    """Read exact owner-provided bytes, never re-encode files to different art."""
    from PIL import Image
    result = {}
    for name, expected_hash in SHA256.items():
        encoded = "".join(
            (ROOT / "novagrid-assets" / f"{name}.b64").read_text(encoding="ascii").splitlines()
        )
        raw = base64.b64decode(encoded, validate=True)
        if hashlib.sha256(raw).hexdigest() != expected_hash:
            raise ValueError(f"Unexpected {name} artwork hash")
        with Image.open(io.BytesIO(raw)) as im:
            required = (512, 512) if name == "icon" else (1024, 500) if name == "feature" else (1080, 1920)
            if im.size != required:
                raise ValueError(f"{name}: wrong image dimensions")
            expected_format = "PNG" if name == "icon" else "JPEG"
            if im.format != expected_format:
                raise ValueError(f"{name}: wrong image format")
            im.verify()
        result[name] = raw
    return result


def apply_listing(data, images):
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    api = build("androidpublisher", "v3", credentials=get_credentials(), cache_discovery=False)
    edits = api.edits()
    edit = edits.insert(packageName=PACKAGE, body={}).execute()
    eid = edit["id"]
    committed = False
    try:
        edits.details().patch(
            packageName=PACKAGE, editId=eid,
            body={"defaultLanguage": "en-US", "contactEmail": SUPPORT_EMAIL,
                  "contactWebsite": APP_WEBSITE},
        ).execute()
        current = edits.listings().list(packageName=PACKAGE, editId=eid).execute()
        current_languages = {x.get("language") for x in current.get("listings", [])}
        for language, fields in data["locales"].items():
            content = {key: fields[key] for key in ("title", "shortDescription", "fullDescription")}
            if language in current_languages:
                edits.listings().patch(
                    packageName=PACKAGE, editId=eid, language=language, body=content
                ).execute()
            else:
                edits.listings().update(
                    packageName=PACKAGE, editId=eid, language=language,
                    body={"language": language, **content},
                ).execute()
        with tempfile.TemporaryDirectory(prefix="novagrid-play-") as work:
            for name, raw in images.items():
                extension = ".png" if name == "icon" else ".jpg"
                path = Path(work) / f"{name}{extension}"
                path.write_bytes(raw)
            for image_type, names in (
                ("icon", ["icon"]),
                ("featureGraphic", ["feature"]),
                ("phoneScreenshots", [f"screen{i}" for i in range(1, 8)]),
            ):
                edits.images().deleteall(
                    packageName=PACKAGE, editId=eid, language="en-US", imageType=image_type
                ).execute()
                for name in names:
                    extension = ".png" if name == "icon" else ".jpg"
                    edits.images().upload(
                        packageName=PACKAGE, editId=eid, language="en-US", imageType=image_type,
                        media_body=MediaFileUpload(
                            str(Path(work) / f"{name}{extension}"),
                            mimetype="image/png" if name == "icon" else "image/jpeg",
                            resumable=False,
                        ),
                    ).execute()
        edits.validate(packageName=PACKAGE, editId=eid).execute()
        edits.commit(packageName=PACKAGE, editId=eid).execute()
        committed = True
        return {"result": "LISTING_COMMITTED", "package": PACKAGE, "languages": sorted(LOCALES),
                "icon": "owner_supplied_verified", "featureGraphic": "owner_supplied_verified",
                "phoneScreenshots": 7, "aabUploaded": False, "productionPublished": False}
    finally:
        if not committed:
            try:
                edits.delete(packageName=PACKAGE, editId=eid).execute()
            except Exception:
                print("WARNING: could not discard uncommitted NovaGrid Play edit", file=sys.stderr)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm", default="")
    args = parser.parse_args(argv)
    try:
        data = load_metadata()
        images = verified_artwork()
        if not args.apply:
            print("NOVAGRID_ARTWORK_CHECK=" + json.dumps(
                {"result": "VALIDATED_OFFLINE", "package": PACKAGE,
                 "languages": sorted(LOCALES), "assets": sorted(images)}, sort_keys=True))
            return 0
        if args.confirm != CONFIRM:
            raise ValueError("Exact NovaGrid owner confirmation required")
        result = apply_listing(data, images)
        print("NOVAGRID_PLAY_LISTING=" + json.dumps(result, sort_keys=True))
        return 0
    except Exception as exc:
        status = getattr(getattr(exc, "resp", None), "status", None)
        print("NOVAGRID_PLAY_LISTING_ERROR=" + json.dumps(
            {"error": type(exc).__name__, "httpStatus": status,
             "committed": False}, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
