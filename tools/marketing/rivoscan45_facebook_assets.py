#!/usr/bin/env python3
"""Build Facebook assets from verified RivoScan 0.45.40 source screenshots.

Never crop or stretch app screenshots. Source: GitHub Actions artifact run 43876459718.
The screenshots are app WebView captures, not demonstrations of native camera/OCR results.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import shutil
import hashlib

ROOT=Path(__file__).resolve().parents[2]
SRC=Path('/tmp/rivo-04540/phone/phone')
OUTPUT=ROOT/'public/rivoscan/social/04540'
ICON=Path('/tmp/rivo-04540/rivoscan-icon.png')
OUTPUT.mkdir(parents=True,exist_ok=True)
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

def ft(size,bold=False): return ImageFont.truetype(BOLD if bold else FONT,size)
def txt(d,xy,value,size,color='#082a54',bold=False): d.text(xy,value,font=ft(size,bold),fill=color)
def background(size):
    w,h=size; im=Image.new('RGB',size)
    d=ImageDraw.Draw(im)
    for y in range(h):
        t=y/max(1,h-1)
        d.line((0,y,w,y),fill=(int(249-25*t),int(253-19*t),255))
    d.ellipse((int(.7*w),-int(.12*h),int(1.4*w),int(.6*h)),fill='#d4f6ff')
    d.ellipse((-int(.4*w),int(.8*h),int(.3*w),int(1.5*h)),fill='#d6efff')
    return im
def source(name):
    p=SRC/(name+'.png')
    im=Image.open(p).convert('RGB')
    if im.size!=(1080,1920) or p.stat().st_size<15000: raise ValueError('Invalid verified source '+str(p))
    return im
def screenshot(name,h):
    im=source(name);w=round(h*1080/1920)
    im=im.resize((w,h),Image.Resampling.LANCZOS)
    output=Image.new('RGBA',(w+20,h+20),(0,0,0,0))
    m=Image.new('L',(w,h));dr=ImageDraw.Draw(m);dr.rounded_rectangle((0,0,w-1,h-1),radius=18,fill=255)
    output.paste(im,(10,10),m)
    ImageDraw.Draw(output).rounded_rectangle((7,7,w+12,h+12),radius=22,outline='#1c6294',width=5)
    return output
rows=[
('01_Home','01_Scan_to_PDF','SCAN TO PDF','Capture documents on Android'),
('02_Documents','02_Organize','ORGANIZE FILES','Browse and search your PDFs'),
('03_Tools','03_Tools','PDF & SCANNER TOOLS','Find the tools you need'),
('04_Book_Scan','04_Book_Scan','BOOK SCAN','Scan book pages'),
('05_Formula_OCR','05_Formula_OCR','FORMULA OCR','Recognize math text'),
('06_Photo_Translation','06_Photo_Translation','PHOTO TRANSLATION','Extract and translate text'),
('07_ID_Photo','07_ID_Photo','ID PHOTO','Prepare ID photo layouts'),
('08_Settings','08_Settings','APP SETTINGS','Customize your preferences'),
]
for src,slug,headline,desc in rows:
    im=background((1080,1350));d=ImageDraw.Draw(im)
    d.rounded_rectangle((45,44,1035,1305),radius=40,outline='#b7ddeb',width=3)
    txt(d,(78,75),'RivoScan  |  Android',43,bold=True)
    txt(d,(78,164),headline,56,bold=True)
    txt(d,(80,255),desc,31,color='#2e6e94')
    shot=screenshot(src,930);im.paste(shot,(510,318),shot)
    d.rounded_rectangle((75,447,465,620),radius=25,fill='#ffffff',outline='#b8def1',width=2)
    txt(d,(96,477),'ORIGINAL APP UI',27,bold=True)
    txt(d,(97,541),'Version 0.45.40',21,color='#3d7297')
    d.rounded_rectangle((78,749,441,839),radius=30,fill='#0768bb')
    txt(d,(116,777),'GOOGLE PLAY',29,color='#ffffff',bold=True)
    txt(d,(82,1139),'Scan  •  Organize  •  Read',22,bold=True)
    txt(d,(83,1196),'Source: original 0.45.40 WebView',16,color='#5b7891')
    im.save(OUTPUT/(slug+'.jpg'),quality=94,optimize=True)
    source(src).save(OUTPUT/(src+'.png'),optimize=True)
# cover: use full screenshots, never crop
im=Image.new('RGB',(1640,624));d=ImageDraw.Draw(im)
for y in range(624):
    t=y/624
    d.line((0,y,1640,y),fill=(int(5+7*t),int(35+71*t),int(83+90*t)))
d.rounded_rectangle((57,93,730,532),radius=33,fill='#114780',outline='#2e7cba',width=3)
txt(d,(97,150),'RivoScan',94,'#ffffff',True)
txt(d,(98,268),'SCAN  •  ORGANIZE  •  READ',28,'#d0f5ff',True)
txt(d,(98,321),'OCR  •  PDF  •  TOOLS',28,'#7defed',True)
txt(d,(100,424),'Android document toolkit',24,'#ffffff')
for i,n in enumerate(['01_Home','02_Documents','03_Tools']):
    shot=screenshot(n,456)
    im.paste(shot,(792+i*281,81),shot)
im.save(OUTPUT/'Facebook_Cover_1640x624.jpg',quality=95,optimize=True)
# latest source icon (do not use older illustration)
orig=Image.open(ICON).convert('RGBA')
logo=background((1080,1080))
# large icon centered with ample margins for circular Facebook crop
orig.thumbnail((835,835),Image.Resampling.LANCZOS)
logo.paste(orig,((1080-orig.width)//2,(1080-orig.height)//2),orig)
logo.save(OUTPUT/'Facebook_Profile_1080x1080.png',optimize=True)
manifest={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUTPUT.iterdir() if p.is_file()}
import json
(OUTPUT/'manifest.json').write_text(json.dumps({'version':'0.45.40','source':'Verified WebView screenshots from GitHub Actions run 43876459718','image_sha256':manifest},indent=2)+'\n')
print('RIVOSCAN_FACEBOOK_REAL_UI_ASSETS_READY:',len(manifest))
