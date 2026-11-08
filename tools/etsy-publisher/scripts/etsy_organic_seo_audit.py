"""Read-only Etsy organic SEO audit for the connected RibhLab shop.

Writes public listing metadata only to job logs. Never changes or renews listings,
buys ads, creates coupons, or prints Etsy credentials.
"""
import json, os, sys, urllib.parse, urllib.request, urllib.error
from check_connection import verify, ConnectionErrorSafe

ROOT = "https://api.etsy.com/v3"

def get(path, headers):
    req=urllib.request.Request(ROOT+path,headers=headers)
    try:
        with urllib.request.urlopen(req,timeout=35) as result:
            return json.load(result)
    except urllib.error.HTTPError as error:
        raise ConnectionErrorSafe("Etsy GET failed: HTTP "+str(error.code)) from None
    except urllib.error.URLError:
        raise ConnectionErrorSafe("Etsy could not be reached") from None

def main():
    shop=verify()
    key=os.environ["ETSY_KEYSTRING"]
    shared=os.environ["ETSY_SHARED_SECRET"]
    refresh=os.environ["ETSY_REFRESH_TOKEN"]
    data=urllib.parse.urlencode({"grant_type":"refresh_token","client_id":key,"refresh_token":refresh}).encode()
    req=urllib.request.Request(ROOT+"/public/oauth/token",data=data,method="POST",headers={"Content-Type":"application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req,timeout=30) as response: token=json.load(response)["access_token"]
    except urllib.error.HTTPError as err:
        raise ConnectionErrorSafe("Etsy refresh denied: HTTP "+str(err.code)) from None
    headers={"x-api-key":key+":"+shared,"Authorization":"Bearer "+token}
    shop_details=get("/application/shops/"+shop,headers)
    print("SHOP_NAME:",shop_details.get("shop_name",""))
    print("SHOP_TITLE:",shop_details.get("title",""))
    print("SHOP_ANNOUNCEMENT_EXCERPT:",str(shop_details.get("announcement") or "")[:350])
    print("SHOP_ICON_PRESENT:",bool(shop_details.get("icon_url_fullxfull")))
    print("SHOP_BANNER_PRESENT:",bool(shop_details.get("image_url_760x100")))
    try:
        sections=get("/application/shops/"+shop+"/sections",headers).get("results",[])
        print("SHOP_SECTIONS:",json.dumps([{ "id":x.get("shop_section_id"),"title":x.get("title"),"active_listing_count":x.get("active_listing_count")} for x in sections],ensure_ascii=False))
    except ConnectionErrorSafe as error: print("SHOP_SECTIONS_UNAVAILABLE:",str(error))
    try:
        featured=get("/application/shops/"+shop+"/listings/featured",headers).get("results",[])
        print("FEATURED_LISTINGS:",json.dumps([{"id":x.get("listing_id"),"rank":x.get("featured_rank")} for x in featured]))
    except ConnectionErrorSafe as error: print("FEATURED_LISTINGS_UNAVAILABLE:",str(error))
    print("SHOP_ANNOUNCEMENT_PRESENT:",bool(shop_details.get("announcement","")))
    print("SHOP_POLICY_STATUS: not provided by getShop; review in Etsy Search Visibility.")
    all_listings=[]
    for state in ("active","draft","inactive","expired","sold_out"):
        offset=0
        while offset<500:
            query=urllib.parse.urlencode({"state":state,"limit":100,"offset":offset})
            batch=get(f"/application/shops/{shop}/listings?{query}",headers).get("results",[])
            for item in batch:
                lid=item.get("listing_id")
                if not lid:continue
                imgs=get(f"/application/listings/{lid}/images",headers).get("results",[])
                # Etsy list endpoints may omit `type`; check buyer files read-only regardless.
                try:
                    files=get(f"/application/shops/{shop}/listings/{lid}/files",headers).get("results",[])
                    count=len(files)
                except ConnectionErrorSafe:
                    count=None
                try:
                    videos=get(f"/application/listings/{lid}/videos",headers).get("results",[])
                    video_count=sum(1 for v in videos if v.get("video_state")=="active")
                except ConnectionErrorSafe:
                    video_count=None
                cover=next((x for x in imgs if x.get("rank")==1),{})
                obj={
                  "id":lid,
                  "state":state,
                  "title":item.get("title",""),
                  "tags":item.get("tags",[]),
                  "description_start":item.get("description","")[:2300],
                  "description_length":len(item.get("description","")),
                  "taxonomy_id":item.get("taxonomy_id"),
                  "section_id":item.get("shop_section_id"),
                  "featured_rank":item.get("featured_rank"),
                  "quantity":item.get("quantity"),
                  "should_auto_renew":item.get("should_auto_renew"),
                  "materials":item.get("materials"),
                  "attributes":item.get("attribute_values"),
                  "type":item.get("type"),
                  "image_count":len(imgs),
                  "video_count":video_count,
                  "cover_width":cover.get("full_width"),
                  "cover_height":cover.get("full_height"),
                  "cover_url":next((x.get("url_570xN") or x.get("url_fullxfull") for x in imgs if x.get("rank")==1),""),
                  "file_count":count,
                  "price":item.get("price"),
                  "created_timestamp":item.get("created_timestamp") or item.get("original_creation_timestamp"),
                  "cover_alt":next((x.get("alt_text","") for x in imgs if x.get("rank")==1),""),
                  "url":f"https://www.etsy.com/listing/{lid}"
                }
                print("LISTING_AUDIT_JSON:",json.dumps(obj,ensure_ascii=False))
                all_listings.append(obj)
            if len(batch)<100:break
            offset+=len(batch)
    print("AUDIT_COMPLETE",len(all_listings),"listings across states; NO CHANGES MADE.")
    with open(os.environ.get("GITHUB_STEP_SUMMARY","/dev/null"),"a",encoding="utf-8") as f:
        f.write("### Read-only Etsy organic SEO audit\n\n")
        f.write("| Listing | Status | Photos | Buyer files | Tags | Title |\n|---|---|---:|---:|---:|---|\n")
        for i in all_listings:
            safe_title=i["title"].replace("|"," ").replace("\n"," ").strip()[:100]
            f.write(f'| {i["id"]} | {i["state"]} | {i["image_count"]} | {i["file_count"]} | {len(i["tags"])} | {safe_title} |\n')

if __name__=="__main__":
    try:main()
    except ConnectionErrorSafe as e:
        print("AUDIT_FAILED:",e,file=sys.stderr);sys.exit(1)
    except Exception as e:
        print("AUDIT_FAILED: Unexpected "+type(e).__name__,file=sys.stderr);sys.exit(1)

# Seller-requested visibility diagnosis, 2026-11-08: fresh read-only status snapshot.
