#!/usr/bin/env python3
"""Replace RivoScan Google Play screenshot slots with unmodified genuine v0.45.40 app UI captures.
Only en-US phone, 7-inch, and 10-inch screenshots are changed. No feature graphic, icon,
app bundle, store text, track, rollout, data safety or ads are touched.
"""
import argparse,hashlib,json,sys
from pathlib import Path
from PIL import Image,ImageStat
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from publish import get_credentials

PACKAGE="com.ribhlab.rivoscan"
VERSION="0.45.40"
PRODUCTION_CODE="144"
CONFIRM="REPLACE_RIVOSCAN_04540_SCREENSHOTS_WITH_ACTUAL_APP_UI"
VIEWS=("01_Home","02_Documents","03_Tools","04_Book_Scan",
       "05_Formula_OCR","06_Photo_Translation","07_ID_Photo","08_Settings")
SLOTS={
 "phoneScreenshots":("phone/phone",(1080,1920)),
 "sevenInchScreenshots":("tablet/7-inch",(1080,1920)),
 "tenInchScreenshots":("tablet/10-inch",(1536,2560)),
}
def verify(root:Path):
    sources=(root/"phone/audit.json",root/"tablet/audit.json")
    all_hashes=[]
    for audit_path in sources:
        audit=json.loads(audit_path.read_text(encoding="utf8"))
        if VERSION not in audit.get("source","") or audit.get("errors"):
            raise ValueError("Invalid real app capture audit: "+str(audit_path))
        if any(int(r.get("horizontalOverflow",0))>4 for r in audit.get("records",[])):
            raise ValueError("Responsive UI overflow in "+str(audit_path))
    results={}
    for kind,(folder,dimensions) in SLOTS.items():
        files=[root/folder/(view+".png") for view in VIEWS]
        for f in files:
            with Image.open(f) as im:
                if im.format!="PNG" or im.size!=dimensions:
                    raise ValueError("Wrong screenshot dimensions/format: "+str(f))
                stddev=ImageStat.Stat(im.convert("RGB")).stddev
                if max(stddev)<18:raise ValueError("Screenshot appears blank: "+str(f))
            size=f.stat().st_size
            if not 15000<size<8000000:raise ValueError("Invalid screenshot size: "+str(f))
            all_hashes.append(hashlib.sha256(f.read_bytes()).hexdigest())
        results[kind]={"count":len(files),"files":files}
    if len(set(all_hashes))!=24:raise ValueError("Screenshots are duplicated")
    print("RIVOSCAN_04540_RAW_SCREENSHOTS_VERIFIED="+json.dumps({
        "sourceVersion":VERSION,"count":24,"perSlot":{k:v["count"] for k,v in results.items()},
        "policy":"Original RivoScan 0.45.40 app UI screenshots; no invented or composited interface"
    }),flush=True)
    return results

def publish(results):
    edits=build("androidpublisher","v3",credentials=get_credentials(),cache_discovery=False).edits()
    eid=edits.insert(packageName=PACKAGE,body={}).execute()["id"]
    committed=False
    try:
        tracks=edits.tracks().list(packageName=PACKAGE,editId=eid).execute().get("tracks",[])
        production=[r for t in tracks if t.get("track")=="production" for r in t.get("releases",[])]
        if len(production)!=1 or production[0].get("status")!="completed" or [str(x) for x in production[0].get("versionCodes",[])]!=[PRODUCTION_CODE]:
            raise RuntimeError("Production is not the approved RivoScan 0.45.40 code 144; abort")
        for kind,record in results.items():
            edits.images().deleteall(packageName=PACKAGE,editId=eid,language="en-US",imageType=kind).execute()
            for f in record["files"]:
                edits.images().upload(packageName=PACKAGE,editId=eid,language="en-US",imageType=kind,
                    media_body=MediaFileUpload(str(f),mimetype="image/png",resumable=False)).execute()
            after=edits.images().list(packageName=PACKAGE,editId=eid,language="en-US",imageType=kind).execute().get("images",[])
            if len(after)!=8:raise RuntimeError("Play API media count mismatch for "+kind)
            print("RIVOSCAN_04540_RAW_SLOT_REPLACED="+json.dumps({"kind":kind,"count":len(after)}),flush=True)
        edits.validate(packageName=PACKAGE,editId=eid).execute()
        edits.commit(packageName=PACKAGE,editId=eid).execute()
        committed=True
        print("RIVOSCAN_04540_REAL_SCREENSHOTS_COMMITTED="+json.dumps({
            "package":PACKAGE,"sourceVersion":VERSION,"productionCodePreserved":PRODUCTION_CODE,
            "phone":8,"tablet7":8,"tablet10":8,"screenshotsReplaced":24,
            "featureGraphicChanged":False,"iconChanged":False,"appBinaryChanged":False,
            "releaseStatusChanged":False,"listingTextChanged":False,
            "reviewMayBeRequired":True}),flush=True)
    finally:
        if not committed:
            try:edits.delete(packageName=PACKAGE,editId=eid).execute()
            except Exception:pass

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",type=Path,required=True)
    parser.add_argument("--apply",action="store_true")
    parser.add_argument("--confirm",default="")
    args=parser.parse_args()
    records=verify(args.source)
    if args.apply:
        if args.confirm!=CONFIRM:raise ValueError("Owner approval required")
        publish(records)
    else:
        print("RIVOSCAN_04540_RAW_SCREENSHOTS_DRY_RUN_SUCCESS",flush=True)
if __name__=="__main__":
    try:main()
    except Exception as e:
        print("RIVOSCAN_04540_RAW_SCREENSHOTS_FAILED="+json.dumps({
            "type":type(e).__name__,"message":str(e)[:400],
            "httpStatus":getattr(getattr(e,"resp",None),"status",None)}),file=sys.stderr)
        raise SystemExit(1)
