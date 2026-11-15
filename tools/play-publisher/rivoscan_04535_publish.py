#!/usr/bin/env python3
"""Publish exactly RivoScan 0.45.35 (versionCode 139) using the ORIGINAL Play upload key.

Requires owner confirmation token. Phase 1: verify official signed AAB and
commit it to an EXISTING completed testing track. Phase 2: atomically update
the existing Production release, 7 locale listings and actual 0.45.35 UI media.
Never changes app-content questionnaires or touch unrelated packages/releases.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

PACKAGE = "com.ribhlab.rivoscan"
VERSION = 139
APP_VERSION = "0.45.35"
RELEASE = ("https://github.com/univcours/ribhlab/releases/download/"
           "rivoscan-0.45.35-original-key/RivoScan-0.45.35-GooglePlay.aab")
CERT = "E9:B3:E2:77:95:75:BA:08:A9:13:72:FC:38:85:EB:A0:1D:D3:E7:3E"
CONFIRM = "PUBLISH_SIGNED_RIVOSCAN_139_AND_REFRESH_STORE"
ROOT = Path(__file__).resolve().parent
LISTING = ROOT / "store-listings/rivoscan.json"
TEST_TRACKS = ("beta", "alpha", "qa", "internal")
VIEWS = ("01_Home", "02_Documents", "03_Tools", "04_Book_Scan",
         "05_Formula_OCR", "06_Photo_Translation", "07_ID_Photo", "08_Settings")


def report(event, **info):
    print("RIVOSCAN_04535_" + event + "=" + json.dumps(info, ensure_ascii=False, sort_keys=True), flush=True)


def safe_source_aab(directory: Path) -> Path:
    dest = directory / "RivoScan-0.45.35-GooglePlay.aab"
    request = urllib.request.Request(RELEASE, headers={"User-Agent": "RivoScan-Verified-PlayPublisher/0.45.35"})
    with urllib.request.urlopen(request, timeout=150) as response:
        with dest.open("wb") as out:
            total = 0
            while True:
                chunk = response.read(65536)
                if not chunk:
                    break
                total += len(chunk)
                if total > 110_000_000:
                    raise ValueError("Downloaded AAB exceeds verified release cap")
                out.write(chunk)
    if not 20_000_000 < dest.stat().st_size < 110_000_000:
        raise ValueError("Signed AAB has implausible size")
    with zipfile.ZipFile(dest) as z:
        if "base/manifest/AndroidManifest.xml" not in z.namelist() or z.testzip():
            raise ValueError("Corrupt or non-Android AAB")
    cert = subprocess.run(["keytool", "-printcert", "-jarfile", str(dest)],
                          check=True, capture_output=True, text=True)
    if "SHA1: " + CERT not in cert.stdout:
        raise RuntimeError("Wrong RivoScan upload certificate: do NOT publish")
    verified = subprocess.run(["jarsigner", "-verify", str(dest)],
                              check=True, capture_output=True, text=True)
    if "jar verified" not in verified.stdout + verified.stderr:
        raise RuntimeError("Original Play AAB signature validation failed")
    report("AAB_VERIFIED", versionCode=VERSION, bytes=dest.stat().st_size,
           sha256=hashlib.sha256(dest.read_bytes()).hexdigest(), originalCertificate=True)
    return dest


def valid_listing() -> dict:
    doc = json.loads(LISTING.read_text(encoding="utf-8"))
    if doc.get("appId") != PACKAGE:
        raise ValueError("Wrong Play listing package")
    required = {"en-US", "ar", "fr-FR", "es-ES", "de-DE", "pt-BR", "it-IT"}
    if set(doc.get("locales", {})) != required:
        raise ValueError("Expected exactly 7 verified locales")
    for lang, listing in doc["locales"].items():
        for key, limit in (("title", 30), ("shortDescription", 80), ("fullDescription", 4000)):
            value = listing.get(key)
            if not isinstance(value, str) or not value.strip() or len(value) > limit:
                raise ValueError(f"Invalid {lang} {key} length; limit {limit}")
        if "rewarded video" in listing["fullDescription"].lower():
            raise ValueError("Stale rewarded advertising claim")
    return doc


def valid_media(directory: Path) -> dict:
    from PIL import Image
    icon = directory / "app-icon-512.png"
    feature = directory / "feature-1024x500.png"
    with Image.open(icon) as im:
        if im.format != "PNG" or im.size != (512, 512):
            raise ValueError("Store icon must be actual app PNG 512x512")
    with Image.open(feature) as im:
        if im.format != "PNG" or im.size != (1024, 500):
            raise ValueError("Feature graphic must be PNG 1024x500")
    slots = {"icon": [icon], "featureGraphic": [feature]}
    for kind, folder, dims in (
        ("phoneScreenshots", "phone/phone", (1080, 1920)),
        ("sevenInchScreenshots", "tablet/7-inch", (1080, 1920)),
        ("tenInchScreenshots", "tablet/10-inch", (1536, 2560)),
    ):
        shots = []
        for view in VIEWS:
            src = directory / folder / (view + ".png")
            if not src.is_file() or src.stat().st_size < 10000 or src.stat().st_size > 8_000_000:
                raise ValueError("Missing or invalid real 0.45.35 screenshot: " + str(src))
            with Image.open(src) as im:
                if im.format != "PNG" or im.size != dims:
                    raise ValueError("Wrong screenshot resolution: " + str(src))
            shots.append(src)
        slots[kind] = shots
    fingerprints = [hashlib.sha256(p.read_bytes()).hexdigest() for files in slots.values() for p in files]
    if len(set(fingerprints)) != len(fingerprints):
        raise ValueError("Duplicate image assets; refuse to publish")
    report("MEDIA_VALIDATED", counts={k: len(v) for k, v in slots.items()},
           source="0.45.35 actual app WebView, no invented camera results")
    return slots


def play_client():
    from googleapiclient.discovery import build
    from publish import get_credentials
    return build("androidpublisher", "v3", credentials=get_credentials(), cache_discovery=False).edits()


def create_edit(edits):
    return edits.insert(packageName=PACKAGE, body={}).execute()["id"]


def safe_discard(edits, edit_id):
    try:
        edits.delete(packageName=PACKAGE, editId=edit_id).execute()
    except Exception:
        report("CLEANUP_WARNING", editId=edit_id)


def release_notes():
    return [
        {"language": "en-US", "text": "Improved first scan saving, a magnifier for document corners, search beside My Documents and simpler importing. Stability improvements."},
        {"language": "fr-FR", "text": "Enregistrement de la première numérisation amélioré, loupe pour les coins, recherche à côté de Mes documents et importation simplifiée."},
        {"language": "ar", "text": "تحسين حفظ أول مستند، وإضافة عدسة مكبّرة لضبط الحواف، ونقل البحث بجانب عنوان مستنداتي، وتبسيط الاستيراد."},
        {"language": "es-ES", "text": "Mejor guardado del primer escaneo, lupa para ajustar bordes, búsqueda junto a Mis documentos e importación simplificada."},
        {"language": "de-DE", "text": "Verbessertes Speichern des ersten Scans, Lupe für Dokumentecken, Suche neben Meine Dokumente und einfacherer Import."},
        {"language": "pt-BR", "text": "Melhor gravação da primeira digitalização, lupa para os cantos, pesquisa junto a Os meus documentos e importação simplificada."},
        {"language": "it-IT", "text": "Salvataggio della prima scansione migliorato, lente per gli angoli, ricerca accanto a I miei documenti e importazione semplificata."},
    ]


def track_releases(tracks):
    return {row.get("track"): row.get("releases", []) for row in tracks}


def stage_original_bundle(edits, aab: Path):
    from googleapiclient.http import MediaFileUpload
    edit_id = create_edit(edits)
    committed = False
    try:
        tracks = track_releases(edits.tracks().list(packageName=PACKAGE, editId=edit_id).execute().get("tracks", []))
        production = tracks.get("production", [])
        if len(production) != 1 or production[0].get("status") != "completed":
            raise RuntimeError("Production not in a single completed-release state; refuse update")
        current = [int(v) for v in production[0].get("versionCodes", [])]
        if len(current) != 1 or current[0] > VERSION:
            raise RuntimeError("Production version is newer or mixed; no downgrade")
        report("PRODUCTION_PRECHECK", servingVersion=current[0])
        options = []
        for idx, track in enumerate(TEST_TRACKS):
            releases = tracks.get(track, [])
            if len(releases) == 1 and releases[0].get("status") == "completed" and len(releases[0].get("versionCodes", [])) == 1:
                options.append((idx, track, int(releases[0]["versionCodes"][0])))
        if not options:
            raise RuntimeError("No safe existing completed test track for staged update")
        options.sort()
        _, track, previous = options[0]
        inventory = edits.bundles().list(packageName=PACKAGE, editId=edit_id).execute().get("bundles", [])
        uploaded = {int(row.get("versionCode", -1)) for row in inventory}
        if VERSION not in uploaded:
            result = edits.bundles().upload(packageName=PACKAGE, editId=edit_id,
                media_body=MediaFileUpload(str(aab), mimetype="application/octet-stream", resumable=True)).execute()
            if int(result.get("versionCode", -1)) != VERSION:
                raise RuntimeError("Play API did not accept expected versionCode 139")
        edits.tracks().update(packageName=PACKAGE, editId=edit_id, track=track,
           body={"track": track, "releases": [{"name": "RivoScan 0.45.35 - First Scan and Edge Magnifier",
                  "versionCodes": [str(VERSION)], "status": "completed",
                  "releaseNotes": release_notes()}]}).execute()
        edits.validate(packageName=PACKAGE, editId=edit_id).execute()
        edits.commit(packageName=PACKAGE, editId=edit_id).execute()
        committed = True
        report("TEST_TRACK_COMMITTED", versionCode=VERSION, track=track, previous=previous,
               productionUntouched=True)
        return current[0]
    finally:
        if not committed:
            safe_discard(edits, edit_id)


def publish_store_and_production(edits, listing: dict, images: dict, previous: int):
    from googleapiclient.http import MediaFileUpload
    edit_id = create_edit(edits)
    committed = False
    try:
        tracks = track_releases(edits.tracks().list(packageName=PACKAGE, editId=edit_id).execute().get("tracks", []))
        production = tracks.get("production", [])
        if len(production) != 1 or production[0].get("status") != "completed":
            raise RuntimeError("Production state changed between test and store publishing")
        codes = [int(v) for v in production[0].get("versionCodes", [])]
        if codes != [previous]:
            raise RuntimeError("Production version changed concurrently; stop safely")
        tests = [
            (track, x) for track in TEST_TRACKS for x in tracks.get(track, [])
            if x.get("status") == "completed" and str(VERSION) in [str(v) for v in x.get("versionCodes", [])]
        ]
        if not tests:
            raise RuntimeError("VersionCode 139 must be completed in an existing test track")
        details = {"defaultLanguage": "en-US", "contactWebsite": "https://ribhlab.github.io/rivoscan/",
                   "contactEmail": "rachid022note4@gmail.com"}
        edits.details().patch(packageName=PACKAGE, editId=edit_id, body=details).execute()
        existing = edits.listings().list(packageName=PACKAGE, editId=edit_id).execute().get("listings", [])
        langs = {x.get("language") for x in existing}
        for lang, values in listing["locales"].items():
            body = {"language": lang, **values}
            kwargs = {"packageName": PACKAGE, "editId": edit_id, "language": lang, "body": body}
            method = edits.listings().patch if lang in langs else edits.listings().update
            method(**kwargs).execute()
            report("LOCALE_UPDATED", locale=lang, title=values["title"])
        for kind, paths in images.items():
            edits.images().deleteall(packageName=PACKAGE, editId=edit_id,
                                    language="en-US", imageType=kind).execute()
            for filepath in paths:
                edits.images().upload(packageName=PACKAGE, editId=edit_id,
                    language="en-US", imageType=kind,
                    media_body=MediaFileUpload(str(filepath),
                       mimetype="image/png", resumable=False)).execute()
            stored = edits.images().list(packageName=PACKAGE, editId=edit_id,
                                         language="en-US", imageType=kind).execute().get("images", [])
            if len(stored) != len(paths):
                raise RuntimeError(f"Play image count mismatch for {kind}: {len(stored)}")
            report("IMAGE_UPDATED", category=kind, count=len(stored))
        edits.tracks().update(packageName=PACKAGE, editId=edit_id, track="production",
           body={"track": "production", "releases": [{
               "name": "RivoScan 0.45.35 - Improved Scanner and Documents",
               "versionCodes": [str(VERSION)], "status": "completed",
               "releaseNotes": release_notes()
           }]}).execute()
        edits.validate(packageName=PACKAGE, editId=edit_id).execute()
        edits.commit(packageName=PACKAGE, editId=edit_id).execute()
        committed = True
        report("PRODUCTION_COMMITTED", package=PACKAGE, versionCode=VERSION, fromCode=previous,
               status="completed", tracks="production", localizedListings=7,
               images={k: len(v) for k,v in images.items()},
               reviewMayBeRequired=True, dataSafetyQuestionnairesUnchanged=True)
    finally:
        if not committed:
            safe_discard(edits, edit_id)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm", default="")
    parser.add_argument("--media-dir", type=Path, default=Path("/tmp/rivoscan-publish-media"))
    options = parser.parse_args()
    listing = valid_listing()
    media = valid_media(options.media_dir)
    if not options.apply:
        report("DRY_RUN_OK", versionCode=VERSION, locales=sorted(listing["locales"]), files=sum(map(len,media.values())))
        return
    if options.confirm != CONFIRM:
        raise ValueError("Missing explicit owner authorization token")
    with tempfile.TemporaryDirectory() as td:
        bundle = safe_source_aab(Path(td))
        edits = play_client()
        previous = stage_original_bundle(edits, bundle)
        publish_store_and_production(edits, listing, media, previous)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        report("ERROR", type=type(exc).__name__, message=str(exc)[:350],
               httpStatus=getattr(getattr(exc, "resp", None), "status", None))
        raise SystemExit(1)
