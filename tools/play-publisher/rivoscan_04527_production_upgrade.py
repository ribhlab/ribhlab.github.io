#!/usr/bin/env python3
"""Publish already-verified RivoScan 0.45.27 (131) to the existing production track.
No AAB upload, no metadata/graphics/video changes, no user-fraction experiment.
Require exact serving v130 production and completed v131 testing proof.
"""
from __future__ import annotations
import argparse,json
from googleapiclient.discovery import build
from publish import get_credentials
APP="com.ribhlab.rivoscan"
EXPECTED=131
def run(confirm:str):
 if confirm!="PUBLISH_SIGNED_RIVOSCAN_131_PRODUCTION":raise ValueError("Explicit production authorization required")
 edits=build("androidpublisher","v3",credentials=get_credentials(),cache_discovery=False).edits()
 eid=edits.insert(packageName=APP,body={}).execute()["id"];committed=False
 try:
  tracks=edits.tracks().list(packageName=APP,editId=eid).execute().get("tracks",[])
  track_map={x.get("track"):x.get("releases",[]) for x in tracks}
  production=track_map.get("production",[])
  if len(production)!=1 or production[0].get("status")!="completed" or [str(v) for v in production[0].get("versionCodes",[])]!=["130"]:
   raise RuntimeError("Production has changed since audit; no automatic overwrite. Current releases: "+
                      json.dumps([{"codes":r.get("versionCodes"),"status":r.get("status")} for r in production]))
  if not any(str(EXPECTED) in [str(v) for v in r.get("versionCodes",[])] and r.get("status")=="completed"
             for t in ("alpha","beta","qa","internal") for r in track_map.get(t,[])):
   raise RuntimeError("v131 not yet validated on a completed test track; stop")
  bundle=edits.bundles().list(packageName=APP,editId=eid).execute().get("bundles",[])
  if EXPECTED not in {int(x["versionCode"]) for x in bundle if "versionCode" in x}:
   raise RuntimeError("Original-key v131 AAB not uploaded or not saved")
  listing=edits.listings().get(packageName=APP,editId=eid,language="en-US").execute()
  if listing.get("video"):raise RuntimeError("Outdated YouTube preview was restored; stop")
  for image_type,expected in [("icon",1),("featureGraphic",1),("phoneScreenshots",8)]:
   images=edits.images().list(packageName=APP,editId=eid,language="en-US",imageType=image_type).execute().get("images",[])
   if len(images)!=expected:raise RuntimeError("Published AI images not present: "+image_type)
  notes="Improved My Documents: Import images and Open phone folder now align with the title. Tighter controls, stable scrolling, and more room for saved documents."
  edits.tracks().update(packageName=APP,editId=eid,track="production",body={
   "track":"production","releases":[{"name":"RivoScan 0.45.27 – Compact Documents Layout",
    "versionCodes":[str(EXPECTED)],"status":"completed",
    "releaseNotes":[{"language":"en-US","text":notes}]}]}).execute()
  edits.validate(packageName=APP,editId=eid).execute()
  edits.commit(packageName=APP,editId=eid).execute();committed=True
  print("RIVOSCAN_PRODUCTION_RESULT="+json.dumps({"result":"COMMITTED","package":APP,
   "track":"production","versionCode":131,"status":"completed","replacedVersion":130,
   "aabUploadedEarlier":True,"compactHeaderChangedInBundle":True,"playImagesUnchanged":True,
   "videoStillRemoved":True,"pendingGoogleReview":True}),flush=True)
 finally:
  if not committed:
   try:edits.delete(packageName=APP,editId=eid).execute()
   except Exception:pass
if __name__=="__main__":
 a=argparse.ArgumentParser();a.add_argument("--confirm",default="")
 args=a.parse_args();run(args.confirm)
