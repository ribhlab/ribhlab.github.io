#!/usr/bin/env python3
"""Replace only Google Play en-US screenshots and feature image with genuine RivoScan 0.45.38 UI posters.
No app binary, release tracks, descriptions, icon, consent, or data-safety changes.
"""
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path
PACKAGE="com.ribhlab.rivoscan"
VERSION="0.45.38"
SOURCE_COMMIT="d27becbf4dcbcf36344308119d5f1fff529debbf"
CONFIRM="PUBLISH_VERIFIED_RIVOSCAN_04538_SCREENSHOTS"
VIEWS=("01_Home","02_Documents","03_Tools","04_Book_Scan","05_Formula_OCR","06_Photo_Translation","07_ID_Photo","08_Settings")
SLOTS={
 "featureGraphic":("feature-1024x500.png",),
 "phoneScreenshots":tuple("phone/"+x+".png" for x in VIEWS),
 "sevenInchScreenshots":tuple("sevenInch/"+x+".png" for x in VIEWS),
 "tenInchScreenshots":tuple("tenInch/"+x+".png" for x in VIEWS),
}
DIMS={"featureGraphic":(1024,500),"phoneScreenshots":(1080,1920),
      "sevenInchScreenshots":(1080,1920),"tenInchScreenshots":(1536,2560)}

def verify(root:Path,source:Path):
    from PIL import Image
    m=json.loads((root/"manifest.json").read_text(encoding="utf8"))
    if m.get("version")!=VERSION or m.get("sourceCommit")!=SOURCE_COMMIT:
        raise ValueError("Wrong RivoScan version or source revision")
    audits=(source/"phone/audit.json",source/"tablet/audit.json")
    for a in audits:
        d=json.loads(a.read_text(encoding="utf8"))
        if VERSION not in d.get("source","") or d.get("errors"):
            raise ValueError("Real app UI capture failed audit: "+str(a))
    hashes=[]
    for kind,files in SLOTS.items():
        for name in files:
            f=root/name
            if not f.is_file() or not 15000<f.stat().st_size<8000000:
                raise ValueError("Missing/oversized image: "+str(f))
            with Image.open(f) as im:
                if im.format!="PNG" or im.size!=DIMS[kind]:
                    raise ValueError("Unexpected image format or size: "+str(f))
            sha=hashlib.sha256(f.read_bytes()).hexdigest()
            matches=[row for row in m.get("files",[]) if row.get("name")==name and row.get("sha256")==sha]
            if len(matches)!=1:raise ValueError("Image checksum mismatch: "+str(f))
            hashes.append(sha)
    if len(hashes)!=25 or len(set(hashes))!=25:
        raise ValueError("Expected 25 unique genuine-source Play media assets")
    print("RIVOSCAN_04538_MEDIA_VERIFIED="+json.dumps({"version":VERSION,"sourceCommit":SOURCE_COMMIT,"images":25,"screenshots":24}),flush=True)

def publish(root:Path):
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from publish import get_credentials
    edits=build("androidpublisher","v3",credentials=get_credentials(),cache_discovery=False).edits()
    eid=edits.insert(packageName=PACKAGE,body={}).execute()["id"]
    committed=False
    try:
        tracks=edits.tracks().list(packageName=PACKAGE,editId=eid).execute().get("tracks",[])
        production=[r for t in tracks if t.get("track")=="production" for r in t.get("releases",[])]
        if len(production)!=1 or production[0].get("status")!="completed":
            raise RuntimeError("Unexpected Google Play production state")
        code=[str(x) for x in production[0].get("versionCodes",[])]
        if code not in (["139"],["142"]):
            raise RuntimeError("Production version changed; require new screenshot compatibility review: "+str(code))
        # 0.45.35 and 0.45.38 both include the eight captured view categories.
        print("RIVOSCAN_04538_PRODUCTION_PRECHECK="+json.dumps({"productionVersionCode":code[0],"screenshotsSourceVersion":VERSION}),flush=True)
        for kind,files in SLOTS.items():
            edits.images().deleteall(packageName=PACKAGE,editId=eid,language="en-US",imageType=kind).execute()
            for name in files:
                f=root/name
                edits.images().upload(packageName=PACKAGE,editId=eid,language="en-US",imageType=kind,
                    media_body=MediaFileUpload(str(f),mimetype="image/png",resumable=False)).execute()
            count=len(edits.images().list(packageName=PACKAGE,editId=eid,language="en-US",imageType=kind).execute().get("images",[]))
            if count!=len(files):raise RuntimeError("Play screenshot count mismatch: "+kind)
            print("RIVOSCAN_04538_SLOT_UPLOADED="+json.dumps({"kind":kind,"count":count}),flush=True)
        edits.validate(packageName=PACKAGE,editId=eid).execute()
        edits.commit(packageName=PACKAGE,editId=eid).execute()
        committed=True
        print("RIVOSCAN_04538_SCREENSHOTS_COMMITTED="+json.dumps({
            "package":PACKAGE,"sourceVersion":VERSION,"productionCodePreserved":code[0],
            "phone":8,"tablet7":8,"tablet10":8,"featureGraphic":1,
            "appBinaryUnchanged":True,"iconUnchanged":True,"releaseStatusUnchanged":True,
            "listingTextUnchanged":True,"reviewMayBeRequired":True}),flush=True)
    finally:
        if not committed:
            try:edits.delete(packageName=PACKAGE,editId=eid).execute()
            except Exception:pass

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--media-dir",type=Path,default=Path("/tmp/rivoscan-04538-promo"))
    p.add_argument("--source-dir",type=Path,default=Path("/tmp/rivoscan-04538"))
    p.add_argument("--apply",action="store_true")
    p.add_argument("--confirm",default="")
    args=p.parse_args()
    verify(args.media_dir,args.source_dir)
    if not args.apply:
        print("RIVOSCAN_04538_MEDIA_DRY_RUN_OK=True",flush=True)
        return
    if args.confirm!=CONFIRM:raise ValueError("Explicit owner approval required")
    publish(args.media_dir)
if __name__=="__main__":
    try:main()
    except Exception as e:
        print("RIVOSCAN_04538_MEDIA_FAILED="+json.dumps({"type":type(e).__name__,"message":str(e)[:300],
          "httpStatus":getattr(getattr(e,"resp",None),"status",None)}),file=sys.stderr)
        raise SystemExit(1)
