#!/usr/bin/env python3
"""Render and upload a 1024x500 RGB RivoScan Google Play feature graphic.

Illustrative promotional artwork only; NOT a purported screenshot.
No AAB, IARC, Data Safety, release track or other metadata is changed.
"""
from __future__ import annotations
import argparse
import json
import math
import sys
import tempfile
from pathlib import Path

WIDTH, HEIGHT, SCALE = 1024, 500, 2
PACKAGE = "com.ribhlab.rivoscan"


def _font(size: int, bold: bool = False):
    from PIL import ImageFont
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def make_graphic(path: Path) -> Path:
    from PIL import Image, ImageDraw, ImageFilter
    w, h = WIDTH * SCALE, HEIGHT * SCALE
    base = Image.new("RGB", (w, h))
    dr = ImageDraw.Draw(base)
    # Deep midnight-blue-to-turquoise layered gradient.
    for y in range(h):
        t = y / h
        for x in range(0, w, 5):
            z = x / w
            c = (round(3 + 8 * (1-t) + 6*z),
                 round(23 + 18 * (1-t) + 16*z),
                 round(39 + 15 * (1-t) + 6*z))
            dr.rectangle((x, y, min(x+4,w), y), fill=c)
    # Soft localized illumination, as rendered layers rather than transparent final output.
    glow = Image.new("RGBA", (w, h))
    g = ImageDraw.Draw(glow)
    g.ellipse((-320, -400, 580, 370), fill=(3, 236, 216, 87))
    g.ellipse((1350, 590, 2300, 1400), fill=(0, 210, 200, 72))
    g.ellipse((1200, -390, 1900, 270), fill=(12, 137, 183, 58))
    glow = glow.filter(ImageFilter.GaussianBlur(150))
    base = Image.alpha_composite(base.convert("RGBA"), glow)
    layer = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(layer)
    # Grounding wave and subtle luminous diagram paths.
    for offset in range(6):
        pts=[]
        for x in range(0,w,10):
            y=925 + 40*math.sin((x-120)/255) - 25*math.sin(x/570) + offset*5
            pts.append((x,int(y)))
        d.line(pts, fill=(29, 225, 219, max(3,44-offset*7)), width=3)
    # Five small document-utility symbols, no app icons or store badges.
    d.rounded_rectangle((92, 102, 345, 150), radius=24, fill=(10,139,147,76), outline=(58,222,213,110), width=2)
    d.text((111, 110), "DOCUMENT TOOLKIT", font=_font(24,True), fill=(160,250,241,255))
    # Main wordmark: prioritize strong legibility in Google Play previews.
    big=_font(145,True)
    text_y=222
    d.text((88,text_y),"Rivo",font=big,fill=(245,251,255,255),stroke_width=0)
    x2=88+int(d.textlength("Rivo",font=big))-8
    d.text((x2,text_y),"Scan",font=big,fill=(30,238,223,255))
    # Three verbs rather than a long sales promise.
    d.text((100,410),"SCAN  •  EDIT  •  SHARE",font=_font(58,False),fill=(231,249,255,255))
    d.text((100,522),"Capture documents. Organize PDFs.",font=_font(29,False),fill=(186,216,226,255))
    # Simple feature chips
    chips=[("SCAN DOCUMENTS",100,778),("PDF TOOLS",410,671),("OCR TEXT",698,602)]
    for label,x,width in chips:
        d.rounded_rectangle((x,657,x+width//2,733),radius=33,
                fill=(9,81,91,218),outline=(39,181,192,160),width=2)
        d.text((x+25,677),label,font=_font(23,True),fill=(223,252,251,255))
    # Floating document cards, illustrative not screenshots.
    d.rounded_rectangle((1745,295,1990,700),radius=36,fill=(225,249,252,215),outline=(56,242,226,145),width=5)
    d.rounded_rectangle((1745,295,1989,354),radius=26,fill=(13,193,197,255))
    d.text((1792,310),"PDF",font=_font(34,True),fill="white")
    for y in (393,436,479,522,565):
        d.rounded_rectangle((1779,y,1944-(y-393)//3,y+12),radius=6,fill=(75,139,156,190))
    # Smartphone with glows and shadow (right, angled-in feeling without fake UI).
    shadow=Image.new("RGBA",(w,h))
    s=ImageDraw.Draw(shadow)
    s.rounded_rectangle((1215,70,1755,906),radius=95,fill=(0,0,0,215))
    base=Image.alpha_composite(base,shadow.filter(ImageFilter.GaussianBlur(40)))
    d=ImageDraw.Draw(layer)
    d.rounded_rectangle((1224,54,1755,901),radius=91,fill=(4,14,26,255),
                        outline=(94,226,236,220),width=12)
    d.rounded_rectangle((1250,88,1729,858),radius=68,fill=(22,70,83,255),
                        outline=(65,124,137,210),width=3)
    d.rounded_rectangle((1406,100,1573,118),radius=10,fill=(3,18,28,255))
    # Camera/desk preview area with paper and scan accents.
    d.rounded_rectangle((1291,165,1689,766),radius=23,fill=(16,105,112,255))
    d.rounded_rectangle((1346,222,1642,672),radius=18,fill=(231,247,249,255))
    for y,length in [(272,216),(310,180),(348,220),(386,205),(424,220),
                     (462,200),(500,211),(538,168),(576,211)]:
        d.rounded_rectangle((1382,y,1382+length,y+12),radius=5,fill=(101,154,171,235))
    # Camera crop brackets around the paper.
    cyan=(40,255,235,255)
    for (x,y,sx,sy) in [(1324,201,1,1),(1665,201,-1,1),(1324,690,1,-1),(1665,690,-1,-1)]:
        d.line([(x,y+sy*56),(x,y),(x+sx*57,y)],fill=cyan,width=13,joint="curve")
    d.line([(1296,482),(1690,482)],fill=(27,251,228,195),width=13)
    d.ellipse((1441,781,1539,879),fill=(249,255,255,255),outline=(3,220,205,255),width=8)
    # Decorative cyan orbit and tiny scanner crosshairs.
    d.arc((1102,420,1972,945),15,168,fill=(31,225,218,160),width=7)
    for x,y in [(1114,297),(1862,151),(1910,777)]:
        d.ellipse((x-5,y-5,x+5,y+5),fill=(54,236,235,165))
    base=Image.alpha_composite(base,layer).convert("RGB")
    base=base.resize((WIDTH,HEIGHT),Image.Resampling.LANCZOS)
    path.parent.mkdir(parents=True,exist_ok=True)
    base.save(path,format="JPEG",quality=90,optimize=True,subsampling=0)
    with Image.open(path) as check:
        if check.size!=(WIDTH,HEIGHT) or check.mode!="RGB":
            raise ValueError("Invalid output graphic size or transparency")
    return path


def upload(path: Path) -> dict:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from publish import get_credentials
    service = build("androidpublisher","v3",credentials=get_credentials(),cache_discovery=False)
    edits=service.edits()
    edit=edits.insert(packageName=PACKAGE,body={}).execute()
    eid=edit["id"]
    committed=False
    try:
        current=edits.images().list(packageName=PACKAGE,editId=eid,
                                    language="en-US",imageType="featureGraphic").execute()
        if current.get("images"):
            return {"result":"ALREADY_PRESENT_NO_CHANGES","count":len(current["images"])}
        data=edits.images().upload(
            packageName=PACKAGE,editId=eid,language="en-US",imageType="featureGraphic",
            media_body=MediaFileUpload(str(path),mimetype="image/jpeg",resumable=False)
        ).execute()
        edits.validate(packageName=PACKAGE,editId=eid).execute()
        edits.commit(packageName=PACKAGE,editId=eid).execute()
        committed=True
        return {"result":"FEATURE_GRAPHIC_COMMITTED","package":PACKAGE,
                "language":"en-US","imageId":data.get("id",""),
                "dimensions":"1024x500","format":"JPEG"}
    finally:
        if not committed:
            try:
                edits.delete(packageName=PACKAGE,editId=eid).execute()
            except Exception:
                print("WARNING: could not clean up temporary Play edit",file=sys.stderr)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output",default="tools/play-publisher/output/RivoScan_Feature_Graphic_1024x500.jpg")
    ap.add_argument("--apply",action="store_true")
    ap.add_argument("--confirm",default="")
    a=ap.parse_args()
    try:
        p=make_graphic(Path(a.output))
        if not a.apply:
            print(json.dumps({"result":"GRAPHIC_GENERATED_ONLY","path":str(p),
                              "pixels":"1024x500"}))
            return 0
        if a.confirm!="UPLOAD_FEATURE_GRAPHIC":
            raise ValueError("Missing explicit UPLOAD_FEATURE_GRAPHIC confirmation")
        print(json.dumps(upload(p),ensure_ascii=False))
        return 0
    except Exception as exc:
        status=getattr(getattr(exc,"resp",None),"status",None)
        print(f"FEATURE_GRAPHIC_FAILED: {type(exc).__name__}, Google HTTP={status}",
              file=sys.stderr)
        return 1

if __name__=="__main__":
    sys.exit(main())
