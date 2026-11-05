"""Free organic SEO: clarify that ProfitLens v3.6 is an HTML offline app.
Only update one existing active listing title; no price, inventory, files,
ad spend, coupon, auto-renewal, or other shop settings are changed.
Read-only inventory health check across listing states.
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from check_connection import verify, ConnectionErrorSafe

ROOT="https://api.etsy.com/v3"
TARGET=4610490076
OLD_TITLE="ProfitLens Offline Finance Dashboard, Profit and Expense Tracker for Small Business"
NEW_TITLE="Offline HTML Finance Dashboard | Profit & Expense Tracker for Small Business"

def call(path,headers,method="GET",data=None):
    req=urllib.request.Request(ROOT+path,headers=headers,method=method,data=data)
    try:
        with urllib.request.urlopen(req,timeout=35) as response: return json.load(response)
    except urllib.error.HTTPError as exc:
        raise ConnectionErrorSafe(f"Etsy API {method} rejected (HTTP {exc.code}).") from None
    except urllib.error.URLError:
        raise ConnectionErrorSafe("Etsy API unreachable.") from None

def main():
    shop=verify()
    key=os.environ["ETSY_KEYSTRING"];secret=os.environ["ETSY_SHARED_SECRET"]
    refresh=os.environ["ETSY_REFRESH_TOKEN"]
    body=urllib.parse.urlencode({"grant_type":"refresh_token","client_id":key,"refresh_token":refresh}).encode("utf-8")
    access=call("/public/oauth/token",{"Content-Type":"application/x-www-form-urlencoded"},"POST",body)["access_token"]
    headers={"x-api-key":key+":"+secret,"Authorization":"Bearer "+access}
    base=f"/application/shops/{shop}/listings"
    known={}
    for state in ("active","draft","inactive","expired","sold_out"):
        offset=0
        for page in range(5):
            query=urllib.parse.urlencode({"state":state,"limit":100,"offset":offset})
            try:
                rows=call(base+"?"+query,headers).get("results",[])
            except ConnectionErrorSafe as exc:
                # Older Etsy accounts may not return every state filter.
                print("STATE_UNAVAILABLE",state,str(exc))
                break
            for item in rows:
                lid=int(item.get("listing_id") or 0)
                if lid and lid not in known:
                    known[lid]={"state":state,"title":str(item.get("title","")).strip(),"shop_id":str(item.get("shop_id"))}
                    print("FOUND_LISTING",lid,"STATE",state,"TITLE",known[lid]["title"][:125])
            if len(rows)<100:break
            offset+=len(rows)
    item=known.get(TARGET)
    if not item or item["state"]!="active" or item["shop_id"]!=str(shop):
        raise ConnectionErrorSafe("Target ProfitLens listing is not active in the expected shop; no changes made.")
    if item["title"]==NEW_TITLE:
        print("ALREADY_OPTIMIZED",TARGET,NEW_TITLE)
        return
    if item["title"]!=OLD_TITLE:
        raise ConnectionErrorSafe("Current ProfitLens title differs from verified baseline; no change made.")
    if len(NEW_TITLE)>140:
        raise ConnectionErrorSafe("Proposed Etsy title is too long.")
    result=call(f"{base}/{TARGET}",{**headers,"Content-Type":"application/x-www-form-urlencoded"},
                "PATCH",urllib.parse.urlencode({"title":NEW_TITLE}).encode("utf-8"))
    if str(result.get("listing_id"))!=str(TARGET):
        raise ConnectionErrorSafe("Etsy did not confirm listing ID after title update.")
    # Re-check through the owner's active listing collection.
    query=urllib.parse.urlencode({"state":"active","limit":100,"offset":0})
    active=call(base+"?"+query,headers).get("results",[])
    found=next((x for x in active if x.get("listing_id")==TARGET),None)
    if not found or found.get("title")!=NEW_TITLE:
        raise ConnectionErrorSafe("Etsy did not confirm updated title in the active shop collection.")
    print("SEO_TITLE_UPDATED",TARGET,NEW_TITLE)
    print("LISTING_STILL_ACTIVE",TARGET)
    with open(os.environ.get("GITHUB_STEP_SUMMARY","/dev/null"),"a",encoding="utf-8") as f:
        f.write(f"### ProfitLens organic SEO title updated\n\n")
        f.write(f"- Listing: {TARGET} (remains ACTIVE)\n")
        f.write(f"- Old: {OLD_TITLE}\n- New: **{NEW_TITLE}**\n")
        f.write("- No ads, discounts, renewals, file changes, or new listings.\n")

if __name__=="__main__":
    try: main()
    except ConnectionErrorSafe as exc:
        print("SEO_UPDATE_FAILED:",str(exc),file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print("SEO_UPDATE_FAILED: Unexpected "+type(exc).__name__,file=sys.stderr)
        sys.exit(1)
