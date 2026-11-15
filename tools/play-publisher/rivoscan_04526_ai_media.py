#!/usr/bin/env python3
"""RivoScan 0.45.26: AI artwork + REAL live app UI screenshots, safely publish.
Use only owner-approved graphics. Screenshots embed real current WebView captures
because Google Play requires screenshots to show the actual in-app experience.
No fake native OCR, camera, ad, or file-processing results are asserted.
Publisher commits images/icon and clears user-requested preview video; no track writes.
"""
from __future__ import annotations
import argparse, hashlib, io, json, sys, tempfile, shutil
from pathlib import Path
from urllib.request import Request, urlopen
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
APP="com.ribhlab.rivoscan"
LANGUAGE="en-US"
VIDEO_TO_REMOVE="https://www.youtube.com/watch?v=pC1USZxFvbk"
MEDIA=[
 ("scan","https://gcdn.picsart.com/picsart-mcp/b4459af3-01f1-484c-a4a9-fd2973764197.png","84fb124c7cbd244ce3447edf05818505650e84d9ba22948fc19641cbc5a55f95"),
 ("organize","https://gcdn.picsart.com/picsart-mcp/5930d6db-194b-4c0d-83c6-9d52c8b5f61b.png","d095cd63f05f17f54f00a643cdba1b4312ba5d2073605734a72544e8b2d5de13"),
 ("ocr","https://gcdn.picsart.com/picsart-mcp/0c16020d-b524-4d4d-b835-f009b88e89e5.png","e1c99a0500762e72cc617b858a0dfc4a847e46822a312156bcd9fd4c81671d7d"),
 ("qr","https://gcdn.picsart.com/picsart-mcp/cb83f45d-3c29-40dd-83b7-5075ceceda15.png","857310077f2ae20f911adbebe807490ede864dc86ab274f65eb1b7bbc06671ef"),
 ("pdf","https://gcdn.picsart.com/picsart-mcp/3693ed77-ff55-424f-8d2d-ddcfacdbfb02.png","2dd5b624a1f3b5ad4eeddd2ff06dbf56b6c5390d87bb555d8b7fa05da0c0d65f"),
 ("privacy","https://gcdn.picsart.com/picsart-mcp/050385a6-df44-43cb-b5dd-e139c2724ff8.png","26132d16133bd9089e11298d391a960cbdf1fed87fe967e5330c44e9cd5a01fd"),
 ("books","https://gcdn.picsart.com/picsart-mcp/aff8db0a-94a4-4684-9807-cb4696b62300.png","d7fcdc166b06a1180a2d57b50f59131b6b0f79a209e6eaef781368993a785e66"),
 ("share","https://gcdn.picsart.com/picsart-mcp/3399ab07-273c-4a39-af14-37aa56bcabe4.png","405a09984c6b7bce41eeb9d75412ccb297583a12606824597bc83903bfb0cd4a")
]
FEATURE=("https://gcdn.picsart.com/picsart-mcp/4604674a-85db-47b8-bf3d-41a116f8a5a7.png","27a1059e639e377f734786e5ecdab2a99c835b1eba9ea9ef52a4d69fb5b773b6")
DEVICE=[
 ("phone","phone",(1080,1920),"phoneScreenshots"),
 ("tablet","7-inch",(1080,1920),"sevenInchScreenshots"),
 ("tablet","10-inch",(1536,2560),"tenInchScreenshots")
]
def approved(url,sha):
 for retry in range(3):
  try:
   with urlopen(Request(url,headers={"User-Agent":"RivoScan-approved-publishing/0.45.26"}),timeout=45) as r:
    body=r.read(10000000)
   digest=hashlib.sha256(body).hexdigest()
   if digest!=sha:raise RuntimeError("Owner asset checksum mismatch: "+sha[:10]+" got "+digest[:10])
   image=Image.open(io.BytesIO(body));image.load()
   return image.convert("RGB")
  except Exception as e:
   if retry==2:raise
   import time;time.sleep(retry+1)
def font(size):
 for f in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf","/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"]:
  if Path(f).exists():return ImageFont.truetype(f,size)
 return ImageFont.load_default()
def crop_to(im,w,h):
 source=im.convert("RGB")
 ratio=max(w/source.width,h/source.height)
 rw=round(source.width*ratio);rh=round(source.height*ratio)
 return ImageOps.fit(source,(w,h),method=Image.Resampling.LANCZOS,centering=(.5,.5))
def genuine_screens(root,area,folder,target):
 images=sorted((root/area/folder).glob("*.png"))
 if len(images)!=8:raise RuntimeError(f"Need all 8 genuine {area}/{folder} captures; got {len(images)}")
 for f in images:
  with Image.open(f) as im:
   if im.size!=target:raise RuntimeError(f"Wrong actual screenshot size {f}: {im.size}")
 return images
def create_overlay(poster,real,device,output):
 w,h=device
 art=crop_to(poster,w,h).convert("RGBA")
 actual=Image.open(real).convert("RGB")
 # Real latest UI occupies a visibly labeled central display; the surrounding
 # AI poster is only promotional art and never misrepresented as a screenshot.
 new_h=int(h*.60)
 new_w=round(new_h*actual.width/actual.height)
 x=(w-new_w)//2
 y=int(h*.365)
 shot=actual.resize((new_w,new_h),Image.Resampling.LANCZOS).convert("RGBA")
 dark=Image.new("RGBA",(w,h))
 d=ImageDraw.Draw(dark)
 border=max(7,w//135)
 d.rounded_rectangle((x-border,y-border,x+new_w+border,y+new_h+border),
  radius=max(19,w//27),fill=(5,23,56,255),outline=(45,238,250,255),width=border)
 art=Image.alpha_composite(art,dark)
 art.alpha_composite(shot,(x,y))
 draw=ImageDraw.Draw(art)
 label="Real RivoScan app interface  ·  AI illustrative background"
 f=font(max(13,w//65));width=draw.textlength(label,font=f)
 if width>w-20:
  label="Real app interface · AI illustration"
  width=draw.textlength(label,font=f)
 xy=((w-width)/2,int(h*.984)-f.size)
 draw.rounded_rectangle((max(5,xy[0]-12),xy[1]-5,min(w-5,xy[0]+width+12),xy[1]+f.size+8),radius=6,fill=(1,22,50,220))
 draw.text(xy,label,font=f,fill=(235,255,255,255))
 output.parent.mkdir(parents=True,exist_ok=True)
 art.convert("RGB").save(output,optimize=True)
 with Image.open(output) as verify:
  assert verify.size==(w,h) and verify.mode=="RGB"
def make_feature(ai,icon,path):
 w,h=1024,500
 texture=crop_to(ai,w,h).filter(ImageFilter.GaussianBlur(43)).convert("RGB")
 # Remove all synthetic phone UI from the featureGraphic: it is a pure AI art
 # background, a real approved icon, and brand text, as Play recommends.
 b=Image.new("RGBA",(w,h));d=ImageDraw.Draw(b)
 d.rectangle((0,0,w,h),fill=(4,25,70,165))
 b=Image.alpha_composite(texture.convert("RGBA"),b)
 d=ImageDraw.Draw(b)
 im=icon.convert("RGBA").resize((316,316),Image.Resampling.LANCZOS)
 b.alpha_composite(im,(650,86))
 d.text((54,120),"RivoScan",font=font(79),fill="#ffffff")
 d.text((58,254),"Scan smarter.",font=font(42),fill="#d6fbff")
 d.text((58,315),"Organize faster.",font=font(39),fill="#d6fbff")
 d.rounded_rectangle((58,386,565,393),radius=3,fill="#2deffc")
 path.parent.mkdir(parents=True,exist_ok=True)
 b.convert("RGB").save(path,quality=93,optimize=True,subsampling=0)
 assert Image.open(path).size==(1024,500)
def prepare(source,out):
 if not (source/"public/rivoscan-store-icon.png").is_file():
  raise RuntimeError("App prebuild did not generate the approved new Play icon")
 app_version=json.loads((source/"package.json").read_text())["version"]
 if app_version!="0.45.26":raise RuntimeError("Do not use another RivoScan app version: "+app_version)
 icon=Image.open(source/"public/rivoscan-store-icon.png").convert("RGB")
 assert icon.size==(512,512)
 out.mkdir(parents=True,exist_ok=True)
 icon.save(out/"RivoScan_Play_Icon_512.png",optimize=True)
 posters=[approved(url,sha) for _,url,sha in MEDIA]
 feature=approved(*FEATURE)
 make_feature(feature,icon,out/"RivoScan_Feature_Graphic_1024x500.jpg")
 for sub,folder,dim,kind in DEVICE:
  real=genuine_screens(source,sub,folder,dim)
  for i,(name,_,_) in enumerate(MEDIA):
   outfile=out/kind/f"{i+1:02d}_{name}_real_ui_ai_art.png"
   create_overlay(posters[i],real[i],dim,outfile)
   print("PREPARED",kind,outfile.name,flush=True)
 audit={"package":APP,"version":"0.45.26","code":130,
   "icon":"512x512 full-bleed no text","feature":"1024x500 AI background, real app brand",
   "phoneScreenshots":8,"sevenInchScreenshots":8,"tenInchScreenshots":8,
   "allPosterIllustrations":"Owner-approved AI backgrounds, plus current-version actual UI capture",
   "video":"removed; user will make a new video","storeLanguage":"en-US",
   "signedAAB":"NOT changed by this metadata-only script"}
 (out/"verified_media_manifest.json").write_text(json.dumps(audit,indent=2)+"\n")
 print("RIVOSCAN_04526_MEDIA_READY="+json.dumps(audit),flush=True)
def publish(media):
 from googleapiclient.discovery import build
 from googleapiclient.http import MediaFileUpload
 from publish import get_credentials
 edits=build("androidpublisher","v3",credentials=get_credentials(),cache_discovery=False).edits()
 eid=edits.insert(packageName=APP,body={}).execute()["id"]
 committed=False
 try:
  current=edits.listings().get(packageName=APP,editId=eid,language=LANGUAGE).execute()
  files={
    "icon":[media/"RivoScan_Play_Icon_512.png"],
    "featureGraphic":[media/"RivoScan_Feature_Graphic_1024x500.jpg"]
  }
  for _,_,_,kind in DEVICE:
   files[kind]=sorted((media/kind).glob("*.png"))
  for kind,pics in files.items():
   expected=1 if kind in ("icon","featureGraphic") else 8
   if len(pics)!=expected:raise RuntimeError(f"Missing {kind} assets {len(pics)}")
   edits.images().deleteall(packageName=APP,editId=eid,language=LANGUAGE,imageType=kind).execute()
   for pic in pics:
    mime="image/jpeg" if pic.suffix==".jpg" else "image/png"
    edits.images().upload(packageName=APP,editId=eid,language=LANGUAGE,imageType=kind,
      media_body=MediaFileUpload(str(pic),mimetype=mime,resumable=False)).execute()
   result=edits.images().list(packageName=APP,editId=eid,language=LANGUAGE,imageType=kind).execute()
   actual=len(result.get("images",[]))
   if actual!=expected:raise RuntimeError(f"{kind}: expected {expected} uploaded, got {actual}")
   print("PLAY_IMAGE_VERIFIED",kind,actual,flush=True)
  # The owner explicitly withdrew the existing preview video. Empty string
  # removes it while all other fields remain unchanged.
  listing=edits.listings().patch(packageName=APP,editId=eid,language=LANGUAGE,
      body={"video":""}).execute()
  if listing.get("video",""):
   raise RuntimeError("Google Play did not clear preview video")
  for key in ("title","shortDescription","fullDescription"):
   if listing.get(key)!=current.get(key):
    raise RuntimeError("Play store description changed unexpectedly: "+key)
  edits.validate(packageName=APP,editId=eid).execute()
  edits.commit(packageName=APP,editId=eid).execute()
  committed=True
  print("RIVOSCAN_04526_PLAY_MEDIA_COMMITTED="+json.dumps({
    "result":"COMMITTED","package":APP,"language":LANGUAGE,
    "icon":1,"featureGraphic":1,"phoneScreenshots":8,
    "sevenInchScreenshots":8,"tenInchScreenshots":8,"previewVideo":"",
    "releaseTrackChanged":False,"aabChanged":False,
    "listingDescriptionsChanged":False
  }),flush=True)
 finally:
  if not committed:
   try:edits.delete(packageName=APP,editId=eid).execute()
   except Exception:pass
def main():
 parser=argparse.ArgumentParser()
 parser.add_argument("--source",type=Path)
 parser.add_argument("--output",type=Path,default=Path("/tmp/rivoscan-04526-play"))
 parser.add_argument("--prepare",action="store_true")
 parser.add_argument("--publish",action="store_true")
 parser.add_argument("--confirm",default="")
 args=parser.parse_args()
 if args.prepare:prepare(args.source,args.output)
 if args.publish:
  if args.confirm!="PUBLISH_RIVOSCAN_04526_OWNER_AI_MEDIA_REMOVE_VIDEO":
   raise ValueError("Explicit owner approval constant required")
  publish(args.output)
if __name__=="__main__":main()
