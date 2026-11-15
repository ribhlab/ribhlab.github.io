#!/usr/bin/env python3
"""Replace ONLY RivoScan v0.45.35 Google Play promotional images.

Safety: require confirmed current Production version 139, exact package,
image type en-US only, and owner authorization. No bundle, track, textual
listing, data-safety, or icon modifications. All images committed atomically.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
from pathlib import Path

PACKAGE="com.ribhlab.rivoscan"
VERSION=139
CONFIRM="PUBLISH_RIVOSCAN_04535_ATTRACTIVE_MEDIA"
NAMES=("01_Home","02_Documents","03_Tools","04_Book_Scan",
       "05_Formula_OCR","06_Photo_Translation","07_ID_Photo","08_Settings")
SLOTS={
 "featureGraphic":("feature-1024x500.png",),
 "phoneScreenshots":tuple("phone/"+x+".png" for x in NAMES),
 "sevenInchScreenshots":tuple("sevenInch/"+x+".png" for x in NAMES),
 "tenInchScreenshots":tuple("tenInch/"+x+".png" for x in NAMES),
}
DIMS={"featureGraphic":(1024,500),"phoneScreenshots":(1080,1920),
      "sevenInchScreenshots":(1080,1920),"tenInchScreenshots":(1536,2560)}


def validate(root:Path):
 from PIL import Image
 manifest=json.loads((root/"manifest.json").read_text(encoding="utf8"))
 if manifest.get("version")!="0.45.35":
  raise ValueError("Not RivoScan 0.45.35 promotional graphics")
 all_hashes=[]
 for kind,names in SLOTS.items():
  for name in names:
   f=root/name
   if not f.is_file():
    raise ValueError("Missing promotional asset "+str(f))
   if f.stat().st_size<15000 or f.stat().st_size>8_000_000:
    raise ValueError("Google Play image file too small or >8 MB: "+str(f))
   with Image.open(f) as im:
    if im.format!="PNG" or im.size!=DIMS[kind]:
     raise ValueError("Unexpected PNG size for "+str(f))
   digest=hashlib.sha256(f.read_bytes()).hexdigest()
   expected=[x for x in manifest["files"] if x.get("name")==name]
   if len(expected)!=1 or expected[0].get("sha256")!=digest:
    raise ValueError("Checksum mismatch for "+name)
   all_hashes.append(digest)
 if len(all_hashes)!=25 or len(set(all_hashes))!=25:
  raise ValueError("Screenshots are missing or duplicated")
 print("RIVOSCAN_PROMO_VALIDATED="+json.dumps(
     {"versionCode":VERSION,"promotionalImages":len(all_hashes),
      "counts":{key:len(names) for key,names in SLOTS.items()}},sort_keys=True),flush=True)


def publish(root:Path):
 from googleapiclient.discovery import build
 from googleapiclient.http import MediaFileUpload
 from publish import get_credentials
 edits=build("androidpublisher","v3",credentials=get_credentials(),cache_discovery=False).edits()
 eid=edits.insert(packageName=PACKAGE,body={}).execute()["id"]
 committed=False
 try:
  tracks=edits.tracks().list(packageName=PACKAGE,editId=eid).execute().get("tracks",[])
  production=[x for t in tracks if t.get("track")=="production"
              for x in t.get("releases",[])]
  if len(production)!=1 or production[0].get("status")!="completed" or \
      [str(v) for v in production[0].get("versionCodes",[])]!=["139"]:
   raise RuntimeError("Production no longer serves exactly RivoScan versionCode 139; stop")
  print("RIVOSCAN_PROMO_PRODUCTION_VERIFIED="+json.dumps(
     {"versionCode":139,"status":"completed"}),flush=True)
  previous={}
  for kind in SLOTS:
   previous[kind]=len(edits.images().list(
      packageName=PACKAGE,editId=eid,language="en-US",imageType=kind
      ).execute().get("images",[]))
  for kind,names in SLOTS.items():
   edits.images().deleteall(packageName=PACKAGE,editId=eid,
                            language="en-US",imageType=kind).execute()
   for name in names:
    path=root/name
    edits.images().upload(packageName=PACKAGE,editId=eid,language="en-US",
                         imageType=kind,
                         media_body=MediaFileUpload(str(path),mimetype="image/png",
                                                    resumable=False)).execute()
   count=len(edits.images().list(packageName=PACKAGE,editId=eid,
                                language="en-US",imageType=kind
                                ).execute().get("images",[]))
   if count!=len(names):
    raise RuntimeError("Google Play failed to store "+kind+" count "+str(count))
   print("RIVOSCAN_PROMO_IMAGES_UPLOADED="+json.dumps({
      "category":kind,"count":count,"previousCount":previous[kind]}),flush=True)
  edits.validate(packageName=PACKAGE,editId=eid).execute()
  edits.commit(packageName=PACKAGE,editId=eid).execute()
  committed=True
  print("RIVOSCAN_PROMO_COMMITTED="+json.dumps({
   "package":PACKAGE,"versionCode":VERSION,
   "featureGraphic":1,"phoneScreenshots":8,"sevenInchScreenshots":8,
   "tenInchScreenshots":8,"productionBinaryUnchanged":True,
   "localizedTextUnchanged":True,"iconUnchanged":True,
   "dataSafetyUnchanged":True,"reviewMayBeRequired":True}),flush=True)
 finally:
  if not committed:
   try:edits.delete(packageName=PACKAGE,editId=eid).execute()
   except Exception:print("WARNING: uncommitted edit cleanup failed",file=sys.stderr)


def main():
 p=argparse.ArgumentParser()
 p.add_argument("--media-dir",type=Path,default=Path("/tmp/rivoscan-promo"))
 p.add_argument("--apply",action="store_true")
 p.add_argument("--confirm",default="")
 args=p.parse_args()
 validate(args.media_dir)
 if not args.apply:
  print("RIVOSCAN_PROMO_DRY_RUN_OK=True",flush=True)
  return
 if args.confirm!=CONFIRM:
  raise ValueError("Owner confirmation token required")
 publish(args.media_dir)


if __name__=="__main__":
 try:main()
 except Exception as e:
  print("RIVOSCAN_PROMO_FAILED="+json.dumps({
   "error":type(e).__name__,"message":str(e)[:350],
   "httpStatus":getattr(getattr(e,"resp",None),"status",None)}),file=sys.stderr)
  raise SystemExit(1)
