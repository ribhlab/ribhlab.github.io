#!/usr/bin/env python3
"""Capture unmodified real RivoSticker Android emulator screens and publish media.

This script never creates false app screenshots: all phone screenshot PNGs are
raw ADB screencap captures from the signed, running APK. Brand art is derived
from the app's actual packaged launcher icon, not a third-party mock app.
No release tracks or app bundles are changed.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageStat

PACKAGE = "com.ribhlab.rivosticker"
VERSION_CODE = 4
BASE = Path("/tmp/rivosticker-real")
LABELS = ("Home", "Gallery", "Packs", "Settings")


def adb(*args: str, binary: bool = False):
    result = subprocess.run(
        ["adb", *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=100,
        check=True,
    )
    return result.stdout if binary else result.stdout.decode("utf-8", "replace")


def ui_xml() -> ET.Element:
    adb("shell", "uiautomator", "dump", "/sdcard/rivosticker-window.xml")
    raw = adb("exec-out", "cat", "/sdcard/rivosticker-window.xml")
    start = raw.find("<?xml")
    if start < 0:
        raise ValueError("Android accessibility UI hierarchy not available")
    return ET.fromstring(raw[start:])


def bounds_center(bounds: str):
    nums = [int(s) for s in re.findall(r"\d+", bounds)]
    if len(nums) != 4:
        raise ValueError("Unexpected Android UI rectangle " + bounds)
    return ((nums[0] + nums[2]) // 2, (nums[1] + nums[3]) // 2)


def tap_label(label: str):
    hierarchy = ui_xml()
    candidates = []
    for node in hierarchy.iter("node"):
        attrs = node.attrib
        if attrs.get("text", "").strip().lower() == label.lower() or attrs.get("content-desc", "").strip().lower() == label.lower():
            if attrs.get("bounds"):
                x, y = bounds_center(attrs["bounds"])
                candidates.append((y, x, y))
    if not candidates:
        # Record on-device UI names only, no app personal content is exported.
        names = sorted({v for e in hierarchy.iter("node") for k, v in e.attrib.items()
                        if k in ("text", "content-desc") and 0 < len(v) < 70})
        raise ValueError(f"Could not locate native RivoSticker tab {label}; labels={names[:75]}")
    # Navigation tabs appear near the bottom; choose the lowest matching label.
    _, x, y = max(candidates)
    adb("shell", "input", "tap", str(x), str(y))
    time.sleep(2.5)


def verify_real_png(file: Path):
    raw = file.read_bytes()
    if not raw.startswith(b"\x89PNG\r\n\x1a\n") or len(raw) < 20_000:
        raise ValueError("Screenshot missing genuine PNG bytes " + file.name)
    with Image.open(io.BytesIO(raw)) as im:
        if im.size != (1080, 1920) or im.format != "PNG":
            raise ValueError(f"Real phone screen invalid dimensions {im.size}")
        im.load()
        # Screens must show actual app content, not uniform splash/dummy images.
        rgb = im.convert("RGB").resize((100, 180))
        if max(ImageStat.Stat(rgb).stddev) < 12:
            raise ValueError("Screenshot appears blank " + file.name)
    return hashlib.sha256(raw).hexdigest()


def capture(apk: Path, output: Path):
    output.mkdir(parents=True, exist_ok=True)
    adb("shell", "wm", "size", "1080x1920")
    adb("shell", "wm", "density", "440")
    adb("shell", "settings", "put", "system", "font_scale", "1.0")
    adb("shell", "svc", "wifi", "disable")
    adb("shell", "svc", "data", "disable")
    adb("install", "-r", str(apk))
    adb("shell", "am", "force-stop", PACKAGE)
    adb("shell", "am", "start", "-n", PACKAGE + "/.MainActivity")
    time.sleep(10)
    output_hashes = {}
    for index, label in enumerate(LABELS, start=1):
        if label != "Home":
            tap_label(label)
        else:
            ui_xml()  # fail rather than capture an Android permissions screen
        filename = f"phone-{index:02d}-{label.lower()}.png"
        path = output / filename
        path.write_bytes(adb("exec-out", "screencap", "-p", binary=True))
        output_hashes[filename] = verify_real_png(path)
        print("REAL_EMULATOR_CAPTURE=" + json.dumps({"label": label, "file": filename,
                                                       "sha256": output_hashes[filename]}), flush=True)
    if len(set(output_hashes.values())) != len(LABELS):
        raise RuntimeError("The 4 images are not unique actual app views; refusing to publish")
    return list(output_hashes)


def icon_from_apk(apk: Path, output: Path):
    with zipfile.ZipFile(apk) as z:
        names = z.namelist()
        candidates = [n for n in names if n.endswith("/ic_launcher.png")]
        candidates.sort(key=lambda n: (
            0 if "mipmap-nodpi" in n else 1 if "mipmap-xxxhdpi" in n else 2,
            len(n)))
        if not candidates:
            candidates = [n for n in names if n.endswith("/rivosticker_foreground.png")]
        if not candidates:
            raise ValueError("Official RivoSticker launcher icon is absent from release APK")
        raw = z.read(candidates[0])
    with Image.open(io.BytesIO(raw)) as img:
        rgba = img.convert("RGBA")
        if rgba.width < 100 or rgba.height < 100:
            raise ValueError("Packaged RivoSticker launcher artwork resolution too low")
        rgba.thumbnail((512, 512), Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (512, 512), "#162d5f")
        canvas.alpha_composite(rgba, ((512 - rgba.width) // 2, (512 - rgba.height) // 2))
        canvas.convert("RGB").save(output / "icon.png", "PNG")
    print("OFFICIAL_APK_ICON=" + candidates[0], flush=True)


def feature_from_icon(output: Path):
    bg = Image.new("RGB", (1024, 500))
    d = ImageDraw.Draw(bg)
    for y in range(500):
        ratio = y / 499
        c1, c2 = (10, 29, 70), (62, 43, 131)
        c = tuple(int(a + (b - a) * ratio) for a, b in zip(c1, c2))
        d.line((0, y, 1024, y), fill=c)
    with Image.open(output / "icon.png") as ic:
        small = ic.convert("RGBA").resize((290, 290), Image.Resampling.LANCZOS)
    bg.paste(small.convert("RGB"), (55, 102))
    font_dir = Path("/usr/share/fonts/truetype/dejavu")
    large = ImageFont.truetype(str(font_dir / "DejaVuSans-Bold.ttf"), 70)
    subtitle = ImageFont.truetype(str(font_dir / "DejaVuSans.ttf"), 34)
    d = ImageDraw.Draw(bg)
    d.text((380, 160), "RivoSticker", font=large, fill="#ffffff")
    d.text((385, 258), "Create. Edit. Share.", font=subtitle, fill="#e2e7ff")
    d.rounded_rectangle((388, 346, 850, 397), radius=25, fill="#dbcafb")
    mini = ImageFont.truetype(str(font_dir / "DejaVuSans-Bold.ttf"), 21)
    d.text((420, 359), "YOUR STICKER STUDIO", font=mini, fill="#2e256a")
    bg.save(output / "feature.png", "PNG")
    if Image.open(output / "feature.png").size != (1024, 500):
        raise ValueError("Bad feature dimensions")


def upload_media(directory: Path, screenshots: list[str]):
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from publish import get_credentials
    files = {
        "icon": ["icon.png"],
        "featureGraphic": ["feature.png"],
        "phoneScreenshots": screenshots,
    }
    service = build("androidpublisher", "v3", credentials=get_credentials(), cache_discovery=False)
    edits = service.edits()
    edit = edits.insert(packageName=PACKAGE, body={}).execute()
    eid = edit["id"]
    args = {"packageName": PACKAGE, "editId": eid}
    committed = False
    try:
        versions = {int(b["versionCode"]) for b in edits.bundles().list(**args).execute().get("bundles", [])}
        if VERSION_CODE not in versions:
            raise RuntimeError("RivoSticker version 4 was not accepted by Play")
        existing = edits.listings().list(**args).execute().get("listings", [])
        if not any(x.get("language") == "en-US" for x in existing):
            raise RuntimeError("English Play listing must already exist")
        tracks = edits.tracks().list(**args).execute().get("tracks", [])
        if any(int(v) > VERSION_CODE for t in tracks for rel in t.get("releases", [])
               for v in rel.get("versionCodes", [])):
            raise RuntimeError("Another newer release exists, refuse stale media update")
        for image_type, names in files.items():
            edits.images().deleteall(**args, language="en-US", imageType=image_type).execute()
            for name in names:
                resp = edits.images().upload(
                    **args, language="en-US", imageType=image_type,
                    media_body=MediaFileUpload(str(directory / name), mimetype="image/png", resumable=False),
                ).execute(num_retries=2)
                if not resp.get("image", {}).get("id"):
                    raise RuntimeError("Google Play did not return image ID for " + name)
            listed = edits.images().list(**args, language="en-US", imageType=image_type).execute().get("images", [])
            if len(listed) != len(names):
                raise RuntimeError("Play did not persist all " + image_type + " images")
        edits.validate(**args).execute()
        edits.commit(**args).execute()
        committed = True
        print("RIVOSTICKER_REAL_IMAGES_PLAY_COMMITTED=" +
              json.dumps({"package": PACKAGE, "versionCode": VERSION_CODE,
                          "screenshots": len(screenshots), "graphic": 1, "icon": 1,
                          "productionReleased": False}), flush=True)
    finally:
        if not committed:
            try:
                edits.delete(**args).execute()
            except Exception:
                print("Uncommitted Play media edit cleanup failed", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apk", type=Path, required=True)
    ap.add_argument("--output", type=Path, default=BASE)
    ap.add_argument("--publish", action="store_true")
    opt = ap.parse_args()
    expected = "0b61505b21134e1196da975f4f1abb937378a08444b52e29552e891fe7c3c82f"
    digest = hashlib.sha256(opt.apk.read_bytes()).hexdigest()
    if digest != expected:
        raise RuntimeError("Signed APK does not match trusted GitHub release SHA-256")
    files = capture(opt.apk, opt.output)
    icon_from_apk(opt.apk, opt.output)
    feature_from_icon(opt.output)
    if opt.publish:
        upload_media(opt.output, files)
    else:
        print("Native images validated but not submitted")


if __name__ == "__main__":
    main()
