#!/usr/bin/env python3
"""Commit only the exact user-approved RivoCaption 0.4.3 brand assets to Play.

No app bundle or release-track changes. All locales updated in one Play edit;
a rejected commit leaves the published listing untouched.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import sys
from pathlib import Path
from PIL import Image

PACKAGE = "com.rivocaption.editor"
EXPECTED_ICON = "952c49aaf96c9494f45403029ebc976a7cf938335531189789d78a87ab03f32a"

def verify(root: Path) -> None:
    for filename, size in (("icon.png", (512,512)), ("feature.png",(1024,500))):
        path=root/filename
        if not path.is_file(): raise RuntimeError("Missing approved asset: "+filename)
        with Image.open(path) as im:
            if im.format!="PNG" or im.size!=size:
                raise RuntimeError("Invalid branding image dimensions: "+filename)
    icon=root/"icon.png"
    digest=hashlib.sha256(icon.read_bytes()).hexdigest()
    if digest != EXPECTED_ICON:
        raise RuntimeError("Uploaded image differs from user-approved 0.4.3 icon")
    if icon.stat().st_size>1024*1024:
        raise RuntimeError("App icon exceeds Google Play 1 MB limit")
    print("APPROVED_BRAND_ASSETS_VALID=TRUE",flush=True)

def apply(root: Path) -> None:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    from publish import get_credentials
    api=build("androidpublisher","v3",credentials=get_credentials(),cache_discovery=False)
    edits=api.edits()
    eid=edits.insert(packageName=PACKAGE,body={}).execute()["id"]
    committed=False
    common={"packageName":PACKAGE,"editId":eid}
    try:
        listings=edits.listings().list(**common).execute().get("listings",[])
        locales=sorted(set(x["language"] for x in listings if x.get("language")))
        if not locales:
            raise RuntimeError("RivoCaption Play store has no listing locales")
        tracks=edits.tracks().list(**common).execute().get("tracks",[])
        production=next((t for t in tracks if t.get("track")=="production"),None)
        if not production or not production.get("releases"):
            raise RuntimeError("No existing RivoCaption production release")
        results=[]
        for language in locales:
            for image_type,file_name in (("icon","icon.png"),("featureGraphic","feature.png")):
                edits.images().deleteall(**common,language=language,imageType=image_type).execute()
                result=edits.images().upload(
                    **common,language=language,imageType=image_type,
                    media_body=MediaFileUpload(str(root/file_name),mimetype="image/png",resumable=False),
                ).execute(num_retries=3)
                if not result.get("image",{}).get("id"):
                    raise RuntimeError(f"Google Play did not verify {language} / {image_type}")
                items=edits.images().list(**common,language=language,imageType=image_type).execute().get("images",[])
                if len(items)!=1:
                    raise RuntimeError(f"Expected one {image_type} for {language}, found {len(items)}")
                results.append((language,image_type))
        edits.validate(**common).execute()
        edits.commit(**common).execute()
        committed=True
        print("RIVOCAPTION_BRANDING_COMMITTED="+json.dumps({"locales":locales,"updated":len(results)}),flush=True)
    finally:
        if not committed:
            try: edits.delete(**common).execute()
            except Exception: print("WARNING: failed to delete uncommitted Play edit",flush=True)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--dir",type=Path,required=True)
    ap.add_argument("--commit-approved",action="store_true")
    a=ap.parse_args()
    verify(a.dir)
    if a.commit_approved:
        apply(a.dir)
    else:
        print("BRAND_VALIDATED_NO_PLAY_MUTATION=TRUE",flush=True)

if __name__=="__main__":
    main()
