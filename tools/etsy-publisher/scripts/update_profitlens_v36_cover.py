"""Replace only the ProfitLens 3.6 Etsy hero photo with a new, accurate design.

The hero uses an actual application screenshot from the seller's original package.
No listing creation, pricing changes, description edits, download-file edits, or
other image uploads are performed by this script.
"""
import hashlib
import io
import os
import sys
import time
import urllib.parse

import requests
from check_connection import verify, ConnectionErrorSafe

LISTING_ID = 4610490076
TITLE = "ProfitLens Offline Finance Dashboard, Profit and Expense Tracker for Small Business"
BASE = "https://api.etsy.com/v3"
COVER_URL = "https://ribhlab.wordpress.com/wp-content/uploads/2026/11/profitlens-offline-v36-updated-etsy-hero.png"
COVER_SHA256 = "f7746707251db492741a9ff962e3bea9312da1f90d3fa7cd69815d8ed9161721"
COVER_FILENAME = "profitlens-offline-v36-updated-etsy-hero.png"
ALT = "ProfitLens Offline 3.6 — HTML finance dashboard promotional cover showing browser-based offline operation, CSV import, JSON backup, and instant digital download."

class PublishError(Exception):
    pass

def must(condition, message):
    if not condition:
        raise PublishError(message)

def api(sess, method, path, **kwargs):
    try:
        response=sess.request(method,BASE+path,timeout=60,allow_redirects=False,**kwargs)
    except requests.RequestException:
        raise PublishError("Unable to contact Etsy while " + method + " " + path.split("?")[0]) from None
    if not response.ok:
        raise PublishError("Etsy "+method+" HTTP "+str(response.status_code)+" on "+path.split("?")[0])
    try:
        return response.json()
    except ValueError:
        raise PublishError("Unexpected non-JSON Etsy reply") from None

def confirm_listing(sess, shop):
    base=f"/application/shops/{shop}/listings"
    for state in ("active", "draft"):
        offset=0
        while offset<500:
            q=urllib.parse.urlencode({"state":state,"limit":100,"offset":offset})
            items=api(sess,"GET",base+"?"+q).get("results",[])
            for item in items:
                if int(item.get("listing_id",0))==LISTING_ID:
                    must(str(item.get("shop_id"))==str(shop), "Listing/shop mismatch")
                    must(item.get("title")==TITLE, "Listing title mismatch")
                    must(item.get("state")=="active", "Listing is not currently active; refusing to modify")
                    return item
            if len(items)<100:break
            offset+=len(items)
    raise PublishError("Could not find ProfitLens listing in connected seller shop")

def main():
    shop=verify()
    key=os.environ["ETSY_KEYSTRING"]
    shared=os.environ["ETSY_SHARED_SECRET"]
    refresh=os.environ["ETSY_REFRESH_TOKEN"]
    try:
        grant=requests.post(BASE+"/public/oauth/token",data={
            "grant_type":"refresh_token","client_id":key,"refresh_token":refresh
        },timeout=25)
    except requests.RequestException:
        raise PublishError("Etsy OAuth connection failed") from None
    must(grant.ok,"Etsy OAuth refresh rejected")
    access=grant.json().get("access_token")
    must(isinstance(access,str) and len(access)>20,"Missing Etsy access token")
    sess=requests.Session()
    sess.headers.update({
        "x-api-key":key+":"+shared,
        "Authorization":"Bearer "+access
    })
    confirm_listing(sess,shop)
    listing_path=f"/application/shops/{shop}/listings/{LISTING_ID}"
    img_path=f"/application/listings/{LISTING_ID}/images"
    images=api(sess,"GET",img_path).get("results",[])
    must(1<=len(images)<=11, "Unexpected image count, no changes made")
    images=sorted(images,key=lambda im:int(im.get("rank",100)))
    cover=images[0]
    if "ProfitLens Offline 3.6 — HTML finance dashboard promotional cover" in str(cover.get("alt_text","")):
        print("COVER_ALREADY_PRIMARY",cover.get("listing_image_id"))
        print("STATE: active, no edits needed.")
        return
    original_image_id=cover.get("listing_image_id")
    buyers=api(sess,"GET",listing_path+"/files").get("results",[])
    must(any("ProfitLens_v3_6" in str(x.get("filename","")) for x in buyers),
         "Original buyer file not found. Refusing to edit a potentially incomplete listing")
    try:
        image_resp=requests.get(COVER_URL,timeout=40,allow_redirects=True)
    except requests.RequestException:
        raise PublishError("Temporary source cover unavailable") from None
    must(image_resp.ok,"Temporary source cover failed to download")
    raw=image_resp.content
    must(0<len(raw)<=5*1024*1024,"Hero image size is unexpected")
    must(hashlib.sha256(raw).hexdigest()==COVER_SHA256,"Hero image SHA-256 mismatch")
    must(raw[:8]==b"\x89PNG\r\n\x1a\n","Hero is not a PNG")
    print("PASS: exact approved ProfitLens promotional cover verified, bytes:",len(raw))
    result=api(sess,"POST",listing_path+"/images",
        data={"rank":"1","overwrite":"true","alt_text":ALT},
        files={"image":(COVER_FILENAME,io.BytesIO(raw),"image/png")})
    uploaded_id=result.get("listing_image_id")
    must(uploaded_id,"Etsy did not return the new image identifier")
    print("IMAGE_UPLOAD_SUCCESS_ID:",uploaded_id)
    for attempt in range(10):
        revised=api(sess,"GET",img_path).get("results",[])
        rank={str(x.get("listing_image_id")):int(x.get("rank",0)) for x in revised}
        if rank.get(str(uploaded_id))==1:
            confirm_listing(sess,shop)
            final_files=api(sess,"GET",listing_path+"/files").get("results",[])
            must(len(final_files)>=len(buyers),"Existing buyer files unexpectedly missing")
            must(1<=len(revised)<=11,"Final listing image count unexpected")
            print("VERIFIED_NEW_COVER_RANK_1:",uploaded_id)
            print("PREVIOUS_COVER_IMAGE_ID:",original_image_id)
            print("FINAL_IMAGE_COUNT:",len(revised))
            print("BUYER_FILE_COUNT:",len(final_files))
            print("LISTING_ACTIVE:",LISTING_ID)
            print("LISTING_URL: https://www.etsy.com/listing/"+str(LISTING_ID))
            with open(os.environ.get("GITHUB_STEP_SUMMARY","/dev/null"),"a",encoding="utf-8") as f:
                f.write("### ProfitLens 3.6 — Main Etsy photo replaced\n\n")
                f.write(f"Listing **{LISTING_ID}** remains **Active**. New custom cover rank **1**; photo count **{len(revised)}**; buyer ZIP retained.\n")
            return
        time.sleep(3)
    raise PublishError("Image submitted but Etsy did not yet confirm rank 1; avoid retrying blindly.")

if __name__=="__main__":
    try: main()
    except (PublishError,ConnectionErrorSafe,KeyError,ValueError) as exc:
        print("COVER_UPDATE_FAILED:",str(exc)[:220],file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print("COVER_UPDATE_FAILED: unexpected "+type(exc).__name__,file=sys.stderr)
        sys.exit(1)
