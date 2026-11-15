#!/usr/bin/env python3
"""Safely upload RivoScan v0.45.26 (130) signed AAB to the EXISTING test track.
Never promote a production release. Never touch images, video, or descriptions.
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from publish import get_credentials
APP="com.ribhlab.rivoscan"
EXPECTED=130
RELEASE_NAME="RivoScan 0.45.26 – New App Icon"
NOTES="New RivoScan app icon with a larger blue R, no text, and improved Android launcher appearance. Existing scanning, OCR and PDF tools remain available."
def upload(aab:Path,confirm:str):
 if confirm!="PUBLISH_RIVOSCAN_130_TO_EXISTING_TESTERS":raise ValueError("Exact approval missing")
 if not aab.exists() or aab.suffix!=".aab" or aab.stat().st_size<15_000_000:raise ValueError("Missing signed AAB")
 edits=build("androidpublisher","v3",credentials=get_credentials(),cache_discovery=False).edits()
 edit=edits.insert(packageName=APP,body={}).execute();eid=edit["id"];done=False
 try:
  known=edits.tracks().list(packageName=APP,editId=eid).execute().get("tracks",[])
  def has_version(track,code):
   return any(str(code) in [str(x) for x in rel.get("versionCodes",[])] for rel in track.get("releases",[]))
  chosen=next((t for tag in ("beta","alpha","qa","internal") for t in known
      if t.get("track")==tag and has_version(t,129)),None)
  if chosen is None:
   # Never create a new public/production rollout on guesswork.
   raise RuntimeError("No existing RivoScan v129 testing track. Existing Play tracks: "+
                      ",".join(t.get("track","?") for t in known))
  track=chosen["track"]
  releases=chosen.get("releases",[])
  if has_version(chosen,130):
   print("RIVOSCAN_AAB_RESULT="+json.dumps({"result":"ALREADY_TRACKED","track":track,
       "versionCode":130,"releaseUnchanged":True}))
   return
  if any(rel.get("status")!="completed" for rel in releases):
   raise RuntimeError("Testing track has draft, staged or halted releases; no automatic overwrite")
  if any(len(rel.get("versionCodes",[]))!=1 for rel in releases):
   raise RuntimeError("Track has multi-APK compatibility releases; manual approval required")
  inventory=edits.bundles().list(packageName=APP,editId=eid).execute().get("bundles",[])
  versions={int(x.get("versionCode")) for x in inventory if x.get("versionCode") is not None}
  if EXPECTED in versions:
   raise RuntimeError("v130 already exists in Play inventory; refuse to overwrite unknown AAB")
  signed=edits.bundles().upload(packageName=APP,editId=eid,
      media_body=MediaFileUpload(str(aab),mimetype="application/octet-stream",resumable=True)).execute()
  got=int(signed.get("versionCode",0))
  if got!=EXPECTED:raise RuntimeError(f"Unexpected AAB code {got} (expected 130)")
  edits.tracks().update(packageName=APP,editId=eid,track=track,body={
   "track":track,"releases":[{
      "name":RELEASE_NAME,"versionCodes":[str(EXPECTED)],
      "status":"completed",
      "releaseNotes":[{"language":"en-US","text":NOTES}]
   }]
  }).execute()
  edits.validate(packageName=APP,editId=eid).execute()
  edits.commit(packageName=APP,editId=eid).execute();done=True
  print("RIVOSCAN_AAB_RESULT="+json.dumps({"result":"COMMITTED","package":APP,
    "track":track,"versionCode":EXPECTED,"status":"completed",
    "note":"Update made available to existing testing-track users, subject to Play review",
    "productionModified":False,"graphicsModified":False,"videoModified":False}))
 finally:
  if not done:
   try:edits.delete(packageName=APP,editId=eid).execute()
   except Exception:pass
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--aab",type=Path,required=True)
 p.add_argument("--confirm",default="")
 args=p.parse_args();upload(args.aab,args.confirm)
if __name__=="__main__":main()
