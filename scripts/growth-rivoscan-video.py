from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import sys,json
p=Path(sys.argv[1]);o=Path(sys.argv[2]);o.mkdir(parents=True,exist_ok=True)
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';bold='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
items=[('01_Home.png','Paper to PDF','Scan documents with your phone'),('02_Documents.png','Find your files','Keep documents organized'),('03_Tools.png','More PDF tools','Merge, manage pages and more'),('04_Book_Scan.png','Book scanning','Split facing pages'),('06_Photo_Translation.png','Photo translation','Explore text recognition tools'),('01_Home.png','Get RivoScan','Available on Google Play')]
for i,(file,title,subtitle) in enumerate(items):
 im=Image.new('RGB',(720,1280),'#0c2549');d=ImageDraw.Draw(im)
 d.rounded_rectangle((22,22,698,1258),radius=32,fill='#122f57',outline='#467bb1',width=2)
 d.text((360,52),'RivoScan',font=ImageFont.truetype(bold,38),anchor='mt',fill='white')
 d.text((360,113),title,font=ImageFont.truetype(bold,39),anchor='mt',fill='#a9deff')
 d.text((360,169),subtitle,font=ImageFont.truetype(font,22),anchor='mt',fill='white')
 pic=Image.open(p/file).convert('RGB');pic.thumbnail((535,940),Image.Resampling.LANCZOS)
 x=(720-pic.width)//2;y=224
 d.rounded_rectangle((x-9,y-9,x+pic.width+9,y+pic.height+9),radius=17,fill='#061328')
 im.paste(pic,(x,y));d.text((360,1186),'Actual app screenshots · v0.45.95',font=ImageFont.truetype(font,20),anchor='mt',fill='#d5e6f4')
 d.text((360,1224),'Search RivoScan on Google Play',font=ImageFont.truetype(bold,20),anchor='mt',fill='#99d7ff')
 im.save(o/f'{i:02}.png')
