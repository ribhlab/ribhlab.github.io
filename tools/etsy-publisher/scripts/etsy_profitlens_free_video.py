"""Create and upload one silent, honest ProfitLens Etsy listing video from
Etsy's existing *public* product screenshots (no private buyer assets involved).

It does NOT create/change/renew listings, buy ads, change price or download files.
If any media/identity validation fails, it makes no listing changes.
"""
import io
import os
import sys
import json
import time
import subprocess
import tempfile
import urllib.parse
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter

from check_connection import verify, ConnectionErrorSafe

BASE="https://api.etsy.com/v3"
LID=4610490076
# Expected 64-bit dHash calculated from original user-supplied genuine product gallery.
PANELS=[
 (2,0x7034b5292b372569,"INVOICE AGING","Review outstanding receivables"),
 (4,0x7836b7093d3b3929,"CSV IMPORT","Load financial data locally"),
 (5,0x5830bd3d31352969,"DECISION SCENARIOS","Explore financial alternatives"),
 (9,0x5836b7393f372969,"JSON BACKUP","Keep and restore local data")
]
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def require(condition,msg):
    if not condition: raise ConnectionErrorSafe(msg)

def get(session,path):
    try:res=session.get(BASE+path,timeout=35,allow_redirects=False)
    except requests.RequestException:
        raise ConnectionErrorSafe("Etsy read failed due to connection error.") from None
    require(res.ok,"Etsy read rejected (HTTP "+str(res.status_code)+").")
    try:return res.json()
    except ValueError:raise ConnectionErrorSafe("Unexpected Etsy response.") from None

def dhash(im):
    image=ImageOps.exif_transpose(im).convert("L").resize((9,8),Image.Resampling.LANCZOS)
    values=list(image.getdata())
    return int("".join("1" if values[y*9+x]>values[y*9+x+1] else "0"
                        for y in range(8) for x in range(8)),2)

def draw_slide(image, heading, detail):
    W,H=1920,960
    bg=Image.new("RGB",(W,H),(9,27,39))
    d=ImageDraw.Draw(bg)
    for y in range(H):
        k=y/H
        d.line((0,y,W,y),fill=(int(7+8*k),int(23+19*k),int(38+27*k)))
    source=ImageOps.exif_transpose(image).convert("RGB")
    source.thumbnail((1170,850),Image.Resampling.LANCZOS)
    left=55+(1200-source.width)//2
    top=54+(850-source.height)//2
    shadow=Image.new("RGBA",(source.width+44,source.height+44),(0,0,0,0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        (18,18,source.width+26,source.height+26),radius=16,fill=(0,0,0,150))
    shadow=shadow.filter(ImageFilter.GaussianBlur(17))
    bg.paste(shadow,(left-20,top-20),shadow)
    bg.paste(source,(left,top))
    d.rounded_rectangle((left-2,top-2,left+source.width+2,top+source.height+2),
                        radius=6,outline=(92,166,155),width=3)
    x=1300
    d.rounded_rectangle((x,105,1800,147),radius=21,fill=(26,96,92))
    d.text((x+22,114),"RIBHLAB DIGITAL  •  DIGITAL DOWNLOAD",
           font=ImageFont.truetype(BOLD,17),fill=(174,239,225))
    y=205
    for wordline in [heading[i:i+19] for i in range(0,len(heading),19)]:
        d.text((x,y),wordline,font=ImageFont.truetype(BOLD,48),fill=(255,255,255))
        y+=75
    y=max(380,y+18)
    import textwrap
    for line in textwrap.wrap(detail,24):
        d.text((x,y),line,font=ImageFont.truetype(BOLD,28),fill=(117,226,203))
        y+=46
    d.line((x,688,1830,688),fill=(56,128,123),width=2)
    for i,feature in enumerate(("Browser-based HTML app","Works offline after download",
                                "No Excel file required")):
        y=730+i*51
        d.ellipse((x,y+4,x+14,y+18),fill=(88,217,175))
        d.text((x+28,y-1),feature,font=ImageFont.truetype(FONT,22),
               fill=(228,244,237))
    d.text((80,916),"REAL PRODUCT SCREENSHOTS   •   FICTIONAL DEMO DATA",
           font=ImageFont.truetype(BOLD,17),fill=(177,203,204))
    return bg

def main():
    shop=verify()
    key=os.environ["ETSY_KEYSTRING"]
    secret=os.environ["ETSY_SHARED_SECRET"]
    try:
        r=requests.post(BASE+"/public/oauth/token",
                        data={"grant_type":"refresh_token","client_id":key,
                              "refresh_token":os.environ["ETSY_REFRESH_TOKEN"]},
                        timeout=25)
    except requests.RequestException:
        raise ConnectionErrorSafe("Etsy token refresh unreachable.") from None
    require(r.ok,"Etsy token refresh denied.")
    access=r.json().get("access_token")
    require(access,"Etsy access token missing.")
    session=requests.Session()
    session.headers.update({"x-api-key":key+":"+secret,"Authorization":"Bearer "+access})
    active=get(session,f"/application/shops/{shop}/listings?state=active&limit=100").get("results",[])
    item=next((x for x in active if int(x.get("listing_id",0))==LID),None)
    require(item and str(item.get("shop_id"))==str(shop)
            and "Offline HTML Finance Dashboard" in item.get("title",""),
            "Target active ProfitLens HTML listing not found.")
    files=get(session,f"/application/shops/{shop}/listings/{LID}/files").get("results",[])
    require(len(files)>0,"No buyer file on listing; stopping.")
    existing=get(session,f"/application/listings/{LID}/videos").get("results",[])
    require(isinstance(existing,list),"Invalid existing-video response.")
    if any(x.get("video_state") in ("active","processing","pending") for x in existing):
        print("VIDEO_ALREADY_PRESENT_OR_PROCESSING",len(existing))
        print("NO_DUPLICATE_VIDEO_UPLOADED")
        return
    require(len(existing)==0,"Unexpected inactive videos; review first.")
    images=get(session,f"/application/listings/{LID}/images").get("results",[])
    rankmap={int(x.get("rank") or 0):x for x in images}
    require(len(images)==10,"ProfitLens photo gallery changed; refusing upload.")

    screenshots=[]
    for rank,expected,heading,detail in PANELS:
        info=rankmap.get(rank)
        require(info is not None,"Expected ProfitLens image rank not found.")
        url=info.get("url_fullxfull") or info.get("url_570xN")
        require(isinstance(url,str) and url.startswith("https://i.etsystatic.com/"),
                "Unexpected Etsy screenshot host.")
        try:res=requests.get(url,timeout=35)
        except requests.RequestException:
            raise ConnectionErrorSafe("Failed to retrieve Etsy product screenshot.") from None
        require(res.ok and 5000<len(res.content)<8*1024*1024,
                "Etsy product image download rejected.")
        try:img=Image.open(io.BytesIO(res.content))
        except Exception:raise ConnectionErrorSafe("Invalid image returned by Etsy.") from None
        distance=(dhash(img)^expected).bit_count()
        print("VERIFIED_SCREENSHOT_RANK",rank,"DIFFERENCE",distance)
        require(distance<=12,
                "Image rank "+str(rank)+" no longer matches the genuine product screenshot.")
        screenshots.append((img,heading,detail))

    with tempfile.TemporaryDirectory() as directory:
        temp=Path(directory)
        concat=[]
        for i,(img,heading,detail) in enumerate(screenshots):
            name=f"panel_{i:02d}.jpg"
            draw_slide(img,heading,detail).save(temp/name,quality=87)
            concat.append(f"file '{name}'\nduration 2.5\n")
        concat.append("file 'panel_03.jpg'\n")
        (temp/"video.txt").write_text("".join(concat),encoding="utf-8")
        video=temp/"ProfitLens_3_6_Real_Dashboard_Demo.mp4"
        subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y",
                        "-f","concat","-safe","0","-i",str(temp/"video.txt"),
                        "-r","12","-vf","format=yuv420p","-an","-c:v","libx264",
                        "-preset","veryfast","-crf","22","-movflags","+faststart",str(video)],
                        cwd=temp,check=True,timeout=120)
        require(video.stat().st_size<100*1024*1024,"Etsy video exceeds 100MB.")
        metadata=subprocess.check_output(["ffprobe","-v","error","-show_entries",
            "format=duration","-of","default=nokey=1:noprint_wrappers=1",str(video)],
            text=True,timeout=15).strip()
        secs=float(metadata)
        require(3<=secs<=15,"Listing video is outside Etsy 3–15 second requirements.")
        print("VIDEO_READY_DURATION",secs,"BYTES",video.stat().st_size)
        # Recheck immediately before upload to avoid a duplicate.
        again=get(session,f"/application/listings/{LID}/videos").get("results",[])
        require(not again,"Another video was added during generation; refusing duplicate.")
        with video.open("rb") as f:
            try:reply=session.post(
                BASE+f"/application/shops/{shop}/listings/{LID}/videos",
                data={"name":video.name},
                files={"video":(video.name,f,"video/mp4")},
                timeout=120,allow_redirects=False)
            except requests.RequestException:
                raise ConnectionErrorSafe("Upload request timed out; inspect video list before any retry.") from None
        require(reply.ok,"Etsy rejected listing video (HTTP "+str(reply.status_code)+").")
        try:obj=reply.json()
        except ValueError:raise ConnectionErrorSafe("Etsy video upload responded without JSON.") from None
        vid=obj.get("video_id")
        require(vid,"Etsy did not return a video ID.")
        print("VIDEO_UPLOADED_ID",vid)
        for i in range(7):
            current=get(session,f"/application/listings/{LID}/videos").get("results",[])
            entry=next((x for x in current if str(x.get("video_id"))==str(vid)),None)
            if entry and entry.get("video_state")=="active":
                print("VIDEO_CONFIRMED_ACTIVE",vid,"LISTING",LID)
                print("PROFITLENS_LISTING_URL https://www.etsy.com/listing/"+str(LID))
                return
            if entry:
                print("VIDEO_PROCESSING",str(entry.get("video_state")))
            time.sleep(4)
        raise ConnectionErrorSafe("Etsy accepted upload but has not confirmed active video.")

if __name__=="__main__":
    try:main()
    except ConnectionErrorSafe as err: print("VIDEO_JOB_FAILED:",err,file=sys.stderr);sys.exit(1)
    except Exception as err:
        print("VIDEO_JOB_FAILED: Unexpected "+type(err).__name__,file=sys.stderr);sys.exit(1)
