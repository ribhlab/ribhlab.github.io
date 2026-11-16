"""Produce Facebook-ready images using verbatim RivoScan 0.45.40 WebView capture artifact.
Screens are proportionally scaled, never redrawn or cropped.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import os, hashlib, json
source=Path(os.environ.get('RIVO_CAPTURE_DIR','/tmp/rivo-screens'))/'phone/phone'
output=Path('public/rivoscan/facebook-04540')
output.mkdir(parents=True,exist_ok=True)
iconpath=Path('public/rivoscan/icon.png')
if not iconpath.exists(): raise RuntimeError('Missing official RivoScan icon')
icon=Image.open(iconpath).convert('RGBA')
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'; BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def font(size,bold=False): return ImageFont.truetype(BOLD if bold else FONT,size)
def background(w,h,a=(5,28,80),b=(0,113,187)):
 from PIL import Image
 im=Image.new('RGB',(w,h));pix=im.load()
 for y in range(h):
  for x in range(w):
   t=.35*x/w+.65*y/h;pix[x,y]=tuple(round(v+(z-v)*t) for v,z in zip(a,b))
 return im

def rr(d,rect,fill,r=20): d.rounded_rectangle(rect,radius=r,fill=fill)
def paste_icon(canvas,xy,s):
 ico=icon.resize((s,s),Image.Resampling.LANCZOS);canvas.paste(ico,xy,ico)
files=['01_Home.png','02_Documents.png','03_Tools.png','04_Book_Scan.png','05_Formula_OCR.png','06_Photo_Translation.png','07_ID_Photo.png','08_Settings.png']
labels=[('SCAN TO PDF','Start scanning documents','The RivoScan home screen'),('ORGANIZE FILES','Keep your documents together','Search, sort and open PDF files'),('DOCUMENT TOOLS','Discover scanning and OCR tools','Useful Android document features'),('BOOK SCAN','Capture facing pages','Split and flatten book scans'),('FORMULA OCR','Recognize mathematical formulas','Edit extracted text and LaTeX'),('PHOTO TRANSLATION','OCR and offline translation','Select languages and recognize text'),('ID PHOTO MAKER','Create ID photo layouts','Adjust dimensions and crop settings'),('APP SETTINGS','Adapt scanning preferences','Choose language and other settings')]
screens={}; hashes={}
for name in files:
 p=source/name
 if not p.is_file():raise RuntimeError('Missing verified screenshot '+str(p))
 im=Image.open(p).convert('RGB')
 if im.size!=(1080,1920):raise RuntimeError('Unexpected screenshot dimensions '+str(im.size))
 screens[name]=im;hashes[name]=hashlib.sha256(p.read_bytes()).hexdigest()
# Square profile. The entire existing icon is retained.
im=background(1080,1080);d=ImageDraw.Draw(im)
d.ellipse((70,70,1010,1010),outline='#55e2ea',width=10)
paste_icon(im,(190,190),700)
im.save(output/'RivoScan_Profile_1080.png',optimize=True)
# Banner with three raw captures. No screen crop, distortion or text re-paint.
im=background(1640,624);d=ImageDraw.Draw(im)
paste_icon(im,(64,54),110)
d.text((192,64),'RivoScan',font=font(61,True),fill='white')
d.text((70,226),'Scan  •  Organize',font=font(39,True),fill='white')
d.text((70,280),'Read  •  OCR',font=font(39,True),fill='#69fff2')
d.text((70,376),'Smart document tools for Android',font=font(22),fill='#ebf9ff')
rr(d,(70,447,374,508),'#10e4dd',22);d.text((104,467),'Get it on Google Play',font=font(19,True),fill='#032f59')
d.text((70,548),'UI screens: RivoScan 0.45.40',font=font(15),fill='#d9f5ff')
for idx,name in enumerate(files[:3]):
 raw=screens[name];height=520;width=round(1080*height/1920);x=709+idx*294;y=51+(idx%2)*17
 rr(d,(x-8,y-8,x+width+8,y+height+8),'#e4f5ff',15)
 im.paste(raw.resize((width,height),Image.Resampling.LANCZOS),(x,y))
im.save(output/'RivoScan_Facebook_Cover_1640x624.jpg',quality=92,optimize=True,subsampling=0)
# Individual 4:5 portraits: entire captured UI within each asset.
for n,(name,(title,desc,small)) in enumerate(zip(files,labels),1):
 w,h=1080,1350;im=background(w,h);d=ImageDraw.Draw(im)
 rr(d,(33,28,1047,1325),'#f6fbff',34)
 paste_icon(im,(63,51),77)
 d.text((156,48),'RivoScan',font=font(32,True),fill='#082657')
 d.text((156,94),'Android document toolkit',font=font(16),fill='#487198')
 d.text((66,153),title,font=font(39,True),fill='#073d84')
 d.text((67,216),desc,font=font(23),fill='#28658c')
 sh=975;sw=round(1080*sh/1920);x=(w-sw)//2;y=288
 rr(d,(x-15,y-14,x+sw+15,y+sh+14),'#cee5f3',20)
 im.paste(screens[name].resize((sw,sh),Image.Resampling.LANCZOS),(x,y))
 d.text((65,1286),small,font=font(17,True),fill='#11507c')
 d.text((958,1287),f'{n}/8',font=font(13),fill='#5288ae')
 im.save(output/f'RivoScan_04540_{n:02d}_{name.replace(".png", "")}_1080x1350.jpg',quality=92,subsampling=0,optimize=True)
meta={'source_version':'0.45.40','raw_source_run_id':43876459718,'artifact_id':14231200039,'source':'RivoScan-04540-Actual-UI-Raw-Screenshots','screens':hashes,'method':'All screenshots preserved without cropping, distortions or generated content. Photo layout and branding added around them.'}
(output/'asset-source.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')
print('RIVOSCAN_LATEST_FB_ASSETS_READY',len(list(output.iterdir())))
