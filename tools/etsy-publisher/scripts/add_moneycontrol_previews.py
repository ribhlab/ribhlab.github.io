"""Attach three extra MoneyControl Etsy marketing images, with safe draft-only checks.
Assets remain temporary on WordPress and are not in the public GitHub repo.
"""
import io
import struct
import sys
import requests
from publish_moneycontrol_pro_draft import get_connection,get_listing,call,check,PublishError,TITLE
LISTING_ID=4617919674
PREVIEWS=[
 (2,"https://ribhlab.wordpress.com/wp-content/uploads/2026/11/moneycontrol-pro-etsy-analytics.png","MoneyControl_Analytics.png"),
 (3,"https://ribhlab.wordpress.com/wp-content/uploads/2026/11/moneycontrol-pro-etsy-features.png","MoneyControl_Features.png"),
 (4,"https://ribhlab.wordpress.com/wp-content/uploads/2026/11/moneycontrol-pro-etsy-instant-access.png","MoneyControl_Instant_Access.png"),
]
def safe_image(url):
    try:r=requests.get(url,timeout=40)
    except requests.RequestException:raise PublishError("Preview transfer unavailable.") from None
    check(r.status_code==200 and 3000<len(r.content)<20*1024*1024,"Preview transfer failed.")
    check(r.content[:16]==bytes.fromhex("89504e470d0a1a0a0000000d49484452"),"Invalid preview PNG.")
    w,h=struct.unpack(">II",r.content[16:24])
    check(900<=w<=6000 and 650<=h<=6000,"Unexpected preview PNG dimensions.")
    return r.content
def run():
    # Verify all temporary previews BEFORE touching Etsy.
    previews=[(rank,name,safe_image(url)) for rank,url,name in PREVIEWS]
    headers,shop=get_connection()
    listing=get_listing(headers,shop)
    check(listing and int(listing.get("listing_id",0))==LISTING_ID and listing.get("state")=="draft",
          "Exact Etsy MoneyControl draft not found.")
    path=f"/application/listings/{LISTING_ID}/images"
    existing=call("GET",path,headers).get("results",[])
    check(len(existing)<=4,"Unexpected number of listing images; manual review required.")
    ranks={int(x["rank"]) for x in existing if "rank" in x}
    for rank,name,data in previews:
        if rank in ranks:
            print("IMAGE_RANK_ALREADY_PRESENT:",rank)
            continue
        call("POST",f"/application/shops/{shop}/listings/{LISTING_ID}/images",headers,
             data={"rank":str(rank)},files={"image":(name,io.BytesIO(data),"image/png")})
        print("IMAGE_RANK_UPLOADED:",rank)
    result=call("GET",path,headers).get("results",[])
    check(len(result)>=4,"All four listing images were not returned by Etsy.")
    print("FOUR_IMAGES_CONFIRMED:",len(result))
    print("STILL_DRAFT:",LISTING_ID)
if __name__=="__main__":
    try:run()
    except PublishError as e:
        print("MONEYCONTROL_PREVIEWS_FAILED:",str(e)[:200],file=sys.stderr);sys.exit(1)
    except Exception as e:
        print("MONEYCONTROL_PREVIEWS_FAILED:",type(e).__name__,file=sys.stderr);sys.exit(1)
