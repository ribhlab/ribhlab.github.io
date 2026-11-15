#!/usr/bin/env python3
"""Create appealing truthful RivoScan 0.45.35 Google Play promotional screenshots.

Every screen area contains the real, unmodified RivoScan 0.45.35 screenshot.
Only the surrounding framing, backgrounds and feature headlines are designed.
No scanner results, ads, users or sample files are fabricated. Source image
pixels come from the verified app build, not from AI-imagined interfaces.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

VIEWS = (
 ("01_Home","SCAN SMARTER","Your documents. One simple place.","AUTO SCAN  /  PDF"),
 ("02_Documents","STAY ORGANIZED","Find every document, faster.","SEARCH  /  IMPORT  /  FILES"),
 ("03_Tools","ONE APP. MORE TOOLS.","Scan, edit and convert PDFs.","PDF  /  QR  /  OCR"),
 ("04_Book_Scan","SCAN BOOK PAGES","A dedicated workspace for books.","BOOK SCANNER"),
 ("05_Formula_OCR","READ MATH FORMULAS","Turn math images into editable text.","MATH OCR  /  LATEX"),
 ("06_Photo_Translation","TRANSLATE PHOTOS","Recognize text and translate.","PHOTO  /  TEXT"),
 ("07_ID_Photo","MAKE ID PHOTOS","Prepare print-ready photo sheets.","ID PHOTO  /  PRINT"),
 ("08_Settings","SCAN YOUR WAY","Language, sound and privacy settings.","PREFERENCES  /  CONTROL"),
)
COLORS = ("#0be4fb","#52b6ff","#4ee7cf","#41caff","#8cc9ff","#5fd6f3","#6bd9fb","#93ecff")
DARK = (5,20,47)
WHITE = (249,252,255)
APP_VERSION = "0.45.35"


def font(size,bold=False):
    options = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
          else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold
          else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for fp in options:
        if Path(fp).is_file():
            return ImageFont.truetype(fp,size)
    return ImageFont.load_default()


def rgb(hexstr):
    return tuple(int(hexstr[i:i+2],16) for i in (1,3,5))


def background(w,h,highlight,seed=0):
    # Navy gradients, cyan light ribbons and luminous circles: consistent with
    # the RivoScan app's electric blue identity and current Play icon.
    strip=Image.new("RGB",(1,h))
    sp=strip.load()
    accent=rgb(highlight)
    for y in range(h):
        t=y/max(1,h-1)
        row=tuple(int(DARK[i]*(1-t)+(8,57,118)[i]*t) for i in range(3))
        sp[0,y]=tuple(min(255,int(row[i]*.87+accent[i]*.13)) for i in range(3))
    image=strip.resize((w,h),Image.Resampling.NEAREST)
    draw=ImageDraw.Draw(image,"RGBA")
    cx=int(w*(.83 if seed%2 else .23))
    cy=int(h*.48)
    for radius in (int(w*.75),int(w*.57),int(w*.42)):
        draw.ellipse((cx-radius,cy-radius,cx+radius,cy+radius),
                     outline=(*accent,34),width=max(2,w//200))
    draw.ellipse((-int(w*.5),int(h*.62),int(w*.65),int(h*1.28)),
                 outline=(*accent,100),width=max(4,w//145))
    draw.arc((-w//4,h//4,int(w*1.4),int(h*.98)),170,280,
             fill=(*accent,110),width=max(4,w//120))
    for col in range(10):
        for row in range(10):
            ox=int(w*.8+col*w*.021)
            oy=int(h*.08+row*w*.021)
            if ox<w and oy<h:
                r=max(1,w//450)
                draw.ellipse((ox-r,oy-r,ox+r,oy+r),fill=(*accent,72))
    bloom=Image.new("RGBA",(w,h),(0,0,0,0))
    bd=ImageDraw.Draw(bloom,"RGBA")
    bd.ellipse((int(w*.47),int(h*.52),int(w*1.3),int(h*1.11)),fill=(*accent,70))
    bloom=bloom.filter(ImageFilter.GaussianBlur(max(24,w//7)))
    return Image.alpha_composite(image.convert("RGBA"),bloom)


def paste_cover(bg,src,rect,radius):
    x,y,w,h=rect
    image=src.convert("RGB").resize((w,h),Image.Resampling.LANCZOS)
    mask=Image.new("L",(w,h),0)
    ImageDraw.Draw(mask).rounded_rectangle((0,0,w-1,h-1),radius=radius,fill=255)
    bg.paste(image,(x,y),mask)


def centered(draw,xy,text,**kwargs):
    font_obj=kwargs["font"]
    bounds=draw.textbbox((0,0),text,font=font_obj)
    x=xy[0]-(bounds[2]-bounds[0])/2
    draw.text((int(x),int(xy[1])),text,**kwargs)


def render_poster(source,icon,out,idx,target_size,kind):
    w,h=target_size
    title,headline,subline,tag=VIEWS[idx]
    accent=COLORS[idx]
    base=background(w,h,accent,idx)
    draw=ImageDraw.Draw(base,"RGBA")
    margin=int(w*.073)
    # Small brand row with exact app icon and a restrained identity.
    icon_size=int(w*.082)
    brand=icon.resize((icon_size,icon_size),Image.Resampling.LANCZOS)
    base.alpha_composite(brand,(margin,int(h*.039)))
    draw.text((margin+icon_size+int(w*.025),int(h*.052)),"RIVO SCAN",
              font=font(int(w*.041),True),fill=WHITE)
    draw.rounded_rectangle((int(w*.755),int(h*.047),int(w*.94),int(h*.086)),
                           radius=int(w*.015),fill=(17,115,182,105),
                           outline=(89,205,250,85),width=2)
    centered(draw,(int(w*.848),int(h*.055)),"PDF TOOLS",
             font=font(int(w*.020),True),fill=WHITE)
    top=int(h*.135)
    max_headline=int(w*.061)
    draw.text((margin,top),headline,font=font(max_headline,True),
              fill=WHITE,stroke_width=0)
    draw.text((margin,top+int(h*.061)),subline,
              font=font(int(w*.028),False),fill=(196,228,248,255))
    stroke_y=top+int(h*.105)
    draw.rounded_rectangle((margin,stroke_y,margin+int(w*.21),stroke_y+max(4,int(w*.009))),
                           radius=5,fill=(*rgb(accent),255))
    # Large app screenshot occupies 72% of the whole image; keep screenshot
    # unmodified so buyers can recognize the real application interface.
    max_h=int(h*.715)
    max_w=int(w*.84)
    ratio=source.width/source.height
    body_h=max_h
    body_w=int(body_h*ratio)
    if body_w>max_w:
        body_w=max_w
        body_h=int(body_w/ratio)
    x=(w-body_w)//2
    y=int(h*.254)
    pad=max(8,int(w*.010))
    radius=max(20,int(w*.037))
    # Drop shadow behind rounded phone frame.
    shadow=Image.new("RGBA",(w,h),(0,0,0,0))
    sd=ImageDraw.Draw(shadow,"RGBA")
    sd.rounded_rectangle((x-pad-10,y-pad+17,x+body_w+pad+10,y+body_h+pad+17),
                         radius=radius,fill=(0,0,0,180))
    shadow=shadow.filter(ImageFilter.GaussianBlur(max(12,w//35)))
    base=Image.alpha_composite(base,shadow)
    draw=ImageDraw.Draw(base,"RGBA")
    draw.rounded_rectangle((x-pad,y-pad,x+body_w+pad,y+body_h+pad),
                           radius=radius,fill=(2,22,50,255),
                           outline=(*rgb(accent),230),width=max(3,w//180))
    paste_cover(base,source,(x,y,body_w,body_h),max(12,radius-pad))
    # Bottom panel stays outside the untouched UI.
    foot_y=int(h*.958)
    centered(ImageDraw.Draw(base,"RGBA"),(w//2,foot_y),tag,
             font=font(int(w*.021),True),fill=(208,235,248,245))
    dest=out/(title+".png")
    base.convert("RGB").save(dest,format="PNG",optimize=True)
    if dest.stat().st_size>=7_800_000:
        raise ValueError(f"Graphic too large for Google Play: {dest}")
    return dest


def feature_graphic(out,phone_screens,icon):
    w,h=1024,500
    bg=background(w,h,"#19cfff",5)
    draw=ImageDraw.Draw(bg,"RGBA")
    icon_small=icon.resize((77,77),Image.Resampling.LANCZOS)
    bg.alpha_composite(icon_small,(53,51))
    draw.text((145,64),"RIVO SCAN",font=font(50,True),fill=WHITE)
    draw.text((54,180),"YOUR SCANS.",font=font(43,True),fill=WHITE)
    draw.text((54,243),"YOUR WORKFLOW.",font=font(37,True),fill=rgb("#49e7ec"))
    draw.rounded_rectangle((54,316,455,321),radius=2,fill=rgb("#29a9ec"))
    draw.text((55,342),"SCAN  •  EDIT  •  ORGANIZE",font=font(21,True),fill=(219,241,254,255))
    # Reduced but genuine screenshots preserve the source view, no fake UI.
    for name,x,y in [("01_Home",632,9),("02_Documents",790,39)]:
        with Image.open(phone_screens/name) as src:
            screenshot=src.convert("RGB")
        sw,sh=181,414
        draw.rounded_rectangle((x-8,y-6,x+sw+8,y+sh+6),radius=26,
                               fill=(0,21,45,255),outline=(75,230,255,210),width=3)
        paste_cover(bg,screenshot,(x,y,sw,sh),17)
    path=out/"feature-1024x500.png"
    bg.convert("RGB").save(path,optimize=True)
    return path


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",type=Path,default=Path("/tmp/rivoscan-publish-media"))
    parser.add_argument("--out",type=Path,default=Path("/tmp/rivoscan-promo"))
    args=parser.parse_args()
    source=args.source
    out=args.out
    out.mkdir(parents=True,exist_ok=True)
    icon_path=source/"app-icon-512.png"
    with Image.open(icon_path) as original:
        if original.size!=(512,512):
            raise ValueError("Official 512px app icon not found")
        icon=original.convert("RGBA")
    paths={}
    for dest_dir,src_dir,dimensions in (
        ("phone","phone/phone",(1080,1920)),
        ("sevenInch","tablet/7-inch",(1080,1920)),
        ("tenInch","tablet/10-inch",(1536,2560)),
    ):
        dest=out/dest_dir
        dest.mkdir(exist_ok=True)
        built=[]
        for idx,(name,_,_,_) in enumerate(VIEWS):
            original=source/src_dir/(name+".png")
            with Image.open(original) as im:
                if im.size!=dimensions:
                    raise ValueError(f"Original source screenshot wrong size: {original}")
                img=im.convert("RGB")
            built.append(render_poster(img,icon,dest,idx,dimensions,dest_dir))
        paths[dest_dir]=built
    with Image.open(source/"phone/phone/01_Home.png") as a:
        home=a.convert("RGB")
    with Image.open(source/"phone/phone/02_Documents.png") as a:
        docs=a.convert("RGB")
    feature=feature_graphic(out,{"01_Home":home,"02_Documents":docs},icon)
    all_files=[feature,*paths["phone"],*paths["sevenInch"],*paths["tenInch"]]
    fingerprints=[hashlib.sha256(p.read_bytes()).hexdigest() for p in all_files]
    if len(set(fingerprints))!=25:
        raise ValueError("Promotional images contain duplicates")
    record={
        "version":APP_VERSION,"screenshots":{k:len(v) for k,v in paths.items()},
        "featureGraphic":str(feature.name),
        "assetPolicy":"True source RivoScan 0.45.35 screenshot is preserved inside decorative framing; no fabricated interface",
        "files":[{"name":str(p.relative_to(out)),"size":p.stat().st_size,"sha256":sha}
                 for p,sha in zip(all_files,fingerprints)],
    }
    (out/"manifest.json").write_text(json.dumps(record,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print("RIVOSCAN_ATTRACTIVE_ASSETS="+json.dumps({
        "count":len(all_files),"screenshots":record["screenshots"],
        "version":APP_VERSION,"verified":True},sort_keys=True),flush=True)


if __name__=="__main__":
    main()
