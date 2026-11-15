#!/usr/bin/env python3
"""Safely publish ORIGINAL upload-key RivoScan 0.45.26 to the existing beta-test
track (or closed/internal test) that currently serves 0.45.25.
This never modifies the public Production track or store listing imagery.
Only the owner-approved original-key AAB from the original GitHub release is used.
"""
from __future__ import annotations
import argparse, json, io, hashlib, sys, tempfile, zipfile
from pathlib import Path
from urllib.request import Request,urlopen
APP="com.ribhlab.rivoscan"
VERSION=130
PREVIOUS=129
URL="https://github.com/univcours/ribhlab/releases/download/rivoscan-0.45.26-original-key/RivoScan-0.45.26-GooglePlay.aab"
NOTES="New RivoScan blue R icon without wordmark, improved visual consistency, and the familiar document-scanning and PDF tools."
TRACK_PRIORITY=("beta","alpha","qa","internal")
def bundle_file(folder:Path):
 path=folder/"RivoScan-0.45.26-GooglePlay.aab"
 if not path.exists():
  req=Request(URL,headers={"User-Agent":"RivoScan-original-upload-key-PlayPublisher/0.45.26"})
  with urlopen(req,timeout=90) as r:
   raw=r.read(120_000_000)
  if len(raw)<1_000_000 or len(raw)>110_000_000:raise RuntimeError("AAB size invalid")
  path.write_bytes(raw)
 with zipfile.ZipFile(path) as z:
  if "base/manifest/AndroidManifest.xml" not in z.namelist() or z.testzip():
   raise RuntimeError("Original-key release AAB invalid or corrupt")
 print("AAB_ORIGINAL_RELEASE_VERIFIED="+json.dumps({"bytes":path.stat().st_size,
      "sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
      "expectedVersionCode":VERSION,"source":"univcours/ribhlab original-key release"}),flush=True)
 return path
def existing_track(tracks):
 choices=[]
 for obj in tracks:
  name=obj.get("track","")
  if name not in TRACK_PRIORITY:continue
  for release in obj.get("releases",[]):
   versions=[str(x) for x in release.get("versionCodes",[])]
   if str(PREVIOUS) in versions or str(VERSION) in versions:
    choices.append((TRACK_PRIORITY.index(name),obj,release))
 if not choices:raise RuntimeError("No eligible testing track serving version 129 or 130; refusing to infer production rollout")
 choices.sort(key=lambda x:x[0])
 _,t,release=choices[0]
 if release.get("status") not in ("draft","completed"):
  raise RuntimeError("Testing track is staged/paused; requires manual review")
 if len(release.get("versionCodes",[]))!=1:
  raise RuntimeError("Testing track has multi-bundle release; stop")
 if any(item.get("status") not in ("draft","completed") for item in t.get("releases",[])):
  raise RuntimeError("Track contains incompatible staged rollout")
 return t,release
def deploy(aab:Path):
 from googleapiclient.discovery import build
 from googleapiclient.http import MediaFileUpload
 from publish import get_credentials
 edits=build("androidpublisher","v3",credentials=get_credentials(),cache_discovery=False).edits()
 eid=edits.insert(packageName=APP,body={}).execute()["id"]
 committed=False
 try:
  tracks=edits.tracks().list(packageName=APP,editId=eid).execute().get("tracks",[])
  target,old=existing_track(tracks)
  name=target["track"]
  if str(VERSION) in [str(v) for v in old.get("versionCodes",[])] and old.get("status")=="completed":
   print("RIVOSCAN_AAB_UPDATE="+json.dumps({"status":"ALREADY_PUBLISHED","track":name,"versionCode":VERSION}),flush=True)
   return
  inventory=edits.bundles().list(packageName=APP,editId=eid).execute().get("bundles",[])
  available={str(b.get("versionCode")) for b in inventory}
  if str(VERSION) not in available:
   res=edits.bundles().upload(packageName=APP,editId=eid,
      media_body=MediaFileUpload(str(aab),mimetype="application/octet-stream",resumable=True)).execute()
   if str(res.get("versionCode"))!=str(VERSION):
    raise RuntimeError("Play API rejected versionCode 130: "+str(res.get("versionCode")))
  # Release only on the matching EXISTING TEST track; no Production modification.
  status=old.get("status")
  release={"status":status,"versionCodes":[str(VERSION)],
     "name":"RivoScan 0.45.26 – Blue Icon Update",
     "releaseNotes":[{"language":"en-US","text":NOTES}]}
  edits.tracks().update(packageName=APP,editId=eid,track=name,
       body={"track":name,"releases":[release]}).execute()
  edits.validate(packageName=APP,editId=eid).execute()
  edits.commit(packageName=APP,editId=eid).execute()
  committed=True
  print("RIVOSCAN_AAB_UPDATE="+json.dumps({
    "status":"COMMITTED","package":APP,"versionCode":VERSION,
    "testTrack":name,"releaseStatus":status,
    "productionChanged":False,"listingAndMediaChanged":False,
    "note":"Google Play review/processing may delay availability"}),flush=True)
 finally:
  if not committed:
   try:edits.delete(packageName=APP,editId=eid).execute()
   except Exception:pass
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--apply",action="store_true")
 p.add_argument("--confirm",default="")
 args=p.parse_args()
 if args.apply and args.confirm!="UPLOAD_RIVOSCAN_04526_SIGNED_TO_EXISTING_TEST_TRACK":
  raise ValueError("Owner approval token missing")
 with tempfile.TemporaryDirectory() as tmp:
  aab=bundle_file(Path(tmp))
  if args.apply:deploy(aab)
  else:print("DRY_RUN=SUCCESS",flush=True)
if __name__=="__main__":
 try:main()
 except Exception as exc:
  print("RIVOSCAN_04526_PUBLISH_ERROR="+type(exc).__name__+": "+str(exc)[:350],file=sys.stderr)
  raise SystemExit(1)
