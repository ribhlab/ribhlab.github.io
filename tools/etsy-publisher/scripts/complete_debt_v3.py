"""Complete exactly Etsy listing 4607819043 using the private checked package.

Runs only from a GitHub Actions job with scoped Etsy secrets.
Downloads never enter this public repository or its Actions artifacts.
"""
import hashlib
import io
import json
import os
import re
import sys
import zipfile
from pathlib import Path
import requests

LISTING_ID = 4607819043
EXPECTED_SHA256 = "68216d67bcabc4e7cb627b4774d0544ec2eb4e9fa8bc12bae4c45796e5b160a8"
EXPECTED_TITLE = "Debt Payoff Spreadsheet for Excel | Snowball vs Avalanche Calculator, Debt Tracker with 9 Live Charts"
BASE = "https://api.etsy.com/v3"

class SafePublishError(Exception): pass

def require(ok, message):
    if not ok:
        raise SafePublishError(message)

def api(method, path, headers, *, data=None, files=None):
    try:
        response = requests.request(method, BASE + path, headers=headers, data=data,
                                    files=files, timeout=90, allow_redirects=False)
    except requests.RequestException:
        raise SafePublishError(f"Etsy network error: {method} {path.split('?')[0]}") from None
    if response.status_code >= 400:
        # Etsy's error body must never reach public GitHub logs.
        raise SafePublishError(f"Etsy HTTP {response.status_code} on {method} {path.split('?')[0]}") from None
    try: return response.json()
    except ValueError: raise SafePublishError("Invalid JSON from Etsy") from None

def load_product(zip_path):
    raw = Path(zip_path).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == EXPECTED_SHA256, "Private package integrity failed")
    require(len(raw) < 10 * 1024 * 1024, "Private package is unexpectedly large")
    with zipfile.ZipFile(io.BytesIO(raw)) as zipf:
        require(zipf.testzip() is None, "Corrupt product package")
        root = "products/ribhlab-debt-freedom-pro-v3/"
        m = json.loads(zipf.read(root + "listing.json"))
        require(m.get("title") == EXPECTED_TITLE, "Wrong listing title")
        require(m.get("type") == "download", "Not a digital download")
        require(len(m.get("images", [])) == 8, "Expected exactly 8 preview images")
        require(len(m.get("digital_files", [])) == 1, "Expected exactly one buyer file")
        files = []
        for rel in m["images"] + m["digital_files"]:
            require(isinstance(rel,str) and not rel.startswith("/") and ".." not in rel and "\\" not in rel,"Unsafe file path")
            full = root + rel
            data = zipf.read(full)
            require(len(data)>0 and len(data)<=20*1024*1024, "Invalid asset size")
            files.append((rel.rsplit("/",1)[-1],data))
        return m, files[:8], files[8:]

def connect():
    key = os.environ.get("ETSY_KEYSTRING", "")
    shared = os.environ.get("ETSY_SHARED_SECRET", "")
    refresh = os.environ.get("ETSY_REFRESH_TOKEN", "")
    require(key and shared and refresh, "One or more required GitHub secrets are missing")
    obj = api("POST", "/public/oauth/token", {"Content-Type":"application/x-www-form-urlencoded"},
              data={"grant_type":"refresh_token","client_id":key,"refresh_token":refresh})
    access = obj.get("access_token")
    require(isinstance(access,str) and access, "Etsy grant was not accepted")
    user = access.split(".",1)[0]
    require(re.fullmatch(r"\d{1,20}",user) is not None,"Cannot infer Etsy user ID")
    auth = {"x-api-key":key+":"+shared,"Authorization":"Bearer "+access}
    shops = api("GET",f"/application/users/{user}/shops",auth)
    rows = shops.get("results",[]) if isinstance(shops,dict) else []
    if not rows and isinstance(shops,dict) and shops.get("shop_id"):
        rows = [shops]
    require(bool(rows), "No Etsy shop found")
    shop_id = int(rows[0]["shop_id"])
    listing = api("GET",f"/application/listings/{LISTING_ID}",auth)
    require(str(listing.get("shop_id","")) == str(shop_id), "Listing belongs to a different shop")
    require(listing.get("title","").strip() == EXPECTED_TITLE, "Wrong Etsy listing")
    require(listing.get("state") in ("draft","active"), "Etsy listing in unexpected state")
    return auth,shop_id,listing

def run():
    m, preview_files, buyer_files = load_product("/tmp/debt-freedom-v3.zip")
    auth, shop, listing = connect()
    print("VERIFIED: exact product ZIP and exact Etsy listing", LISTING_ID)
    image_url = f"/application/listings/{LISTING_ID}/images"
    images = api("GET",image_url,auth).get("results",[])
    require(len(images)<=8, "Listing already has more images than expected; review required")
    ranks = {int(x["rank"]) for x in images if "rank" in x}
    for rank, (filename, data) in enumerate(preview_files, 1):
        if rank in ranks:
            print(f"IMAGE {rank}/8 ALREADY PRESENT")
            continue
        form={"rank":str(rank)}
        api("POST",f"/application/shops/{shop}/listings/{LISTING_ID}/images",auth,
            data=form,files={"image":(filename,io.BytesIO(data),"image/jpeg")})
        print(f"IMAGE {rank}/8 UPLOADED")
    images = api("GET",image_url,auth).get("results",[])
    ranks = {int(x["rank"]) for x in images if "rank" in x}
    require(all(i in ranks for i in range(1,9)),"Not all 8 Etsy image ranks are present")
    file_url = f"/application/shops/{shop}/listings/{LISTING_ID}/files"
    current = api("GET",file_url,auth).get("results",[])
    found = {x.get("filename","") for x in current}
    for filename,data in buyer_files:
        if filename in found:
            print("BUYER ZIP ALREADY PRESENT")
        else:
            api("POST",file_url,auth,data={"name":filename},
                files={"file":(filename,io.BytesIO(data),"application/zip")})
            print("BUYER ZIP UPLOADED")
    current = api("GET",file_url,auth).get("results",[])
    require(any(x.get("filename","")==buyer_files[0][0] for x in current),"Buyer file missing after upload")
    if listing["state"] == "active":
        print("ALREADY ACTIVE",LISTING_ID)
    else:
        updated = api("PATCH",f"/application/shops/{shop}/listings/{LISTING_ID}",auth,
                      data={"type":"download","state":"active"})
        require(updated.get("state") == "active","Etsy did not confirm activation")
        print("ACTIVATED",LISTING_ID)
    print("PUBLIC_LISTING_URL https://www.etsy.com/listing/"+str(LISTING_ID))

if __name__=="__main__":
    try:run()
    except (SafePublishError,KeyError,ValueError,zipfile.BadZipFile) as exc:
        print("PUBLISH_FAILED:",str(exc)[:250],file=sys.stderr);sys.exit(1)
