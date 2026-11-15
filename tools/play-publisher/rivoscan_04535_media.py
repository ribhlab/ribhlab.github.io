#!/usr/bin/env python3
"""Generate RivoScan v0.45.35 feature graphic from real app icon and current UI.

Do not fabricate live scanner images, ads, document contents or files.
The 24 store screenshots are captured by the official RivoScan Playwright scripts
and are copied byte-for-byte. This renders only the supplementary feature banner.
"""
from pathlib import Path
import argparse
import json
import shutil
from PIL import Image, ImageDraw, ImageFont

VIEWS=("01_Home","02_Documents","03_Tools","04_Book_Scan",
       "05_Formula_OCR","06_Photo_Translation","07_ID_Photo","08_Settings")
PALE=(230,244,255)
NAVY=(5,29,60)
CYAN=(49,227,226)


def font(size,bold=False):
    names=[
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for name in names:
        if Path(name).is_file():
            return ImageFont.truetype(name,size)
    return ImageFont.load_default()


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--app-dir",type=Path,default=Path("rivoscan-app"))
    p.add_argument("--output",type=Path,default=Path("/tmp/rivoscan-publish-media"))
    args=p.parse_args()
    out=args.output
    out.mkdir(parents=True,exist_ok=True)
    source=args.app_dir/"public/rivoscan-store-icon.png"
    if not source.is_file():
        source=args.app_dir/"public/rivoscan-icon.png"
    with Image.open(source) as im:
        if im.format!="PNG" or im.size!=(512,512):
            raise ValueError("Official source icon must be a 512x512 PNG")
    shutil.copy2(source,out/"app-icon-512.png")
    shotdir=out/"phone/phone"
    home=shotdir/"01_Home.png"
    docs=shotdir/"02_Documents.png"
    if not home.is_file() or not docs.is_file():
        raise ValueError("Source WebView screenshots have not been captured")
    width,height=1024,500
    background=Image.new("RGB",(width,height),NAVY)
    draw=ImageDraw.Draw(background)
    for x in range(width):
        t=x/(width-1)
        c=(int(5+5*t),int(28+83*t),int(60+102*t))
        draw.line((x,0,x,height),fill=c)
    draw=ImageDraw.Draw(background)
    icon=Image.open(source).convert("RGBA").resize((82,82),Image.Resampling.LANCZOS)
    background.paste(icon,(44,39),icon)
    draw.text((144,55),"RivoScan",font=font(51,True),fill="white")
    draw.text((45,180),"Scan smarter.",font=font(43,True),fill="white")
    draw.text((45,236),"Keep it private.",font=font(37,True),fill=CYAN)
    draw.rounded_rectangle((45,295,479,297),radius=1,fill=(52,198,227))
    for y,label in enumerate(["PDF SCANNER  /  EDITOR","QR  /  BARCODE","ORGANIZE  /  PROTECT"]):
        draw.text((48,330+y*39),label,font=font(17,True),fill=PALE)
    # Real unmodified screenshots are shown inside the two device frames.
    for i,source_path in enumerate([home,docs]):
        sx=618+i*133
        sy=20+i*32
        frameW=204
        frameH=431
        draw.rounded_rectangle((sx-8,sy-6,sx+frameW+8,sy+frameH+6),radius=22,
                               fill=(2,23,54),outline=(72,203,255),width=2)
        with Image.open(source_path) as im:
            real=im.convert("RGB").resize((frameW,frameH),Image.Resampling.LANCZOS)
        background.paste(real,(sx,sy))
        draw.rounded_rectangle((sx-8,sy-6,sx+frameW+8,sy+frameH+6),radius=22,
                               outline=(76,219,255),width=2)
    target=out/"feature-1024x500.png"
    background.save(target,optimize=True)
    index={
        "version":"0.45.35","versionCode":139,"feature":"actual 0.45.35 screenshots + RivoScan official source icon",
        "realUiScreenshotCounts":{"phone":8,"7-inch":8,"10-inch":8},
        "note":"No fabricated camera captures, files, native ads, or OCR outputs"}
    (out/"manifest.json").write_text(json.dumps(index,indent=2)+"\n",encoding="utf8")
    print("RIVOSCAN_MEDIA_PREPARED="+json.dumps(index),flush=True)


if __name__=="__main__":
    main()
