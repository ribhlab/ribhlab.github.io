#!/usr/bin/env python3
"""Replace RivoScan Play marketing media with user-approved AI promotional artwork.
This intentionally does not call screenshots real screenshots, touch releases,
change binaries, legal declarations, or publish a YouTube preview.
"""
from __future__ import annotations
import argparse, io, json, sys, hashlib, urllib.request
from pathlib import Path
from PIL import Image, ImageOps, ImageFilter, ImageChops, ImageDraw
APP="com.ribhlab.rivoscan"
SOURCE=[
 ("icon","https://gcdn.picsart.com/picsart-mcp/ce5d87c2-dc15-45ff-8b58-16e8d5ac8fd7.png",(1254,1254)),
 ("01_scan","https://gcdn.picsart.com/picsart-mcp/1ded302e-f7dc-4b96-a7bb-0c4c2b73a83c.png",(941,1672)),
 ("02_organize","https://gcdn.picsart.com/picsart-mcp/9dfc311a-1c1a-4aba-85bd-0bc126a7cda0.png",(941,1672)),
 ("03_ocr","https://gcdn.picsart.com/picsart-mcp/a2750311-4030-4e72-8296-541c7f6d0141.png",(941,1672)),
 ("04_qr","https://gcdn.picsart.com/picsart-mcp/42a7d7ef-359f-402a-bf0f-b368974ae812.png",(941,1672)),
 ("05_pdf","https://gcdn.picsart.com/picsart-mcp/bf159088-241c-4374-813d-67a2ef596ff3.png",(941,1672)),
 ("06_privacy","https://gcdn.picsart.com/picsart-mcp/87c962fd-1136-4bde-a718-69ce04e276a0.png",(941,1672)),
 ("07_book","https://gcdn.picsart.com/picsart-mcp/d0066f2f-4ca3-4765-ad33-dbf222351299.png",(941,1672)),
 ("08_share","https://gcdn.picsart.com/picsart-mcp/14002fdb-9018-4c5d-812d-13de150397c8.png",(941,1672)),
 ("feature","https://gcdn.picsart.com/picsart-mcp/f740f824-c6f1-46d6-bcf7-6faf28592ff2.png",(1794,876))
]
def download(name,url,size):
 req=urllib.request.Request(url,headers={"User-Agent":"RivoScan-verified-store-publisher/1.0"})
 with urllib.request.urlopen(req,timeout=45) as response:
  raw=response.read(9_000_001)
 if not raw.startswith(b"\x89PNG\r\n\x1a\n") or len(raw)>9_000_000 or len(raw)<15_000:
  raise ValueError(f"Invalid or implausible original AI artwork: {name}")
 image=Image.open(io.BytesIO(raw)).convert("RGB")
 if image.size!=size:raise ValueError(f"Size mismatch for {name}: {image.size}, expected {size}")
 return image
def blue_icon(src):
 # Google's store icon must use ALL the 512x512 area. Remove source's black
 # corners using a luminance-independent (max RGB) matte, not a tiny transparent
 # launcher mask. Result: solid full-bleed blue square with large R mark.
 img=src.resize((512,512),Image.Resampling.LANCZOS)
 r,g,b=img.split()
 intensity=ImageChops.lighter(ImageChops.lighter(r,g),b)
 alpha=intensity.point(lambda v:int(max(0,min(255,(v-18)*255/65))))
 alpha=alpha.filter(ImageFilter.GaussianBlur(1))
 base=Image.new("RGB",(512,512))
 px=base.load()
 for y in range(512):
  for x in range(512):
   k=x/511
   px[x,y]=(int(5+6*k),int(49+82*k),int(178+50*k))
 base.paste(img,(0,0),alpha)
 return base
def prepare(out):
 out.mkdir(parents=True,exist_ok=True)
 originals={name:download(name,url,size) for name,url,size in SOURCE}
 icon=blue_icon(originals["icon"])
 icon.save(out/"RivoScan_Icon_512.png",format="PNG",optimize=True)
 feature=ImageOps.fit(originals["feature"],(1024,500),method=Image.Resampling.LANCZOS,centering=(.5,.5))
 feature.save(out/"RivoScan_Feature_1024x500.jpg",format="JPEG",quality=93,subsampling=0,optimize=True)
 targets={"phoneScreenshots":(1080,1920),"sevenInchScreenshots":(1080,1920),"tenInchScreenshots":(1440,2560)}
 for category,size in targets.items():
  folder=out/category;folder.mkdir(exist_ok=True)
  for index,(name,_,_) in enumerate(SOURCE[1:9],1):
   picture=ImageOps.fit(originals[name],size,method=Image.Resampling.LANCZOS)
   path=folder/(f"{index:02d}_{name}.jpg")
   picture.save(path,format="JPEG",quality=91,subsampling=0,optimize=True)
 manifest={"package":APP,"artwork":"AI-generated promotional renderings, not literal app screenshots",
  "name":"RivoScan 0.45.25 marketing refresh","icon":"full-bleed square, large R with no text",
  "feature":"1024x500","phone":8,"tablet7":8,"tablet10":8,"requestedVideo":"remove",
  "originalPhotosReplaced":True}
 (out/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf8")
 print("RIVOSCAN_AI_MEDIA_PREPARED="+json.dumps(manifest),flush=True)
def publish(out,confirm):
 if confirm!="REPLACE_RIVOSCAN_AI_MEDIA_AND_REMOVE_VIDEO":
  raise ValueError("Exact upload approval required")
 from googleapiclient.discovery import build
 from googleapiclient.http import MediaFileUpload
 from publish import get_credentials
 service=build("androidpublisher","v3",credentials=get_credentials(),cache_discovery=False)
 edits=service.edits()
 edit=edits.insert(packageName=APP,body={}).execute()
 eid=edit["id"];committed=False
 try:
  tracks=edits.tracks().list(packageName=APP,editId=eid).execute().get("tracks",[])
  # Track read-only, never overwrite its release or status.
  existing={str(v) for t in tracks for r in t.get("releases",[]) for v in r.get("versionCodes",[])}
  if "129" not in existing and "130" not in existing:
   raise RuntimeError("RivoScan 0.45.25/0.45.26 not on any saved Play track; stop")
  slots={"icon":[out/"RivoScan_Icon_512.png"],
         "featureGraphic":[out/"RivoScan_Feature_1024x500.jpg"]}
  for category in ("phoneScreenshots","sevenInchScreenshots","tenInchScreenshots"):
   slots[category]=sorted((out/category).glob("*.jpg"))
  for category,assets in slots.items():
   count_expected=1 if category in ("icon","featureGraphic") else 8
   if len(assets)!=count_expected:raise RuntimeError(f"Missing assets for {category}")
   edits.images().deleteall(packageName=APP,editId=eid,language="en-US",imageType=category).execute()
   for path in assets:
    edits.images().upload(packageName=APP,editId=eid,language="en-US",imageType=category,
     media_body=MediaFileUpload(str(path),
       mimetype="image/png" if path.suffix==".png" else "image/jpeg",resumable=False)).execute()
   stored=edits.images().list(packageName=APP,editId=eid,language="en-US",imageType=category).execute().get("images",[])
   if len(stored)!=count_expected:raise RuntimeError(f"Play image count mismatch: {category} {len(stored)}")
   print("PLAY_AI_IMAGE_VERIFIED",category,len(stored),flush=True)
  languages=[]
  for listing in edits.listings().list(packageName=APP,editId=eid).execute().get("listings",[]):
   language=listing.get("language")
   if language and listing.get("video"):
    result=edits.listings().patch(packageName=APP,editId=eid,language=language,body={"video":""}).execute()
    if result.get("video"):raise RuntimeError("Preview video not cleared for "+language)
    languages.append(language)
    print("PLAY_VIDEO_REMOVED",language,flush=True)
  edits.validate(packageName=APP,editId=eid).execute()
  edits.commit(packageName=APP,editId=eid).execute();committed=True
  print("RIVOSCAN_AI_PLAY_RESULT="+json.dumps({"result":"COMMITTED","package":APP,
   "language":"en-US","artwork":"AI","icon":1,"feature":1,"phone":8,"tablet7":8,
   "tablet10":8,"videoRemovedLanguages":languages,
   "aabChanged":False,"trackChanged":False,"listingTextChanged":False}),flush=True)
 finally:
  if not committed:
   try:edits.delete(packageName=APP,editId=eid).execute()
   except Exception:pass
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--prepare",action="store_true")
 p.add_argument("--apply",action="store_true")
 p.add_argument("--output",type=Path,default=Path("/tmp/rivoscan-ai-media"))
 p.add_argument("--confirm",default="")
 a=p.parse_args()
 if a.prepare:prepare(a.output)
 if a.apply:publish(a.output,a.confirm)
if __name__=="__main__":
 main()
