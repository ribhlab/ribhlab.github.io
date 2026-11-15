#!/usr/bin/env python3
"""Update RivoScan Play listing text and metadata for owner-uploaded versionCode 129.
No images, bundles, release status, rollout, track assignment, or app settings are changed.
"""
import json
import sys
from pathlib import Path
from googleapiclient.discovery import build
from publish import get_credentials

PACKAGE="com.ribhlab.rivoscan"
CODE="129"
RELEASE_NAME="RivoScan 0.45.25 – Premium Scanner"
NOTES="Improved information buttons across scanning tools, refined layouts, and enhanced interface consistency for a smoother document scanning experience."
SHORT="Scan documents to PDF, recognize text with OCR, edit, organize and share files."
FULL="""RivoScan is a document scanner and PDF toolkit for Android. Capture pages, organize documents and handle everyday PDF tasks in one app.

DOCUMENT SCANNER
Scan paper documents with your camera, review and adjust pages, and export them to PDF. Automatic edge detection depends on your device.

PDF TOOLS
Merge PDFs, extract or remove pages, rotate and reorder pages, add page numbers, text annotations and watermarks.

OCR AND CONVERSION
Recognize text from scanned pages with OCR in supported languages, extract selectable PDF text, and export PDF pages as JPG or PNG. Some OCR language models may require an initial download.

SIGN AND SHARE
Add a drawn visual signature and save or share files using supported Android options.

Some tools may be experimental or device-dependent. Drawn signatures are not certificate-backed digital signatures. PDF compression may remove searchable text or interactive features."""
assert len(SHORT)<=80 and len(FULL)<=4000 and len(RELEASE_NAME)<=80 and len(NOTES)<=500

def main():
    service=build("androidpublisher","v3",credentials=get_credentials(),cache_discovery=False)
    edits=service.edits()
    edit_id=edits.insert(packageName=PACKAGE,body={}).execute()["id"]
    committed=False
    try:
        existing=edits.listings().get(packageName=PACKAGE,editId=edit_id,language="en-US").execute()
        # Preserve current title, only update descriptions.
        edits.listings().patch(packageName=PACKAGE,editId=edit_id,language="en-US",
            body={"shortDescription":SHORT,"fullDescription":FULL}).execute()
        updated_tracks=[]
        for track in edits.tracks().list(packageName=PACKAGE,editId=edit_id).execute().get("tracks",[]):
            releases=track.get("releases",[])
            matches=[r for r in releases if CODE in [str(c) for c in r.get("versionCodes",[])]]
            if not matches:continue
            if len(matches)!=1:
                raise RuntimeError("Ambiguous versionCode 129 in "+track["track"])
            # Preserve every other release field including status, rollout, versionCodes and targeting.
            for release in matches:
                release["name"]=RELEASE_NAME
                notes=release.get("releaseNotes",[])
                notes=[n for n in notes if n.get("language")!="en-US"]
                notes.append({"language":"en-US","text":NOTES})
                release["releaseNotes"]=notes
            edits.tracks().update(packageName=PACKAGE,editId=edit_id,track=track["track"],
                body={"track":track["track"],"releases":releases}).execute()
            updated_tracks.append(track["track"])
        edits.validate(packageName=PACKAGE,editId=edit_id).execute()
        edits.commit(packageName=PACKAGE,editId=edit_id).execute()
        committed=True
        print("RIVOSCAN_04525_METADATA_RESULT="+json.dumps({
            "result":"COMMITTED","appId":PACKAGE,"descriptionLanguage":"en-US",
            "releaseVersionCode":CODE,"releaseTracksUpdated":updated_tracks,
            "releaseNameUpdated":bool(updated_tracks),
            "imagesChanged":False,"aabChanged":False,"releaseStatusChanged":False,
            "note":"If releaseTracksUpdated is empty, uploaded AAB 129 has not been found in a Play track."
        }))
    finally:
        if not committed:
            try:edits.delete(packageName=PACKAGE,editId=edit_id).execute()
            except Exception:pass

if __name__=="__main__":
    try:main()
    except Exception as e:
        print("RIVOSCAN_04525_METADATA_FAILED="+type(e).__name__+":"+str(e)[:250],file=sys.stderr)
        raise SystemExit(1)
