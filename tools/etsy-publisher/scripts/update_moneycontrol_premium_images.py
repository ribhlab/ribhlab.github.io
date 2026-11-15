"""Update MoneyControl Pro's existing ACTIVE Etsy listing with four premium images.

Does not alter buyer files, price, title, listing status, or public GitHub assets.
Loads temporary WordPress media URLs and verifies PNGs before Etsy writes.
Uploads in reverse order at rank 1, so the new hero is the first listing photo.
"""
import io
import struct
import sys
import requests
from publish_moneycontrol_pro_draft import get_connection,get_listing,call,check,PublishError,TITLE

LISTING_ID=4617919674
MEDIA=[
    ("HERO","https://ribhlab.wordpress.com/wp-content/uploads/2026/11/moneycontrol-etsy-new-cover.png","MoneyControl_Pro_Hero.png"),
    ("ANALYTICS","https://ribhlab.wordpress.com/wp-content/uploads/2026/11/moneycontrol-etsy-new-analytics.png","MoneyControl_Analytics.png"),
    ("DESKTOP_MOBILE","https://ribhlab.wordpress.com/wp-content/uploads/2026/11/moneycontrol-etsy-new-desktop-mobile.png","MoneyControl_Desktop_Mobile.png"),
    ("HOW_IT_WORKS","https://ribhlab.wordpress.com/wp-content/uploads/2026/11/moneycontrol-etsy-new-how-it-works.png","MoneyControl_How_It_Works.png")
]
def download(entry):
    tag,url,name=entry
    try:r=requests.get(url,timeout=40)
    except requests.RequestException:raise PublishError(tag+": media temporarily unavailable.") from None
    check(r.status_code==200 and 500000<len(r.content)<8*1024*1024,tag+": missing/incorrect media.")
    check(r.content[:16]==bytes.fromhex("89504e470d0a1a0a0000000d49484452"),tag+": invalid PNG.")
    w,h=struct.unpack(">II",r.content[16:24])
    check((w,h)==(1448,1086),tag+": wrong image dimensions.")
    print("VERIFIED_PREMIUM_IMAGE:",tag,w,h,len(r.content))
    return tag,name,r.content
def run():
    data=[download(row) for row in MEDIA]
    headers,shop=get_connection()
    listing=get_listing(headers,shop)
    check(listing and int(listing.get("listing_id",0))==LISTING_ID and listing.get("state")=="active",
          "Exact ACTIVE MoneyControl Pro Etsy listing not found.")
    route=f"/application/listings/{LISTING_ID}/images"
    images=call("GET",route,headers).get("results",[])
    print("INITIAL_IMAGE_COUNT:",len(images))
    if len(images)>=8:
        print("ALREADY_EIGHT_IMAGES: no further uploads made")
        print("LISTING_URL: https://www.etsy.com/listing/"+str(LISTING_ID))
        return
    check(len(images)==4,"Expected four original listing images. Refuse unsafe partial retry; inspect before uploading.")
    uploaded=[]
    for tag,name,png in reversed(data):
        response=call("POST",f"/application/shops/{shop}/listings/{LISTING_ID}/images",headers,
                      data={"rank":"1"},
                      files={"image":(name,io.BytesIO(png),"image/png")})
        iid=response.get("listing_image_id")
        uploaded.append((tag,iid))
        print("UPLOADED_PREMIUM_IMAGE:",tag,iid)
    now=call("GET",route,headers).get("results",[])
    ranks=sorted(now,key=lambda x:int(x.get("rank") or 999))
    print("FINAL_IMAGE_COUNT:",len(ranks))
    check(len(ranks)==8,"Etsy returned the wrong final image count.")
    known={x[0]:x[1] for x in uploaded}
    actual=[int(x.get("listing_image_id") or 0) for x in ranks[:4]]
    expected=[int(known[x]) for x in ("HERO","ANALYTICS","DESKTOP_MOBILE","HOW_IT_WORKS")]
    check(actual==expected,"Uploaded images exist but order was not verified; manual rank review required.")
    check(get_listing(headers,shop).get("state")=="active","Etsy listing did not remain ACTIVE.")
    print("PREMIUM_HERO_CONFIRMED:",actual[0])
    print("NEW_PREMIUM_IMAGES_CONFIRMED: 4")
    print("LISTING_REMAINS_ACTIVE:",LISTING_ID)
    print("PUBLIC_URL: https://www.etsy.com/listing/"+str(LISTING_ID))
if __name__=="__main__":
    try:run()
    except PublishError as e:
        print("PREMIUM_IMAGE_UPDATE_FAILED:",str(e)[:350],file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print("PREMIUM_IMAGE_UPDATE_FAILED:",type(e).__name__,file=sys.stderr)
        sys.exit(1)
