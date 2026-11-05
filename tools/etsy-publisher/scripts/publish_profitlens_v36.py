"""Secure, idempotent ProfitLens Offline 3.6 full Etsy publisher.

No buyer assets, decryption keys, Etsy credentials or downloaded plaintext files
are ever committed to the public GitHub repository or written to workflow logs.
"""
import hashlib
import io
import json
import os
import re
import sys
import urllib.parse
import zipfile

import requests
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from pypdf import PdfReader

from check_connection import verify, ConnectionErrorSafe

BASE = "https://api.etsy.com/v3"
STAGING_URL = "https://ribhlab.wordpress.com/wp-content/uploads/2026/11/ribhlab-profitlens-v36-encrypted-transfer.pdf"
STAGING_SHA = "74d5bbd2e8e2e0a5a8ecdd52043bb0821d2da8eb42bdb4fcb20df435229c81c7"
PLAINTEXT_SHA = "a836ee22467349a0bc6cb2173b90a9da97918dc5c438d4100b74822bb95bf94a"
KEY_URL = "https://ribhlab-profitlens-v36-secure-trans.vercel.app/api/key"
AUDIENCE = "ribhlab-profitlens-v36-transfer-v1"
ROOT = "products/profitlens-offline-v36/"
AAD = b"ribhlab-profitlens-v36-etsy-transfer"

class PublishError(Exception):
    pass

def require(condition,message):
    if not condition: raise PublishError(message)

def private_bundle():
    id_url = os.environ["ACTIONS_ID_TOKEN_REQUEST_URL"]
    id_token = os.environ["ACTIONS_ID_TOKEN_REQUEST_TOKEN"]
    sep = "&" if "?" in id_url else "?"
    try:
        auth_response = requests.get(id_url+sep+"audience="+AUDIENCE,
            headers={"Authorization":"Bearer "+id_token}, timeout=22)
        require(auth_response.ok, "GitHub OIDC token request rejected")
        jwt = auth_response.json()["value"]
        require(len(jwt)<18000,"OIDC token invalid")
        key_response = requests.get(KEY_URL,headers={"Authorization":"Bearer "+jwt},timeout=35)
        require(key_response.status_code==200, "Private transfer key endpoint denied GitHub verification")
        key = bytes.fromhex(key_response.json()["key"])
        require(len(key)==32,"Transfer key invalid")
        del jwt
        encrypted = requests.get(STAGING_URL, timeout=90)
        require(encrypted.ok,"Encrypted staging archive could not be downloaded")
        require(len(encrypted.content)<8*1024*1024,"Unexpected encrypted file size")
        require(hashlib.sha256(encrypted.content).hexdigest()==STAGING_SHA,"Encrypted PDF checksum mismatch")
        pdf=PdfReader(io.BytesIO(encrypted.content))
        attached=pdf.attachments.get("profitlens-v36-encrypted.bin")
        require(attached is not None,"Encrypted PDF attachment missing")
        sealed=attached[0] if isinstance(attached,list) else attached
        require(sealed.startswith(b"RIBHLAB1") and len(sealed)>36,"Encrypted attachment invalid")
        raw=AESGCM(key).decrypt(sealed[8:20],sealed[20:],AAD)
        require(hashlib.sha256(raw).hexdigest()==PLAINTEXT_SHA,"Product ZIP SHA-256 mismatch")
        print("PASS: one-time encrypted transfer, PDF attachment, AES-GCM and ZIP SHA-256 verified.")
        return zipfile.ZipFile(io.BytesIO(raw))
    except (requests.RequestException,ValueError,KeyError,TypeError) as e:
        raise PublishError("Secure download failed: "+type(e).__name__) from None

def api(sess, method, path, **kwargs):
    try:
        res=sess.request(method,BASE+path,timeout=65,allow_redirects=False,**kwargs)
    except requests.RequestException:
        raise PublishError("Etsy network error on "+method+" "+path.split("?")[0]) from None
    if not res.ok:
        # Do not print Etsy error bodies; they may expose personal information.
        raise PublishError("Etsy "+method+" failed HTTP "+str(res.status_code)+" on "+path.split("?")[0])
    try: return res.json()
    except ValueError: raise PublishError("Etsy returned non-JSON response") from None

def prepare(zipf):
    require(zipf.testzip() is None,"Corrupt product ZIP")
    m=json.loads(zipf.read(ROOT+"listing.json"))
    ready=json.loads(zipf.read("PUBLISH_READY.json"))
    require(ready.get("product_slug")=="profitlens-offline-v36","Wrong product slug")
    require(m.get("type")=="download","Not an Etsy digital listing")
    require(m.get("title")=="ProfitLens Offline Finance Dashboard, Profit and Expense Tracker for Small Business","Product title unexpected")
    require(m.get("taxonomy_id")==12476,"Unexpected category ID")
    require(m.get("price")=="29.95","Unexpected price")
    require(len(m.get("images",[]))==10,"Not 10 listing images")
    require(len(m.get("digital_files",[]))==1,"Not one buyer attachment")
    require(len(m.get("tags",[]))==13 and all(len(t)<=20 for t in m["tags"]),"Etsy tags invalid")
    require(m["images"][0]=="images/01_profitlens_dashboard.jpg","Hero image out of order")
    all_items=ready["images"]+ready["buyer_downloads"]
    require(len(all_items)==11,"Transfer manifest contains unexpected assets")
    for item in all_items:
        name=item["path"]
        require(name.startswith(ROOT) and ".." not in name and "\\" not in name,"Unsafe asset path")
        data=zipf.read(name)
        require(0<len(data)<=20*1024*1024,"Invalid Etsy upload size")
        require(hashlib.sha256(data).hexdigest()==item["sha256"],"Product item checksum failed")
    return m

def connect():
    shop_id=verify()
    key=os.environ["ETSY_KEYSTRING"];shared=os.environ["ETSY_SHARED_SECRET"]
    refresh=os.environ["ETSY_REFRESH_TOKEN"]
    obj=requests.post(BASE+"/public/oauth/token",
        data={"grant_type":"refresh_token","client_id":key,"refresh_token":refresh},timeout=30)
    require(obj.ok,"Etsy refresh token rejected")
    access=obj.json().get("access_token")
    require(isinstance(access,str) and access,"Etsy access token unavailable")
    sess=requests.Session()
    sess.headers.update({"x-api-key":key+":"+shared,"Authorization":"Bearer "+access})
    return sess,shop_id

def get_existing(sess,shop,title):
    found=[]
    root=f"/application/shops/{shop}/listings"
    for state in ("draft","active","inactive"):
        offset=0
        while offset<500:
            q=urllib.parse.urlencode({"state":state,"limit":100,"offset":offset})
            rows=api(sess,"GET",root+"?"+q).get("results",[])
            for row in rows:
                name=row.get("title","").strip()
                if name==title:
                    found.append(row)
                elif "profitlens" in name.lower() and "offline" in name.lower() and ("3.6" in name or "v36" in name.lower()):
                    raise PublishError("Potential existing ProfitLens Offline 3.6 listing with different title; stop to avoid duplicates")
            if len(rows)<100:break
            offset+=len(rows)
    require(len(found)<2,"Duplicate ProfitLens listings already exist; stop")
    return found[0] if found else None

def main():
    with private_bundle() as bundle:
        manifest=prepare(bundle)
        print("PASS: 10 correct screenshots and one real offline buyer ZIP checked.")
        sess,shop=connect()
        base=f"/application/shops/{shop}/listings"
        existing=get_existing(sess,shop,manifest["title"])
        if existing is None:
            fields={k:manifest[k] for k in ("quantity","title","description","price","taxonomy_id","type","who_made","when_made")}
            fields["is_supply"]="false"
            fields["should_auto_renew"]="false"
            fields["tags"]=",".join(manifest["tags"])
            draft=api(sess,"POST",base,data=fields)
            require(draft.get("listing_id"),"Etsy did not return a listing ID")
            lid=int(draft["listing_id"])
            print("CREATED_PROFITLENS_DRAFT_ID:",lid)
            state="draft"
        else:
            lid=int(existing["listing_id"])
            state=existing.get("state")
            require(state in ("active","draft"),"Existing listing has unsupported state")
            require(str(existing.get("shop_id"))==str(shop),"Existing listing shop mismatch")
            print("REUSING_PROFITLENS_LISTING_ID:",lid,"STATE:",state)
        listing_path=f"{base}/{lid}"
        imgs_path=f"/application/listings/{lid}/images"
        files_path=listing_path+"/files"
        def images():return api(sess,"GET",imgs_path).get("results",[])
        def buyerfiles():return api(sess,"GET",files_path).get("results",[])
        current=images()
        require(len(current)<=10,"Listing has unexpected extra preview images")
        ranks={int(x.get("rank",0)) for x in current}
        # Rank 1 must be the real interface, not an abstract/illustrative image.
        for rank,rel in enumerate(manifest["images"],1):
            if rank in ranks:
                print("IMAGE_RANK",rank,"ALREADY_PRESENT")
                continue
            data=bundle.read(ROOT+rel)
            api(sess,"POST",listing_path+"/images",data={"rank":str(rank)},
                files={"image":(rel.rsplit("/",1)[-1],io.BytesIO(data),"image/jpeg")})
            print("IMAGE_RANK",rank,"UPLOADED")
        current=images()
        ranks={int(x.get("rank",0)) for x in current}
        require(len(current)>=10 and all(r in ranks for r in range(1,11)),"Gallery incomplete; draft retained")
        expected=manifest["digital_files"][0].rsplit("/",1)[-1]
        current_files=buyerfiles()
        if not any(x.get("filename")==expected for x in current_files):
            require(len(current_files)<5,"Digital attachments slots exhausted")
            raw=bundle.read(ROOT+manifest["digital_files"][0])
            api(sess,"POST",files_path,
                data={"name":expected},
                files={"file":(expected,io.BytesIO(raw),"application/zip")})
            print("BUYER_ZIP_UPLOADED")
        else:
            print("BUYER_ZIP_ALREADY_PRESENT")
        current_files=buyerfiles()
        require(any(x.get("filename")==expected for x in current_files),"Etsy could not verify buyer ZIP; not activating")
        print("VERIFIED_IMAGES:",len(current))
        print("VERIFIED_BUYER_FILES:",len(current_files))
        if state=="active":
            print("ALREADY_ACTIVE",lid)
        else:
            updated=api(sess,"PATCH",listing_path,data={"type":"download","state":"active"})
            if updated.get("state")!="active":
                found=get_existing(sess,shop,manifest["title"])
                require(found and found.get("state")=="active","Etsy did not confirm Active state")
            print("CONFIRMED_ACTIVE_LISTING:",lid)
        print("PUBLIC_LISTING_URL: https://www.etsy.com/listing/"+str(lid))
        with open(os.environ.get("GITHUB_STEP_SUMMARY","/dev/null"),"a",encoding="utf-8") as f:
            f.write(f"### ProfitLens Offline 3.6 published\n\nListing **{lid}** is Active. Gallery: **{len(current)}** images; buyer downloads: **{len(current_files)}**.\n")

if __name__=="__main__":
    try: main()
    except (PublishError,ConnectionErrorSafe,zipfile.BadZipFile,KeyError,ValueError,TypeError) as exc:
        print("PUBLISH_FAILED:",str(exc)[:250],file=sys.stderr);sys.exit(1)
    except Exception as exc:
        print("PUBLISH_FAILED: unexpected "+type(exc).__name__,file=sys.stderr);sys.exit(1)
