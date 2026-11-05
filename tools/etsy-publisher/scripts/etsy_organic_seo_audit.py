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
    print("SHOP_ANNOUNCEMENT_PRESENT:",bool(shop_details.get("announcement","")))
    print("SHOP_POLICY_PRESENT:",bool(shop_details.get("policy_welcome","") or shop_details.get("policy_seller_info","")))
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
                obj={
                  "id":lid,
                  "state":state,
                  "title":item.get("title",""),
                  "tags":item.get("tags",[]),
                  "description_start":item.get("description","")[:400],
                  "taxonomy_id":item.get("taxonomy_id"),
                  "type":item.get("type"),
                  "image_count":len(imgs),
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
