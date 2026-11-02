"""Reorder the existing six CashFlow v2.2 images; put CFO Cockpit at rank 1.

One safe POST only after perceptual fingerprint matching. Never upload/delete an image,
change metadata, modify files, or create a listing. Fails closed if ambiguous.
"""
import io
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from PIL import Image, ImageOps
from check_connection import verify, ConnectionErrorSafe

BASE="https://api.etsy.com/v3"
LISTING="4608157428"
FINGERPRINTS={
 "01-CFO-COCKPIT": 0x303274656501514b,
 "02-DECISION-LAB": 0x5d7d574541696957,
 "03-RISK-RADAR": 0x301a7d5d75696d4b,
 "04-FORECAST": 0x381851614949595b,
 "05-RECEIVABLES": 0x301059414561694b,
 "06-WHATS-INSIDE": 0x281a74656501115b
}
def fetch_json(url, headers, data=None):
    req=urllib.request.Request(url,headers=headers,data=data,method="POST" if data is not None else "GET")
    try:
        with urllib.request.urlopen(req,timeout=35) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        raise ConnectionErrorSafe(f"Etsy API rejected {req.method} (HTTP {exc.code}).") from None
    except urllib.error.URLError:
        raise ConnectionErrorSafe("Cannot reach Etsy API.") from None

def fingerprint(raw):
    with Image.open(io.BytesIO(raw)) as im:
        im=ImageOps.fit(ImageOps.exif_transpose(im).convert("L"), (9,8), method=Image.Resampling.LANCZOS)
        vals=list(im.getdata())
    bits=["1" if vals[y*9+x]>vals[y*9+x+1] else "0" for y in range(8) for x in range(8)]
    return int("".join(bits),2)

def identify(item):
    link=item.get("url_570xN") or item.get("url_fullxfull")
    if not isinstance(link,str) or not link.startswith("https://"):
        raise ConnectionErrorSafe("Image URL missing.")
    try:
        req=urllib.request.Request(link,headers={"User-Agent":"RibhLabEtsyPublisher/1.0"})
        with urllib.request.urlopen(req,timeout=35) as response:
            raw=response.read(5*1024*1024+1)
    except (urllib.error.HTTPError,urllib.error.URLError):
        raise ConnectionErrorSafe("Could not fetch Etsy image preview.") from None
    if len(raw)>5*1024*1024: raise ConnectionErrorSafe("Image preview exceeds safe size.")
    actual=fingerprint(raw)
    ranked=sorted(((actual^expected).bit_count(),name) for name,expected in FINGERPRINTS.items())
    return ranked[0],ranked[1]

def main():
    shop=verify()
    key=os.environ["ETSY_KEYSTRING"]
    shared=os.environ["ETSY_SHARED_SECRET"]
    refresh=os.environ["ETSY_REFRESH_TOKEN"]
    token=fetch_json(BASE+"/public/oauth/token",
        {"Content-Type":"application/x-www-form-urlencoded"},
        urllib.parse.urlencode({"grant_type":"refresh_token","client_id":key,"refresh_token":refresh}).encode("utf-8"))
    access=token.get("access_token")
    if not access: raise ConnectionErrorSafe("Cannot refresh Etsy OAuth token.")
    headers={"x-api-key":key+":"+shared,"Authorization":"Bearer "+access}
    list_url=BASE+f"/application/listings/{LISTING}/images"
    listing=fetch_json(list_url,headers)
    images=listing.get("results",[])
    if len(images)!=6: raise ConnectionErrorSafe(f"Expected six CashFlow images, found {len(images)}. No change made.")
    matched={}
    for item in images:
        best,nextbest=identify(item)
        print("IMAGE",item.get("listing_image_id"),"CURRENT_RANK",item.get("rank"),"CANDIDATE",best[1],"DISTANCE",best[0])
        if best[0]>8 or nextbest[0]-best[0]<3 or best[1] in matched:
            raise ConnectionErrorSafe("One or more listing images could not be identified confidently; no change made.")
        matched[best[1]]=item
    if len(matched)!=6: raise ConnectionErrorSafe("Missing one or more images. No change made.")
    cover=matched["01-CFO-COCKPIT"]
    if cover["rank"]==1:
        print("SUCCESS: The CFO Cockpit image is already the Etsy cover (rank 1); nothing changed.")
        return
    image_id=cover["listing_image_id"]
    path=BASE+f"/application/shops/{shop}/listings/{LISTING}/images"
    boundary="----ribhlabEtsyRankChange"
    fields={"listing_image_id":str(image_id),"rank":"1","overwrite":"false"}
    body=b"".join(("--"+boundary+"\r\nContent-Disposition: form-data; name=\""+name+"\"\r\n\r\n"+value+"\r\n").encode("utf-8") for name,value in fields.items())+("--"+boundary+"--\r\n").encode("utf-8")
    result=fetch_json(path,{**headers,"Content-Type":"multipart/form-data; boundary="+boundary},body)
    print("RANK_CHANGE_RESPONSE_IMAGE",result.get("listing_image_id"),"REPORTED_RANK",result.get("rank"))
    confirmed=fetch_json(list_url,headers)
    ranks={str(i.get("listing_image_id")):i.get("rank") for i in confirmed.get("results",[])}
    if ranks.get(str(image_id))!=1:
        raise ConnectionErrorSafe("Etsy did not confirm rank 1 for the CFO Cockpit image.")
    print("SUCCESS: CFO Cockpit is now rank 1 / main listing cover.")
    print("LISTING_URL: https://www.etsy.com/listing/"+LISTING)

if __name__=="__main__":
    try: main()
    except ConnectionErrorSafe as e: print("ERROR:",e,file=sys.stderr);sys.exit(1)
    except Exception as e: print("ERROR: Unexpected failure: "+type(e).__name__,file=sys.stderr);sys.exit(1)
