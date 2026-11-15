#!/usr/bin/env python3
"""RivoScan 0.45.25 marketing media built from exact, actual WebView captures.
No fabricated OCR/camera result. Google Play media upload is one transactional edit.
The preview MP4 is for GitHub Release; Google Play requires a separate YouTube URL.
"""
from __future__ import annotations
import argparse, hashlib, json, subprocess, shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

APP="com.ribhlab.rivoscan"
VERSION_CODE="129"
APPROVED_ICON_SHA="35ade99dba942696056a24fd25a1fb8a26c2094b7f5d24c8d43f23665a7d0d14"
TITLE=[
 ("SCAN DOCUMENTS","Capture pages and save PDFs"),
 ("ALL FILES IN ONE PLACE","Find and organize documents"),
 ("POWERFUL PDF TOOLS","Convert, edit and share your files"),
 ("BOOK SCANNING","Work with facing-page scans"),
 ("FORMULA OCR","Read math expressions (beta)"),
 ("PHOTO TRANSLATION","Extract and translate text"),
 ("ID PHOTO TOOLS","Make and export ID photo sheets"),
 ("PERSONAL SETTINGS","Your app, your preferences")
]
DEVICE_SPECS=[
 ("Phone","phone",(1080,1920),"phoneScreenshots"),
 ("Tablet7","7-inch",(1080,1920),"sevenInchScreenshots"),
 ("Tablet10","10-inch",(1536,2560),"tenInchScreenshots")
]
def font(size):
 for name in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf","/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"]:
  if Path(name).exists():return ImageFont.truetype(name,size)
 return ImageFont.load_default()
def bg(w,h):
 grad=Image.linear_gradient("L").resize((w,h))
 im=ImageOps.colorize(grad,black="#061936",white="#135ab1").convert("RGBA")
 glow=Image.new("RGBA",(w,h));d=ImageDraw.Draw(glow)
 d.ellipse((int(w*.43),int(h*.05),int(w*1.25),int(h*.5)),fill=(8,235,255,120))
 d.ellipse((-int(w*.5),int(h*.55),int(w*.65),int(h*1.22)),fill=(0,132,246,100))
 glow=glow.filter(ImageFilter.GaussianBlur(max(20,w//7)))
 im=Image.alpha_composite(im,glow)
 d=ImageDraw.Draw(im)
 for j in range(7):
  y=int(h*(.84+j*.018))
  d.arc((-w//3,y-w//4,w*13//10,y+w//5),3,170,fill=(40,224,253,max(40,170-j*22)),width=max(2,w//500))
 return im
def load_source(src,device_label):
 assert src.is_dir(),f"Source UI screenshots missing: {src}"
 files=sorted(src.glob("*.png"))
 assert len(files)==8,(src,len(files))
 return files
def make_screenshots(source_root,out,icon):
 for store_folder,label,size,image_type in DEVICE_SPECS:
  original_root=source_root/("phone" if label=="phone" else "tablet")/label
  originals=load_source(original_root,label)
  w,h=size;folder=out/store_folder;folder.mkdir(parents=True,exist_ok=True)
  for idx,path in enumerate(originals):
   source=Image.open(path).convert("RGB")
   # The unaltered UI pixels are never retouched; the surrounding frame is
   # clearly promotional artwork rather than a fabricated Android screenshot.
   assert source.size==size,(str(path),source.size,size)
   im=bg(w,h);d=ImageDraw.Draw(im)
   title,subtitle=TITLE[idx]
   heading=int(w*.052) if len(title)<19 else int(w*.043)
   d.text((int(w*.07),int(h*.075)),title,fill="white",font=font(heading))
   d.text((int(w*.07),int(h*.121)),subtitle,fill="#c5f8ff",font=font(int(w*.024)))
   mark=icon.resize((int(w*.095),int(w*.095)),Image.Resampling.LANCZOS)
   im.alpha_composite(mark,(int(w*.83),int(h*.024)))
   display_width=int(w*.755)
   display_height=round(display_width*source.height/source.width)
   bound=int(h*.74)
   if display_height>bound:
    display_height=bound
    display_width=round(display_height*source.width/source.height)
   photo=source.resize((display_width,display_height),Image.Resampling.LANCZOS).convert("RGBA")
   x=(w-display_width)//2;y=int(h*.2)
   d.rounded_rectangle((x-10,y-10,x+display_width+10,y+display_height+10),
     radius=max(18,w//28),fill="#0c326a",outline="#4be3ee",width=max(3,w//300))
   im.alpha_composite(photo,(x,y))
   out_file=folder/(f"{idx+1:02d}_"+path.stem[3:]+".png")
   im.convert("RGB").save(out_file,optimize=True)
   with Image.open(out_file) as verify:
    assert verify.size==size and verify.mode=="RGB"
   print("MEDIA_READY",image_type,out_file.name,flush=True)
def feature_graphic(out,icon):
 w,h=1024,500;canvas=bg(w,h)
 d=ImageDraw.Draw(canvas)
 d.rounded_rectangle((44,61,128,145),radius=18,fill="#ffffff")
 mark=icon.resize((78,78),Image.Resampling.LANCZOS)
 canvas.alpha_composite(mark,(47,64))
 d.text((153,74),"RivoScan",font=font(50),fill="#ffffff")
 d.rounded_rectangle((51,184,142,190),radius=3,fill="#28e5f1")
 d.text((50,218),"SCAN SMARTER.",font=font(42),fill="#ffffff")
 d.text((50,274),"ORGANIZE FASTER.",font=font(35),fill="#a2f4ff")
 d.text((55,386),"PDF SCANNER  •  OCR  •  PDF TOOLS",font=font(19),fill="#d9f7ff")
 # Illustrative sheets, NOT an invented app feature screenshot.
 for k,(x,y) in enumerate([(715,106),(742,91),(770,80)]):
  d.rounded_rectangle((x,y,x+172,y+287),radius=20,fill=("#c0e9ff" if k<2 else "#eafbff"),outline="#58c7ff",width=5)
  for q in range(4):
   d.rounded_rectangle((x+26,y+45+q*38,x+139,y+52+q*38),radius=4,fill="#309bd4")
 d.line((701,342,979,342),fill="#24efff",width=7)
 pic=out/"RivoScan_Feature_Graphic_1024x500.jpg"
 canvas.convert("RGB").save(pic,quality=92,optimize=True,subsampling=0)
 print("MEDIA_READY featureGraphic",pic.name,flush=True)
 return pic
def promo_video(out,sources):
 scenes=out/"Promo-Scenes";scenes.mkdir(parents=True,exist_ok=True)
 for idx,index in enumerate([0,2,3,4,5,6],1):
  photo=Image.open(sources[index]).convert("RGB")
  canvas=bg(1280,720);d=ImageDraw.Draw(canvas)
  d.text((62,96),"RivoScan",font=font(76),fill="white")
  title,subtitle=TITLE[index]
  d.text((67,287),title,font=font(40 if len(title)<20 else 33),fill="#ffffff")
  d.text((68,375),subtitle,font=font(20),fill="#d8f7ff")
  d.text((68,642),"SCAN   ·   ORGANIZE   ·   EDIT",font=font(18),fill="#a5f8ff")
  target_h=610;target_w=round(target_h*photo.width/photo.height)
  screenshot=photo.resize((target_w,target_h),Image.Resampling.LANCZOS)
  x=900-target_w//2;y=58
  d.rounded_rectangle((x-8,y-8,x+target_w+8,y+target_h+8),radius=18,
    fill="#113d7c",outline="#34e6ff",width=5)
  canvas.alpha_composite(screenshot.convert("RGBA"),(x,y))
  canvas.convert("RGB").save(scenes/f"{idx:02d}.jpg",quality=88,optimize=True)
 inputs=[]
 for pic in sorted(scenes.glob("*.jpg")):
  inputs += ["-framerate","25","-loop","1","-t","3","-i",str(pic)]
 filters=[]
 for i in range(6):
  filters.append(f"[{i}:v]fps=25,trim=duration=3,setpts=PTS-STARTPTS,fade=t=in:st=0:d=0.3,fade=t=out:st=2.65:d=0.3,format=yuv420p[v{i}]")
 filters.append("".join(f"[v{i}]" for i in range(6))+"concat=n=6:v=1:a=0[final]")
 video=out/"RivoScan_0.45.25_App_Preview_16x9.mp4"
 subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y",*inputs,
  "-filter_complex",";".join(filters),"-map","[final]","-c:v","libx264",
  "-preset","veryfast","-crf","23","-pix_fmt","yuv420p",
  "-movflags","+faststart","-an",str(video)],check=True)
 assert video.stat().st_size>100000
 print("MEDIA_READY video",video,flush=True)
def prepare(src,out):
 out.mkdir(parents=True,exist_ok=True)
 icon_path=src/"public/rivoscan-icon.png"
 raw=icon_path.read_bytes()
 if hashlib.sha256(raw).hexdigest()!=APPROVED_ICON_SHA:
  raise RuntimeError("RivoScan icon SHA changed; refusing to publish a wrong icon")
 icon=Image.open(icon_path).convert("RGBA")
 assert icon.size==(512,512)
 shutil.copyfile(icon_path,out/"RivoScan_Icon_512x512.png")
 make_screenshots(src,out,icon)
 feature_graphic(out,icon)
 promo_video(out,load_source(src/"phone"/"phone","phone"))
 manifest={"app":APP,"versionCode":129,"sourceCommit":"ea135957e63008ccd296a0b9b3dc36d27cb03e5b",
  "iconSHA256":APPROVED_ICON_SHA,
  "deviceImageCounts":{type:len(list((out/folder).glob("*.png"))) for folder,_,_,type in DEVICE_SPECS},
  "note":"Screenshots use the actual v0.45.25 WebView interface. Marketing frames are labelled with truthful UI features. Android native camera and ads are not simulated.",
  "video":"MP4 published as GitHub Release asset only. To show preview video in Play, upload MP4 to YouTube then add URL to listing."}
 (out/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
 print("PREPARED",json.dumps(manifest),flush=True)
def publish(out,confirm):
 if confirm!="UPLOAD_RIVOSCAN_04525_MEDIA":
  raise ValueError("Explicit required confirmation")
 from googleapiclient.discovery import build
 from googleapiclient.http import MediaFileUpload
 from publish import get_credentials
 assert hashlib.sha256((out/"RivoScan_Icon_512x512.png").read_bytes()).hexdigest()==APPROVED_ICON_SHA
 service=build("androidpublisher","v3",credentials=get_credentials(),cache_discovery=False)
 edits=service.edits()
 edit=edits.insert(packageName=APP,body={}).execute()
 eid=edit["id"];committed=False
 try:
  # Never touch the release track, its status or version codes.
  visible=set()
  for track in edits.tracks().list(packageName=APP,editId=eid).execute().get("tracks",[]):
   for rel in track.get("releases",[]):
    visible.update(str(code) for code in rel.get("versionCodes",[]))
  if VERSION_CODE not in visible:
   raise RuntimeError("Version 129 is not saved in a Play track; refusing to update a different release")
  slots={"icon":[out/"RivoScan_Icon_512x512.png"],
    "featureGraphic":[out/"RivoScan_Feature_Graphic_1024x500.jpg"]}
  slots.update({image_type:sorted((out/folder).glob("*.png")) for folder,_,_,image_type in DEVICE_SPECS})
  for kind,pictures in slots.items():
   expected=1 if kind in ("icon","featureGraphic") else 8
   if len(pictures)!=expected:raise RuntimeError("Invalid source image count "+kind)
   edits.images().deleteall(packageName=APP,editId=eid,language="en-US",imageType=kind).execute()
   for pic in pictures:
    mime="image/jpeg" if pic.suffix.lower()==".jpg" else "image/png"
    edits.images().upload(packageName=APP,editId=eid,language="en-US",imageType=kind,
       media_body=MediaFileUpload(str(pic),mimetype=mime,resumable=False)).execute()
   count=len(edits.images().list(packageName=APP,editId=eid,language="en-US",imageType=kind).execute().get("images",[]))
   if count!=expected:raise RuntimeError(f"Upload count mismatch for {kind}: {count}")
   print("PLAY_MEDIA_VERIFIED",kind,count,flush=True)
  edits.validate(packageName=APP,editId=eid).execute()
  edits.commit(packageName=APP,editId=eid).execute()
  committed=True
  print("RIVOSCAN_MEDIA_PUBLISHED="+json.dumps({"result":"COMMITTED","package":APP,
   "language":"en-US","versionCode":129,"imageTypes":list(slots),
   "phone":8,"tablet7":8,"tablet10":8,"feature":1,"icon":1,
   "tracksChanged":False,"aabChanged":False,"videoYouTubeUrlAdded":False}),flush=True)
 finally:
  if not committed:
   try:edits.delete(packageName=APP,editId=eid).execute()
   except Exception:pass
def main():
 parser=argparse.ArgumentParser()
 parser.add_argument("--prepare",action="store_true")
 parser.add_argument("--source",type=Path)
 parser.add_argument("--output",type=Path,default=Path("/tmp/rivoscan-media"))
 parser.add_argument("--apply",action="store_true")
 parser.add_argument("--confirm",default="")
 args=parser.parse_args()
 if args.prepare:
  if not args.source:parser.error("--source is required to render")
  prepare(args.source,args.output)
 if args.apply:publish(args.output,args.confirm)
if __name__=="__main__":
 main()
