#!/usr/bin/env python3
"""Update ONLY RivoNFC initial Play listing with signed-build screenshots."""
import hashlib
import json
import math
import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from publish import get_credentials

PACKAGE = "com.ribhlab.rivonfc"
HERE = Path(__file__).resolve().parent
INPUTS = HERE / "rivonfc-061-input"
SHOTS = {
    "RivoNFC-0.6.1-real-scan.png": "1d03ffdafc4771ffc99f714f857342c1783eac8151c869a759ba61411a1b2084",
    "RivoNFC-0.6.1-real-write.png": "06cbcd5e24029318f5c9671036178842fb30e6011e57d650cd0405eb9a1b4031",
    "RivoNFC-0.6.1-real-tools.png": "707132d0925d9a9c809efa6f1eb1a1c08c7e159d9d6177755f8f5b9b2a1801c1",
    "RivoNFC-0.6.1-real-history.png": "4ffbc30a39653c8687cf8b0a7a8ac1b404496bf77fc95a0d7a860b363f551a0a",
}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def fnt(size, bold=False):
    path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    return ImageFont.truetype(path, size)

def create_visuals():
    images = []
    for filename, digest in SHOTS.items():
        source = INPUTS / filename
        if not source.exists() or sha(source) != digest:
            raise RuntimeError("Screenshot source hash mismatch: " + filename)
        with Image.open(source) as pic:
            if pic.width < 320 or pic.height < 600 or pic.height > 3840 or pic.width > pic.height:
                raise RuntimeError("Unexpected screenshot geometry: " + filename)
            frame = pic.convert("RGB")
        if frame.height > 2 * frame.width:
            width = math.ceil(frame.height * 9 / 16)
            padded = Image.new("RGB", (width, frame.height), "#073038")
            padded.paste(frame, ((width - frame.width) // 2, 0))
            frame = padded
        dest = INPUTS / ("phone-%02d.png" % (len(images) + 1))
        frame.save(dest, "PNG", optimize=True)
        images.append(dest)
    if len({sha(p) for p in images}) < 3:
        raise RuntimeError("Screenshots must show different actual app screens")
    source_icon = INPUTS / "icon-512.png"
    with Image.open(source_icon) as picture:
        if picture.size != (512, 512):
            raise RuntimeError("Icon must be 512x512")
        icon = picture.convert("RGBA")
    icon.save(source_icon)
    canvas = Image.new("RGB", (1024, 500), "#082a38")
    dr = ImageDraw.Draw(canvas)
    for y in range(500):
        t = y / 500
        dr.line([(0, y), (1024, y)], fill=(int(9 + 5*t), int(35 + 22*t), int(51 + 25*t)))
    for rr in (115, 170, 225, 280):
        dr.arc((250-rr, 250-rr, 250+rr, 250+rr), -58, 74, fill=(27, 131, 122), width=3)
    dr.rounded_rectangle((56, 52, 432, 445), radius=63, fill=(13, 75, 79), outline=(57, 173, 153), width=3)
    resized = icon.resize((340, 340), Image.Resampling.LANCZOS)
    canvas.paste(resized, (73, 77), resized)
    dr.text((475, 125), "RivoNFC", font=fnt(76, True), fill="#f0fff9")
    dr.text((479, 243), "Read  •  Write  •  Inspect", font=fnt(29, True), fill="#86e8d6")
    dr.text((479, 292), "NFC tools, private and offline", font=fnt(22), fill="#e3f5f1")
    dr.rounded_rectangle((476, 375, 861, 435), radius=20, fill="#137a6a")
    dr.text((503, 390), "NFC TOOLS FOR ANDROID", font=fnt(19, True), fill="#eafff9")
    feature = INPUTS / "feature-1024x500.jpg"
    canvas.save(feature, "JPEG", quality=94, subsampling=0)
    print("RIVONFC_MEDIA_CHECK=" + json.dumps({"screenshots": len(images), "icon": icon.size, "feature": canvas.size}), flush=True)
    return source_icon, feature, images

def publish():
    if os.getenv("RIVONFC_APPROVAL") != "PUBLISH_RIVONFC_061_INITIAL_STORE_LISTING":
        raise RuntimeError("Missing exact owner authorization")
    doc = json.loads((HERE / "rivonfc-061-listing.json").read_text(encoding="utf-8"))
    if doc.get("appId") != PACKAGE or doc.get("versionCode") != 8:
        raise RuntimeError("Unexpected application ID / versionCode")
    if set(doc["locales"]) != {"en-US", "fr-FR", "ar"}:
        raise RuntimeError("Unexpected store locales")
    for lang, payload in doc["locales"].items():
        for key, limit in (("title", 30), ("shortDescription", 80), ("fullDescription", 4000)):
            value = payload.get(key, "")
            if not 0 < len(value) <= limit or "http://" in value or "https://" in value:
                raise RuntimeError("Invalid text length or URL: " + lang + " " + key)
    icon, feature, images = create_visuals()
    api = build("androidpublisher", "v3", credentials=get_credentials(), cache_discovery=False)
    edits = api.edits()
    edit_id = edits.insert(packageName=PACKAGE, body={}).execute()["id"]
    kw = {"packageName": PACKAGE, "editId": edit_id}
    committed = False
    try:
        bundles = edits.bundles().list(**kw).execute().get("bundles", [])
        if bundles:
            raise RuntimeError("Bundle already present; a concurrent publisher may be active")
        existing = edits.listings().list(**kw).execute().get("listings", [])
        langs = {item["language"] for item in existing}
        edits.details().patch(**kw, body={
            "defaultLanguage": "en-US",
            "contactEmail": "rachid022note4@gmail.com",
            "contactWebsite": "https://ribhlab.github.io/rivonfc/",
        }).execute()
        for lang, content in doc["locales"].items():
            body = {"language": lang, **content}
            if lang in langs:
                edits.listings().patch(**kw, language=lang, body=body).execute()
            else:
                edits.listings().update(**kw, language=lang, body=body).execute()
        for kind, paths, mime in (
            ("icon", [icon], "image/png"),
            ("featureGraphic", [feature], "image/jpeg"),
            ("phoneScreenshots", images, "image/png"),
        ):
            existing_images = edits.images().list(**kw, language="en-US", imageType=kind).execute().get("images", [])
            if existing_images:
                raise RuntimeError("Existing RivoNFC Play images found; avoid overwriting: " + kind)
            for image in paths:
                reply = edits.images().upload(**kw, language="en-US", imageType=kind,
                    media_body=MediaFileUpload(str(image), mimetype=mime)).execute()
                print("RIVONFC_IMAGE_ADDED=" + json.dumps({"type": kind, "name": image.name, "id": reply.get("id")}), flush=True)
        edits.validate(**kw).execute()
        edits.commit(**kw).execute()
        committed = True
        print("RIVONFC_LISTING_COMMITTED=" + json.dumps({
            "appId": PACKAGE, "languages": list(doc["locales"]), "genuineScreenshots": len(images),
            "tracksChanged": False, "existingMediaPreserved": True
        }), flush=True)
    finally:
        if not committed:
            try:
                edits.delete(**kw).execute()
            except Exception as cleanup:
                print("EDIT_CLEANUP_WARNING=" + str(cleanup)[:100], file=sys.stderr)

if __name__ == "__main__":
    try:
        publish()
    except Exception as exc:
        print("RIVONFC_LISTING_FAILED=" + json.dumps({
            "error": type(exc).__name__, "reason": str(exc)[:430]
        }), file=sys.stderr, flush=True)
        sys.exit(1)
