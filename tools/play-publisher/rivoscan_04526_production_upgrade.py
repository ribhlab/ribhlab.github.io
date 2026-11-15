#!/usr/bin/env python3
"""Publish already-verified RivoScan 0.45.26 (130) to the existing production track.
No AAB upload, no metadata/graphics/video changes, no user-fraction experiment.
Require exact serving v129 production and completed v130 testing proof.
"""
from __future__ import annotations
import argparse,json
from googleapiclient.discovery import build
from publish import get_credentials
APP="com.ribhlab.rivoscan"
EXPECTED=130
def run(confirm:str):
 if confirm!="PUBLISH_SIGNED_RIVOSCAN_130_PRODUCTION":raise ValueError("Explicit production authorization required")
 edits=build("androidpublisher","v3",credentials=get_credentials(),cache_discovery=False).edits()
 eid=edits.insert(packageName=APP,body={}).execute()["id"];committed=False
 try:
  tracks=edits.tracks().list(packageName=APP,editId=eid).execute().get("tracks",[])
  track_map={x.get("track"):x.get("releases",[]) for x in tracks}
  production=track_map.get("production",[])
  if len(production)!=1 or production[0].get("status")!="completed" or [str(v) for v in production[0].get("versionCodes",[])]!=["129"]:
   raise RuntimeError("Production has changed since audit; no automatic overwrite. Current releases: "+
                      json.dumps([{"codes":r.get("versionCodes"),"status":r.get("status")} for r in production]))
  if not any(str(EXPECTED) in [str(v) for v in r.get("versionCodes",[])] and r.get("status")=="completed"
             for t in ("alpha","beta","qa","internal") for r in track_map.get(t,[])):
   raise RuntimeError("v130 not yet validated on a completed test track; stop")
  bundle=edits.bundles().list(packageName=APP,editId=eid).execute().get("bundles",[])
  if EXPECTED not in {int(x["versionCode"]) for x in bundle if "versionCode" in x}:
   raise RuntimeError("Original-key v130 AAB not uploaded or not saved")
  listing=edits.listings().get(packageName=APP,editId=eid,language="en-US").execute()
  if listing.get("video"):raise RuntimeError("Outdated YouTube preview was restored; stop")
  for image_type,expected in [("icon",1),("featureGraphic",1),("phoneScreenshots",8)]:
   images=edits.images().list(packageName=APP,editId=eid,language="en-US",imageType=image_type).execute().get("images",[])
   if len(images)!=expected:raise RuntimeError("Published AI images not present: "+image_type)
  notes="New large blue R launcher icon without the small RivoScan wordmark. Improved visibility on Android home screens. Existing scanning, OCR and PDF tools remain available."
  edits.tracks().update(packageName=APP,editId=eid,track="production",body={
   "track":"production","releases":[{"name":"RivoScan 0.45.26 – New Icon",
    "versionCodes":[str(EXPECTED)],"status":"completed",
    "releaseNotes":[{"language":"en-US","text":notes}]}]}).execute()
  edits.validate(packageName=APP,editId=eid).execute()
  edits.commit(packageName=APP,editId=eid).execute();committed=True
  print("RIVOSCAN_PRODUCTION_RESULT="+json.dumps({"result":"COMMITTED","package":APP,
   "track":"production","versionCode":130,"status":"completed","replacedVersion":129,
   "aabUploadedEarlier":True,"iconChangedInBundle":True,"playImagesUnchanged":True,
   "videoStillRemoved":True,"pendingGoogleReview":True}),flush=True)
 finally:
  if not committed:
   try:edits.delete(packageName=APP,editId=eid).execute()
   except Exception:pass
if __name__=="__main__":
 a=argparse.ArgumentParser();a.add_argument("--confirm",default="")
 args=a.parse_args();run(args.confirm)
