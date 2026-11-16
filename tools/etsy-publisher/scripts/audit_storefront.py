"""Safe Etsy storefront audit: read-only, no orders, no changes or secrets in logs."""
import json, os, re, sys, urllib.parse, urllib.request, urllib.error
from check_connection import verify, ConnectionErrorSafe, BASE
def fetch_json(path, headers, stage):
    req=urllib.request.Request(BASE+path,headers=headers,method="GET")
    try:
        with urllib.request.urlopen(req,timeout=25) as r: return json.load(r)
    except urllib.error.HTTPError as e:
        print(stage+": HTTP "+str(e.code))
        return None
    except urllib.error.URLError:
        print(stage+": connection unavailable")
        return None

def main():
    sid=verify()
    key=os.environ["ETSY_KEYSTRING"]; shared=os.environ["ETSY_SHARED_SECRET"]
    refresh=os.environ["ETSY_REFRESH_TOKEN"]
    body=urllib.parse.urlencode({"grant_type":"refresh_token","client_id":key,"refresh_token":refresh}).encode()
    req=urllib.request.Request(BASE+"/public/oauth/token",data=body,headers={"Content-Type":"application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req,timeout=25) as r: token=json.load(r)["access_token"]
    except Exception: raise ConnectionErrorSafe("Could not refresh Etsy grant")
    headers={"Authorization":"Bearer "+token,"x-api-key":key+":"+shared}
    shop=fetch_json("/application/shops/"+sid,headers,"Shop overview")
    if isinstance(shop,dict):
        print("SHOP",json.dumps({k:shop.get(k) for k in ("shop_name","listing_active_count","transaction_sold_count","is_vacation") if k in shop},ensure_ascii=False))
    for state in ("active","draft","inactive"):
        rows=[];offset=0
        for page in range(5):
            query=urllib.parse.urlencode({"state":state,"limit":100,"offset":offset})
            d=fetch_json("/application/shops/"+sid+"/listings?"+query,headers,"List "+state)
            if not isinstance(d,dict):break
            items=d.get("results",[])
            if not isinstance(items,list):break
            rows.extend(items)
            if len(items)<100:break
            offset+=len(items)
        print("LISTINGS",state,"COUNT",len(rows))
        for row in rows[:30]:
            detail={"id":row.get("listing_id"),"title":str(row.get("title",""))[:105],
                    "state":row.get("state"),"price":row.get("price"),
                    "views":row.get("views"),"num_favorers":row.get("num_favorers"),
                    "type":row.get("type")}
            print("ITEM",json.dumps(detail,ensure_ascii=False,default=str))
            if state=="active":
                listing_id=row.get("listing_id")
                if listing_id and str(listing_id).isdigit():
                    imgs=fetch_json(f"/application/listings/{listing_id}/images",headers,"Images")
                    if isinstance(imgs,dict) and isinstance(imgs.get("results"),list):
                        print("IMAGES",listing_id,len(imgs["results"]))
    print("AUDIT COMPLETE (read-only, no publication)")
if __name__=="__main__":
    try:main()
    except ConnectionErrorSafe as e:print("ERROR",e);sys.exit(1)
