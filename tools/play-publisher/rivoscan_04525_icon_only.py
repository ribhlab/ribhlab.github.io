#!/usr/bin/env python3
"""Publish exact owner-provided RivoScan 0.45.25 icon, preserving other Play assets."""
import hashlib,io,json,sys,tempfile
from pathlib import Path
from urllib.request import urlopen,Request
from PIL import Image
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from publish import get_credentials

PACKAGE="com.ribhlab.rivoscan"
LANGUAGE="en-US"
URL="https://gcdn.picsart.com/picsart-mcp/2d71979a-4ea6-4fad-ac6b-a2c8ff7a0aee.png"
SHA256="35ade99dba942696056a24fd25a1fb8a26c2094b7f5d24c8d43f23665a7d0d14"

def main():
    with urlopen(Request(URL,headers={"User-Agent":"RivoScan-Play-Icon-Upload/1.0"}),timeout=45) as r:
        raw=r.read(1000001)
    if hashlib.sha256(raw).hexdigest()!=SHA256:raise ValueError("Icon does not match uploaded owner's original")
    with Image.open(io.BytesIO(raw)) as im:
        if im.size!=(512,512) or im.mode!="RGBA" or im.format!="PNG":raise ValueError("Invalid Play icon")
        im.verify()
    edits=build("androidpublisher","v3",credentials=get_credentials(),cache_discovery=False).edits()
    edit_id=edits.insert(packageName=PACKAGE,body={}).execute()["id"]
    committed=False
    try:
        with tempfile.TemporaryDirectory() as tmp:
            icon=Path(tmp)/"RivoScan-0.45.25-Icon.png"
            icon.write_bytes(raw)
            # Google Play icon image type accepts one image; only this slot is replaced.
            edits.images().deleteall(packageName=PACKAGE,editId=edit_id,language=LANGUAGE,imageType="icon").execute()
            edits.images().upload(packageName=PACKAGE,editId=edit_id,language=LANGUAGE,imageType="icon",
                                  media_body=MediaFileUpload(str(icon),mimetype="image/png")).execute()
        current=edits.images().list(packageName=PACKAGE,editId=edit_id,language=LANGUAGE,imageType="icon").execute().get("images",[])
        if len(current)!=1:raise RuntimeError("Expected exactly one Play icon")
        edits.validate(packageName=PACKAGE,editId=edit_id).execute()
        edits.commit(packageName=PACKAGE,editId=edit_id).execute()
        committed=True
        print("RIVOSCAN_04525_ICON_RESULT="+json.dumps({"result":"COMMITTED","package":PACKAGE,
          "language":LANGUAGE,"imageType":"icon","sha256":SHA256,"iconCount":1,
          "screenshotsChanged":False,"featureGraphicChanged":False,"aabChanged":False,
          "releaseTracksChanged":False,"listingTextChanged":False}))
    finally:
        if not committed:
            try:edits.delete(packageName=PACKAGE,editId=edit_id).execute()
            except Exception:pass
if __name__=="__main__":
    try:main()
    except Exception as e:
        print("RIVOSCAN_04525_ICON_FAILED="+type(e).__name__+":"+str(e)[:250],file=sys.stderr)
        raise SystemExit(1)
