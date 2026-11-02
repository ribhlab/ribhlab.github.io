"""Finalize existing CashFlow Etsy listing. Original paid files are never committed to GitHub.

Downloads seller ZIP from private Vercel API only after signed GitHub Actions OIDC
verification. Etsy credentials remain GitHub secrets and go only to Etsy.
"""
import hashlib
import io
import json
import os
import sys
import urllib.parse
import urllib.request
import zipfile

import requests

from check_connection import verify, ConnectionErrorSafe

TARGET = 4608157428
TITLE = "13 Week Cash Flow Excel Template | CFO Cockpit, Cash Risk Alerts, AR AP, Scenario & Decision Dashboard"
BASE = "https://api.etsy.com/v3"
BUNDLE = "https://ribhlab-cashflow-etsy-finalizer.vercel.app/api/package"
SHA256 = "d6f24701844d493cbfffcdc33f71675cec1725be5000f8a782af6a4f764d91df"
IMAGES = [
    "UPLOAD_TO_ETSY/IMAGES/01-01-EXCEL-CFO-COCKPIT.jpg",
    "UPLOAD_TO_ETSY/IMAGES/02-02-EXCEL-DECISION-LAB.jpg",
    "UPLOAD_TO_ETSY/IMAGES/03-03-EXCEL-RISK-RADAR.jpg",
    "UPLOAD_TO_ETSY/IMAGES/04-04-EXCEL-FORECAST.jpg",
    "UPLOAD_TO_ETSY/IMAGES/05-05-EXCEL-RECEIVABLES.jpg",
    "UPLOAD_TO_ETSY/IMAGES/06-06-EXCEL-WHATS-INSIDE.jpg",
]
BUYER = "UPLOAD_TO_ETSY/BUYER_DIGITAL_DOWNLOAD/RibhLab_CashFlow_CommandCenter_PRO_v2_2_BUYER.zip"

def download_secure_archive():
    request_url = os.environ["ACTIONS_ID_TOKEN_REQUEST_URL"]
    request_token = os.environ["ACTIONS_ID_TOKEN_REQUEST_TOKEN"]
    join = "&" if "?" in request_url else "?"
    request = urllib.request.Request(
        request_url + join + "audience=ribhlab-etsy-cashflow-finalizer",
        headers={"Authorization": "Bearer " + request_token},
    )
    with urllib.request.urlopen(request, timeout=20) as result:
        jwt = json.load(result)["value"]
    response = requests.get(BUNDLE, headers={"Authorization":"Bearer " + jwt}, timeout=80)
    if response.status_code != 200:
        raise ConnectionErrorSafe(f"Private package transfer failed (HTTP {response.status_code}).")
    if hashlib.sha256(response.content).hexdigest() != SHA256:
        raise ConnectionErrorSafe("Archive SHA-256 mismatch: refusing to upload.")
    print("PASS: Authenticated private file transfer and SHA-256 verification.")
    return zipfile.ZipFile(io.BytesIO(response.content))

def api(session, url, method="GET", **kwargs):
    try:
        response = session.request(method, BASE + url, timeout=55, **kwargs)
    except requests.RequestException:
        raise ConnectionErrorSafe("Network error while using Etsy API.") from None
    if not response.ok:
        raise ConnectionErrorSafe(f"Etsy {method} failed (HTTP {response.status_code}).") from None
    try:
        return response.json()
    except ValueError:
        raise ConnectionErrorSafe("Unexpected Etsy API response.") from None

def main():
    shop=verify()
    keys={k:os.environ[k] for k in ("ETSY_KEYSTRING","ETSY_SHARED_SECRET","ETSY_REFRESH_TOKEN")}
    with download_secure_archive() as bundle:
        if bundle.testzip() is not None:
            raise ConnectionErrorSafe("Corrupt ZIP archive.")
        if not all(name in bundle.namelist() for name in [*IMAGES,BUYER]):
            raise ConnectionErrorSafe("Missing image or buyer file in product package.")
        metadata=json.loads(bundle.read("SELLER/listing.json"))
        if metadata.get("title")!=TITLE:
            raise ConnectionErrorSafe("Bundle title does not match existing listing.")
        for name in [*IMAGES,BUYER]:
            if bundle.getinfo(name).file_size>20*1024*1024:
                raise ConnectionErrorSafe("A file exceeds Etsy 20MB limit.")
        token_req=requests.post(BASE+"/public/oauth/token",
            data={"grant_type":"refresh_token","client_id":keys["ETSY_KEYSTRING"],"refresh_token":keys["ETSY_REFRESH_TOKEN"]},
            timeout=30)
        if not token_req.ok:
            raise ConnectionErrorSafe("Etsy OAuth refresh rejected.")
        access=token_req.json().get("access_token")
        if not access:
            raise ConnectionErrorSafe("Etsy did not grant access.")
        sess=requests.Session()
        sess.headers.update({"x-api-key":keys["ETSY_KEYSTRING"]+":"+keys["ETSY_SHARED_SECRET"],"Authorization":"Bearer "+access})
        path=f"/application/shops/{shop}/listings/{TARGET}"
        # Owner draft listings are discoverable through the shop collection.
        # Avoid single-listing GET paths that can return 404 for drafts.
        listing=None
        for state in ("draft","active"):
            offset=0
            while offset<500:
                query=f"/application/shops/{shop}/listings?state={state}&limit=100&offset={offset}"
                rows=api(sess,query).get("results",[])
                for row in rows:
                    if int(row.get("listing_id",0))==TARGET:
                        listing=row
                        break
                if listing or len(rows)<100:
                    break
                offset+=len(rows)
            if listing:
                break
        if not listing:
            raise ConnectionErrorSafe("CashFlow listing was not returned by Etsy's shop listing collection.")
        if int(listing.get("listing_id",-1))!=TARGET or int(listing.get("shop_id",-1))!=int(shop) or listing.get("title")!=TITLE:
            raise ConnectionErrorSafe("Listing identity/title/shop verification failed.")
        if listing.get("state")=="active":
            print("ALREADY_ACTIVE:",TARGET)
            return
        if listing.get("state")!="draft":
            raise ConnectionErrorSafe("Listing is not in Draft state: refusing write.")
        imagePath=f"/application/listings/{TARGET}/images"
        def current_images():
            return api(sess,imagePath).get("results",[])
        def current_files():
            return api(sess,path+"/files").get("results",[])
        original_images=current_images()
        if len(original_images)>6:
            raise ConnectionErrorSafe("Unexpected extra images in draft: aborting.")
        for index, name in enumerate(IMAGES,1):
            images=current_images()
            if any(int(item.get("rank",0))==index for item in images):
                print(f"IMAGE_RANK_{index}: already present")
                continue
            data=bundle.read(name)
            # Multipart Etsy upload: never log buyer content.
            api(sess,path+"/images","POST",
                data={"rank":str(index)},
                files={"image":(name.split("/")[-1],io.BytesIO(data),"image/jpeg")})
            print(f"IMAGE_RANK_{index}: uploaded")
        buyerName=BUYER.split("/")[-1]
        files=current_files()
        if not any(item.get("filename")==buyerName for item in files):
            if len(files)>=5:
                raise ConnectionErrorSafe("Etsy digital attachment slots full.")
            api(sess,path+"/files","POST",data={"name":buyerName},
                files={"file":(buyerName,io.BytesIO(bundle.read(BUYER)),"application/zip")})
            print("BUYER_FILE: uploaded")
        else:
            print("BUYER_FILE: already present")
        images=current_images()
        files=current_files()
        if len(images)<6 or not any(item.get("filename")==buyerName for item in files):
            raise ConnectionErrorSafe("Image/file verification incomplete: listing remains Draft.")
        print("VERIFIED_IMAGES:",len(images))
        print("VERIFIED_BUYER_FILES:",len(files))
        activated=api(sess,path,"PATCH",data={"state":"active"})
        if activated.get("state")!="active":
            active_rows=api(sess,f"/application/shops/{shop}/listings?state=active&limit=100&offset=0").get("results",[])
            activated=next((x for x in active_rows if int(x.get("listing_id",0))==TARGET),activated)
        if activated.get("state")!="active":
            raise ConnectionErrorSafe("Etsy did not confirm Active state.")
        print("CONFIRMED_ACTIVE_LISTING:",TARGET)
        print("ETSY_URL: https://www.etsy.com/listing/"+str(TARGET))
        with open(os.environ.get("GITHUB_STEP_SUMMARY","/dev/null"),"a",encoding="utf-8") as f:
            f.write(f"## CashFlow Command Center — Published\n\nListing {TARGET} is **ACTIVE**.\n\nImages: {len(images)}; Buyer files: {len(files)}.\n")

if __name__=="__main__":
    try: main()
    except ConnectionErrorSafe as exc:
        print("FAIL:",exc,file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print("FAIL: Unexpected error of type",type(exc).__name__,file=sys.stderr)
        sys.exit(1)
