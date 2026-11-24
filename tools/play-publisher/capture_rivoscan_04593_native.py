#!/usr/bin/env python3
"""Capture actual signed RivoScan UI through ADB, not a recreated browser layout."""
import hashlib,json,re,subprocess,time,xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image,ImageStat,ImageChops
import argparse
P='com.ribhlab.rivoscan'
def adb(*args):
    return subprocess.check_output(['adb',*args],timeout=60)
def tree():
    for _ in range(4):
        try:
            adb('shell','uiautomator','dump','/sdcard/rivo04593.xml')
            return ET.fromstring(adb('exec-out','cat','/sdcard/rivo04593.xml'))
        except Exception:
            time.sleep(2)
    raise RuntimeError('Could not read live Android accessibility tree')
def labels(t):
    return [v for n in t.iter('node') for v in (n.get('text',''),n.get('content-desc','')) if v]
def find(t,label):
    nodes=[n for n in t.iter('node') if n.get('package')==P and any(v.strip().casefold()==label.casefold() for v in (n.get('text',''),n.get('content-desc','')))]
    nodes.sort(key=lambda n:n.get('clickable')!='true')
    return nodes[0] if nodes else None
def tap(label,optional=False):
    for _ in range(3):
        t=tree(); n=find(t,label)
        if n is not None:
            x1,y1,x2,y2=map(int,re.findall(r'\d+',n.get('bounds','')))
            if x2>x1 and y2>y1:
                adb('shell','input','tap',str((x1+x2)//2),str((y1+y2)//2)); time.sleep(2); return True
        time.sleep(1)
    if optional:return False
    raise RuntimeError('Live UI control not found: '+label+' / '+str(labels(t)[:35]))
def launch():
    adb('shell','am','force-stop',P)
    adb('shell','monkey','-p',P,'-c','android.intent.category.LAUNCHER','1');time.sleep(7)
def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--device',required=True);p.add_argument('--size',required=True);p.add_argument('--density',required=True);a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=True);w,h=map(int,a.size.split('x'))
    adb('shell','wm','size',a.size);adb('shell','wm','density',a.density)
    adb('shell','settings','put','system','screen_off_timeout','1800000')
    version=adb('shell','dumpsys','package',P).decode(errors='replace')
    if 'versionName=0.45.93' not in version or not re.search(r'versionCode=208\b',version):raise RuntimeError('Unexpected installed version')
    launch()
    if find(tree(),'Got it') is not None:tap('Got it')
    if find(tree(),'Close') is not None:tap('Close',optional=True)
    records=[]; previous=[]
    def shot(name,markers=(),modal=False):
        t=tree(); vals=labels(t); joined=' '.join(vals).casefold()
        if not any(n.get('package')==P for n in t.iter('node')):raise RuntimeError('RivoScan not in foreground')
        if any(x in joined for x in ("isn't responding","is not responding","close app","what's new in rivoscan")):raise RuntimeError('System/start dialog')
        if not all(m.casefold() in joined for m in markers):raise RuntimeError(name+' missing expected UI markers: '+str(vals[:80]))
        if modal and find(t,'Close') is None:raise RuntimeError(name+' no app dialog')
        f=a.out/(name+'.png');f.write_bytes(adb('exec-out','screencap','-p'))
        with Image.open(f) as im:
            if im.size!=(w,h) or im.format!='PNG':raise RuntimeError('Unexpected screenshot dimensions')
            if max(ImageStat.Stat(im.convert('RGB')).stddev)<18:raise RuntimeError('Blank screenshot')
            thumb=im.convert('RGB').resize((96,160))
            for other in previous:
                if sum(ImageStat.Stat(ImageChops.difference(thumb,other)).mean)/3<2.0:raise RuntimeError('Near-duplicate '+name)
            previous.append(thumb)
        if not 15000<f.stat().st_size<8000000:raise RuntimeError('Invalid screenshot bytes')
        (a.out/(name+'.xml')).write_bytes(ET.tostring(t,encoding='utf-8'))
        records.append({'name':f.name,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'size':[w,h],'source':'installed signed Android APK 0.45.93 code 208'})
        print('Captured '+name,flush=True)
    shot('01_Home',('My files','Scan your first document'))
    tap('Documents');shot('02_Documents',('Documents/RivoScan',))
    tap('Tools');shot('03_Tools',('Read Math Formulas','Scan Book Pages'))
    for name,label in [('04_Book_Scan','Scan Book Pages'),('05_Formula_OCR','Read Math Formulas'),('06_Photo_Translation','Translate a Photo'),('07_ID_Photo','ID Photos for Print')]:
        tap(label);shot(name,modal=True);tap('Close')
        if find(tree(),'Read Math Formulas') is None:tap('Tools')
    tap('Me');shot('08_Settings',('No account needed',))
    (a.out/'audit.json').write_text(json.dumps({'version':'0.45.93','versionCode':208,'device':a.device,'package':P,'records':records},indent=2))
if __name__=='__main__':main()
