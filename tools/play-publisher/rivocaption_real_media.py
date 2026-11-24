#!/usr/bin/env python3
"""Real signed RivoCaption Android studio screenshots and official app icon for Play.

Screenshots come only from adb screencap of the original-key-signed running APK.
Do not upload picker, Android OS, synthetic or mock studio screenshots.
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
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageStat
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from publish import get_credentials

PACKAGE = "com.rivocaption.editor"
CODE = 8
ROOT = Path("/tmp/rivocaption-real")
ANDROID = "{http://schemas.android.com/apk/res/android}"


def adb(*args: str, binary: bool = False, timeout: int = 100):
    done = subprocess.run(["adb", *args], stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, timeout=timeout, check=True)
    return done.stdout if binary else done.stdout.decode("utf-8", "replace")


def dump_ui(out: Path, label: str) -> list[dict]:
    adb("shell", "uiautomator", "dump", "/sdcard/rivocaption-ui.xml")
    xml = adb("exec-out", "cat", "/sdcard/rivocaption-ui.xml")
    start = xml.find("<?xml")
    if start == -1:
        raise RuntimeError("Cannot inspect actual Android UI")
    (out / (label + ".xml")).write_text(xml[start:], "utf-8")
    root = ET.fromstring(xml[start:])
    nodes = [n.attrib for n in root.iter("node")]
    names = sorted({str(n.get(k, "")) for n in nodes for k in ("text", "content-desc")
                    if str(n.get(k, "")).strip()})
    print("REAL_ANDROID_UI=" + json.dumps({"step": label, "names": names[:95]}, ensure_ascii=False), flush=True)
    return nodes


def tap(nodes: list[dict], label: str, partial: bool = False) -> bool:
    candidates = []
    for node in nodes:
        for prop in ("text", "content-desc"):
            val = node.get(prop, "").strip()
            if val.lower() == label.lower() or (partial and label.lower() in val.lower()):
                xy = [int(v) for v in re.findall(r"\d+", node.get("bounds", ""))]
                if len(xy) == 4:
                    candidates.append(((xy[1]+xy[3]) // 2, (xy[0]+xy[2]) // 2))
    if not candidates:
        return False
    y, x = sorted(candidates)[0]
    adb("shell", "input", "tap", str(x), str(y))
    time.sleep(2.0)
    print("REAL_ANDROID_TAPPED=" + json.dumps({"label": label, "x": x, "y": y}), flush=True)
    return True


def verify_image(path: Path):
    raw = path.read_bytes()
    if not raw.startswith(b"\x89PNG\r\n\x1a\n") or len(raw) < 18_000:
        raise ValueError("Missing or tiny native Android screenshot: " + path.name)
    with Image.open(io.BytesIO(raw)) as im:
        if im.format != "PNG" or im.size != (1080, 1920):
            raise ValueError("Incorrect emulator screenshot format or size: " + str(im.size))
        score = max(ImageStat.Stat(im.convert("RGB").resize((120, 180))).stddev)
        if score < 10:
            raise ValueError("Native image is uniform/blank " + path.name)
    return hashlib.sha256(raw).hexdigest()


def screenshot(out: Path, name: str):
    target = out / name
    target.write_bytes(adb("exec-out", "screencap", "-p", binary=True))
    print("REAL_CAPTION_SCREENSHOT=" + json.dumps({"file": name, "sha256": verify_image(target)}), flush=True)


def setup_sample_video(out: Path):
    target = out / "RivoCaptionDemo.mp4"
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
           "-f", "lavfi", "-i", "testsrc2=size=720x1280:rate=24",
           "-t", "8", "-c:v", "libx264", "-preset", "ultrafast",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(target)]
    subprocess.run(cmd, check=True, timeout=180)
    if target.stat().st_size < 60_000:
        raise RuntimeError("Test video not created")
    adb("shell", "mkdir", "-p", "/sdcard/Movies")
    adb("push", str(target), "/sdcard/Movies/RivoCaptionDemo.mp4")
    adb("shell", "am", "broadcast", "-a", "android.intent.action.MEDIA_SCANNER_SCAN_FILE",
        "-d", "file:///sdcard/Movies/RivoCaptionDemo.mp4")
    print("TEST_MEDIA_CREATED=" + str(target.stat().st_size), flush=True)


def open_video_in_picker(out: Path):
    nodes = dump_ui(out, "before-picker")
    if not tap(nodes, "Choose video"):
        raise RuntimeError("Signed app did not show genuine RivoCaption Choose video control")
    for i in range(10):
        nodes = dump_ui(out, f"picker-{i}")
        text = {n.get("text", "").strip() for n in nodes}
        descriptions = {n.get("content-desc", "").strip() for n in nodes}
        if "RIVO · CREATOR STUDIO" in text or "CAPTION STYLE" in text:
            return True
        if tap(nodes, "RivoCaptionDemo", partial=True):
            time.sleep(4)
            return True
        if tap(nodes, "Movies"):
            continue
        if tap(nodes, "Videos"):
            continue
        if tap(nodes, "Browse"):
            continue
        if tap(nodes, "Show roots"):
            continue
        if tap(nodes, "Open navigation drawer"):
            continue
        if tap(nodes, "Internal storage"):
            continue
        if tap(nodes, "sdk_gphone64_x86_64"):
            continue
        if i == 0 and (("Recent" in text) or ("Recent" in descriptions)):
            time.sleep(2)
            continue
        time.sleep(2)
    raise RuntimeError("System document picker did not offer imported test video; screenshots were NOT submitted")


def capture(apk: Path, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    adb("shell", "wm", "size", "1080x1920")
    adb("shell", "wm", "density", "440")
    adb("shell", "settings", "put", "system", "font_scale", "1.0")
    adb("install", "-r", str(apk), timeout=200)
    adb("shell", "svc", "wifi", "disable")
    adb("shell", "svc", "data", "disable")
    adb("shell", "am", "force-stop", PACKAGE)
    adb("shell", "am", "start", "-W", "-n", PACKAGE + "/.MainActivity")
    time.sleep(13)
    if not adb("shell", "pidof", PACKAGE).strip():
        raise RuntimeError("RivoCaption release could not launch on Android emulator")
    nodes = dump_ui(out, "home")
    if not any(n.get("text", "") == "Your creative studio" for n in nodes):
        raise RuntimeError("Home screenshot would not show actual RivoCaption studio")
    screenshot(out, "phone-01-home.png")
    setup_sample_video(out)
    open_video_in_picker(out)
    time.sleep(7)
    nodes = dump_ui(out, "after-import")
    if any(n.get("text", "") == "Got it" for n in nodes):
        if not tap(nodes, "Got it"):
            raise RuntimeError("Immersive Android onboarding dialog could not be dismissed")
        time.sleep(3)
        nodes = dump_ui(out, "after-fullscreen-consent")
    if not any(n.get("text", "") in ("Captions", "Styles", "Export") for n in nodes):
        raise RuntimeError("RivoCaption video editor not visible after selecting sample video")
    screenshot(out, "phone-02-ai.png")
    for label, name in (("Styles", "phone-03-styles.png"),
                        ("Captions", "phone-04-captions.png"),
                        ("Export", "phone-05-export.png")):
        nodes = dump_ui(out, "before-" + label.lower())
        if not tap(nodes, label):
            raise RuntimeError("Actual app editor tab unavailable: " + label)
        dump_ui(out, "after-" + label.lower())
        screenshot(out, name)
    names = [f"phone-0{i}-{suffix}.png" for i, suffix in
             ((1, "home"), (2, "ai"), (3, "styles"), (4, "captions"), (5, "export"))]
    if len({verify_image(out / name) for name in names}) != len(names):
        raise RuntimeError("Real screenshots are duplicates, refusing Play upload")
    return names


def official_icon(out: Path):
    from html import escape
    import cairosvg
    source = Path(__file__).with_name("rivocaption_official_icon_foreground.xml")
    root = ET.parse(source).getroot()
    paths = []
    for node in root.findall("path"):
        a = node.attrib
        d = a.get(ANDROID + "pathData", "")
        if not d:
            continue
        fill = a.get(ANDROID + "fillColor", "#ffffff")
        stroke = a.get(ANDROID + "strokeColor", "none")
        stroke_width = a.get(ANDROID + "strokeWidth", "0")
        cap = a.get(ANDROID + "strokeLineCap", "round")
        paths.append(f'<path d="{escape(d)}" fill="{escape(fill)}" '
                     f'stroke="{escape(stroke)}" stroke-width="{stroke_width}" stroke-linecap="{cap}"/>')
    if len(paths) < 6:
        raise RuntimeError("Official RivoCaption launcher vector missing")
    svg = '<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 108 108">' + "".join(paths) + "</svg>"
    png = cairosvg.svg2png(bytestring=svg.encode("utf-8"), output_width=512, output_height=512)
    fg = Image.open(io.BytesIO(png)).convert("RGBA")
    canvas = Image.new("RGB", (512, 512))
    px = canvas.load()
    for y in range(512):
        for x in range(512):
            fraction = min(1.0, (x+y)/1022)
            px[x,y] = (int(89-64*fraction), int(17-5*fraction), int(142-104*fraction))
    canvas.paste(fg, (0, 0), fg)
    canvas.save(out / "icon.png", "PNG")
    if (out / "icon.png").stat().st_size > 1_000_000:
        raise RuntimeError("512x512 Play icon exceeds max size")


def official_feature(out: Path):
    canvas = Image.new("RGB", (1024, 500))
    d = ImageDraw.Draw(canvas)
    for y in range(500):
        t = y/499
        color = (int(18+55*t), int(10+14*t), int(50+88*t))
        d.line((0,y,1024,y), fill=color)
    with Image.open(out / "icon.png") as icon:
        badge = icon.convert("RGB").resize((300,300), Image.Resampling.LANCZOS)
        canvas.paste(badge, (45, 102))
    fonts = Path("/usr/share/fonts/truetype/dejavu")
    large = ImageFont.truetype(str(fonts / "DejaVuSans-Bold.ttf"), 70)
    medium = ImageFont.truetype(str(fonts / "DejaVuSans.ttf"), 35)
    small = ImageFont.truetype(str(fonts / "DejaVuSans-Bold.ttf"), 24)
    d.text((375,147),"RivoCaption",font=large,fill="#ffffff")
    d.text((383,242),"Make every word visible.",font=medium,fill="#f5e4ff")
    d.rounded_rectangle((386,334,835,396),radius=26,fill="#ffcf69")
    d.text((414,352),"CAPTION · STYLE · EXPORT",font=small,fill="#3e1453")
    canvas.save(out / "feature.png", "PNG")


def upload(out: Path, captures: list[str]):
    edits = build("androidpublisher", "v3", credentials=get_credentials(), cache_discovery=False).edits()
    eid = edits.insert(packageName=PACKAGE, body={}).execute()["id"]
    args = {"packageName": PACKAGE, "editId": eid}
    committed = False
    try:
        codes = {int(b["versionCode"]) for b in edits.bundles().list(**args).execute().get("bundles", [])}
        if codes != {CODE}:
            raise RuntimeError("Play bundle versions not the exact signed RivoCaption v8: " + str(codes))
        listings = edits.listings().list(**args).execute().get("listings", [])
        if not any(x.get("language") == "en-US" and x.get("title") for x in listings):
            raise RuntimeError("RivoCaption English store listing not saved; refuse upload")
        tracks = edits.tracks().list(**args).execute().get("tracks", [])
        if any(int(c) > CODE for t in tracks for rel in t.get("releases", []) for c in rel.get("versionCodes", [])):
            raise RuntimeError("Higher version already on Play; never overwrite")
        grouped = {"icon": ["icon.png"], "featureGraphic": ["feature.png"], "phoneScreenshots": captures}
        for kind, names in grouped.items():
            edits.images().deleteall(**args, language="en-US", imageType=kind).execute()
            for name in names:
                result = edits.images().upload(
                    **args, language="en-US", imageType=kind,
                    media_body=MediaFileUpload(str(out/name), mimetype="image/png", resumable=False)
                ).execute(num_retries=3)
                if not result.get("image", {}).get("id"):
                    raise RuntimeError("Google Play missing uploaded image id: " + name)
            stored = edits.images().list(**args, language="en-US", imageType=kind).execute().get("images", [])
            if len(stored) != len(names):
                raise RuntimeError("Google Play image count mismatch " + kind)
        edits.validate(**args).execute()
        edits.commit(**args).execute()
        committed = True
        print("RIVOCAPTION_GENUINE_IMAGES_PLAY_COMMITTED=" + json.dumps(
            {"package": PACKAGE, "versionCode": CODE, "images": {k:len(v) for k,v in grouped.items()},
             "productionReleased": False}), flush=True)
    finally:
        if not committed:
            try: edits.delete(**args).execute()
            except Exception: print("Uncommitted media edit cleanup failed", file=sys.stderr)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--apk", required=True, type=Path)
    p.add_argument("--output", default=ROOT, type=Path)
    p.add_argument("--publish", action="store_true")
    args=p.parse_args()
    if not args.apk.is_file():
        raise RuntimeError("Original-signed APK missing")
    names = capture(args.apk, args.output)
    official_icon(args.output)
    official_feature(args.output)
    if args.publish: upload(args.output, names)
    else: print("Captured real screens and genuine launcher icon; no Play upload requested")


if __name__ == "__main__":
    main()
