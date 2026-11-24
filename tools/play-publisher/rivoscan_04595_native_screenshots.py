#!/usr/bin/env python3
"""Replace only RivoScan screenshots after exact installed APK capture and approved production update."""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image
from google_auth_httplib2 import AuthorizedHttp
import httplib2
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from publish import get_credentials
P='com.ribhlab.rivoscan'
VIEWS=['01_Home','02_Documents','03_Tools','04_Book_Scan','05_Formula_OCR','06_Photo_Translation','07_ID_Photo','08_Settings']
SLOTS={'phoneScreenshots':('phone',(720,1440)),'sevenInchScreenshots':('tablet7',(720,1280)),'tenInchScreenshots':('tablet10',(1200,1920))}
def verify(root):
    groups={}
    for typ,(folder,size) in SLOTS.items():
        d=root/folder
        audit=json.loads((d/'audit.json').read_text())
        if (audit['package'],audit['versionCode'],audit['device'])!=(P,210,folder) or audit['version']!='0.45.95':raise ValueError('Unexpected capture audit')
        records=audit['records']; expected=[v+'.png' for v in VIEWS]
        names=[r['name'] for r in records]
        required={'01_Home.png','02_Documents.png','03_Tools.png'}
        if len(names)<4 or not required.issubset(names) or len(names)!=len(set(names)) or any(n not in expected for n in names):raise ValueError('Missing essential or unexpected views')
        files=[];hashes=set()
        for r in records:
            f=d/r['name'];digest=hashlib.sha256(f.read_bytes()).hexdigest()
            if digest!=r['sha256'] or digest in hashes or tuple(r['size'])!=size:raise ValueError('Invalid or repeated capture')
            if not (d/(f.stem+'.xml')).is_file():raise ValueError('Missing native accessibility evidence')
            with Image.open(f) as im:
                if im.size!=size or im.format!='PNG':raise ValueError('Bad format/size')
            hashes.add(digest);files.append(f)
        groups[typ]=files
    return groups
def main():
    p=argparse.ArgumentParser();p.add_argument('--source',required=True,type=Path);p.add_argument('--confirm',required=True);a=p.parse_args()
    if a.confirm!='REPLACE_RIVOSCAN_04595_NATIVE_SCREENSHOTS':raise ValueError('Owner approval required')
    groups=verify(a.source)
    edits=build('androidpublisher','v3',http=AuthorizedHttp(get_credentials(),http=httplib2.Http(timeout=180)),cache_discovery=False).edits()
    eid=edits.insert(packageName=P,body={}).execute()['id']; committed=False
    params=dict(packageName=P,editId=eid)
    try:
        tracks=edits.tracks().list(**params).execute().get('tracks',[])
        prod=next((t.get('releases',[]) for t in tracks if t['track']=='production'),[])
        if len(prod)!=1 or prod[0].get('status')!='completed' or list(map(str,prod[0].get('versionCodes',[])))!=['210']:raise RuntimeError('Production is not verified 210; refuse changes')
        locs=edits.listings().list(**params).execute().get('listings',[])
        if not any(x.get('language')=='en-US' for x in locs):raise RuntimeError('Missing en-US listing')
        # Default en-US images are the source for localized listings without custom screenshots.
        def ids(lang,typ):return [x['id'] for x in edits.images().list(**params,language=lang,imageType=typ).execute().get('images',[])]
        locales=[x['language'] for x in locs]
        before={lang:{typ:len(ids(lang,typ)) for typ in groups} for lang in locales}
        print('SCREENSHOT_COUNTS_BEFORE='+json.dumps(before),flush=True)
        preserved={lang:{typ:ids(lang,typ) for typ in ('icon','featureGraphic')} for lang in locales}
        for typ,files in groups.items():
            edits.images().deleteall(**params,language='en-US',imageType=typ).execute()
            for f in files:
                result=edits.images().upload(**params,language='en-US',imageType=typ,media_body=MediaFileUpload(str(f),mimetype='image/png',resumable=False)).execute()
                if not result.get('image',{}).get('id'):raise RuntimeError('Missing upload confirmation')
            if len(edits.images().list(**params,language='en-US',imageType=typ).execute().get('images',[]))!=len(files):raise RuntimeError('Wrong screenshot count')
        if any(ids(lang,typ)!=value for lang,types in preserved.items() for typ,value in types.items()):raise RuntimeError('Unexpected icon or feature graphic modification')
        edits.validate(**params).execute();result=edits.commit(**params).execute();committed=True
        print('RIVOSCAN_04595_SCREENSHOTS_COMMITTED='+json.dumps({'versionCode':210,'locale':'en-US','counts':{k:len(v) for k,v in groups.items()},'editId':result.get('id'),'reviewMayBeRequired':True}),flush=True)
    finally:
        if not committed:
            try:edits.delete(**params).execute()
            except Exception:pass
if __name__=='__main__':main()
