#!/usr/bin/env python3
"""One Google Play edit: exact signed RivoScan 208 + 24 genuine native screenshots.
Abort without committing on any unexpected track, hash or screenshot."""
import argparse,json
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from publish import get_credentials
from rivoscan_04593_prod_only_preserve_images import check_file,RELEASE,EXPECTED_SHA256
from rivoscan_04593_native_screenshots import verify
P='com.ribhlab.rivoscan';CODE='208'
def main():
    p=argparse.ArgumentParser();p.add_argument('--aab',type=Path,required=True);p.add_argument('--screens',type=Path,required=True);p.add_argument('--confirm',required=True);a=p.parse_args()
    if a.confirm!='PUBLISH_RIVOSCAN_04593_WITH_NATIVE_SCREENSHOTS':raise ValueError('Explicit owner approval required')
    check_file(a.aab);groups=verify(a.screens)
    edits=build('androidpublisher','v3',credentials=get_credentials(),cache_discovery=False).edits()
    eid=edits.insert(packageName=P,body={}).execute()['id']; params=dict(packageName=P,editId=eid);committed=False
    try:
        tracks=edits.tracks().list(**params).execute().get('tracks',[])
        prod=next((t.get('releases',[]) for t in tracks if t['track']=='production'),[])
        print('RIVOSCAN_04593_PRODUCTION_BEFORE='+json.dumps(prod),flush=True)
        if len(prod)!=1 or prod[0].get('status')!='completed' or len(prod[0].get('versionCodes',[]))!=1:raise RuntimeError('Unexpected production state; no overwrite')
        if any(int(c)>int(CODE) for t in tracks for r in t.get('releases',[]) for c in r.get('versionCodes',[])):raise RuntimeError('Newer version on Play; no downgrade')
        existing=next((b for b in edits.bundles().list(**params).execute().get('bundles',[]) if str(b['versionCode'])==CODE),None)
        if existing:
            if existing.get('sha256','').lower()!=EXPECTED_SHA256:raise RuntimeError('Existing versionCode hash mismatch')
        else:
            b=edits.bundles().upload(**params,media_body=MediaFileUpload(str(a.aab),mimetype='application/octet-stream',resumable=True)).execute(num_retries=3)
            if str(b.get('versionCode'))!=CODE:raise RuntimeError('Wrong uploaded versionCode')
        if list(map(str,prod[0]['versionCodes']))!=[CODE]:
            edits.tracks().update(**params,track='production',body={'track':'production','releases':[RELEASE]}).execute()
        locs=edits.listings().list(**params).execute().get('listings',[])
        if not any(x.get('language')=='en-US' for x in locs):raise RuntimeError('Missing en-US listing')
        def image_ids(typ):
            return [x['id'] for x in edits.images().list(**params,language='en-US',imageType=typ).execute().get('images',[])]
        preserved={typ:image_ids(typ) for typ in ('icon','featureGraphic')}
        for typ,files in groups.items():
            edits.images().deleteall(**params,language='en-US',imageType=typ).execute()
            for f in files:
                x=edits.images().upload(**params,language='en-US',imageType=typ,media_body=MediaFileUpload(str(f),mimetype='image/png',resumable=False)).execute()
                if not x.get('image',{}).get('id'):raise RuntimeError('Screenshot not confirmed')
            if len(image_ids(typ))!=len(files):raise RuntimeError('Wrong screenshot count')
        if any(image_ids(typ)!=ids for typ,ids in preserved.items()):raise RuntimeError('Icon or feature graphic changed')
        edits.validate(**params).execute();r=edits.commit(**params).execute();committed=True
        print('RIVOSCAN_04593_PRODUCTION_AND_SCREENSHOTS_COMMITTED='+json.dumps({'package':P,'versionCode':208,'versionName':'0.45.93','track':'production','counts':{k:len(v) for k,v in groups.items()},'editId':r.get('id'),'reviewMayBeRequired':True}),flush=True)
    finally:
        if not committed:
            try:edits.delete(**params).execute()
            except Exception:pass
if __name__=='__main__':main()
