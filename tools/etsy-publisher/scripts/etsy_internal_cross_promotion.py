"""Add Etsy-internal discovery links to four verified active RibhLab listings.

Etsy Seller Handbook recommends linking related Etsy listings near the end of
descriptions. This job does exactly that; no price changes, ad spend, discounts,
renewals, media or buyer-file changes. Fail closed on unknown listings.
"""
import os,sys,json,urllib.error,urllib.parse,urllib.request
from check_connection import verify,ConnectionErrorSafe
API="https://api.etsy.com/v3"
HEAD="\n\nEXPLORE MORE FROM RIBHLABDIGITAL\n"
SHOP="https://www.etsy.com/shop/RibhLabDigital"
LINKS={
 4610490076: [
   "Need shared access for staff? Explore the self-hosted ProfitLens Team edition:",
   "https://www.etsy.com/listing/4610734598",
   "Want both the no-server and team editions together? See the two-in-one bundle:",
   "https://www.etsy.com/listing/4610758074"
 ],
 4610734598: [
   "Need a personal edition that runs without a server? Explore ProfitLens Offline:",
   "https://www.etsy.com/listing/4610490076",
   "Want both options in one download? Explore the two-in-one bundle:",
   "https://www.etsy.com/listing/4610758074"
 ],
 4610758074: [
   "Only need one edition? See the individual products:",
   "Offline HTML edition (no server): https://www.etsy.com/listing/4610490076",
   "Team edition (self-hosted Python/SQLite): https://www.etsy.com/listing/4610734598"
 ],
 4607532475: [
   "Looking for financial reporting tools instead of a website theme? Explore the RibhLabDigital finance products:",
   SHOP
 ]
}
EXPECTED_TITLES={
 4610490076:"Offline HTML Finance Dashboard | Profit & Expense Tracker for Small Business",
 4610734598:"ProfitLens Team Finance Dashboard, Self-Hosted Profit and Expense Tracker with User Roles",
 4610758074:"Finance Dashboard Bundle | Offline HTML + Self-Hosted Team App for Small Business",
 4607532475:"WordPress Magazine Theme | Arabic RTL News & Blog Template — RibhLab Viva"
}
PRICES={4610490076:2995,4610734598:3995,4610758074:4893,4607532475:2500}
def request(path,headers,method="GET",data=None):
    h=dict(headers)
    body=None
    if data is not None:
        h["Content-Type"]="application/x-www-form-urlencoded"
        body=urllib.parse.urlencode(data).encode("utf8")
    req=urllib.request.Request(API+path,headers=h,data=body,method=method)
    try:
        with urllib.request.urlopen(req,timeout=45) as resp:return json.load(resp)
    except urllib.error.HTTPError as exc:
        raise ConnectionErrorSafe(f"Etsy {method} request failed (HTTP {exc.code}).") from None
    except urllib.error.URLError:
        raise ConnectionErrorSafe("Etsy not reachable.") from None

def main():
    shop=verify()
    key=os.environ["ETSY_KEYSTRING"]
    secret=os.environ["ETSY_SHARED_SECRET"]
    r=request("/public/oauth/token",{},"POST",{
        "grant_type":"refresh_token","client_id":key,"refresh_token":os.environ["ETSY_REFRESH_TOKEN"]})
    auth={"x-api-key":key+":"+secret,"Authorization":"Bearer "+r["access_token"]}
    path=f"/application/shops/{shop}/listings"
    active=request(path+"?state=active&limit=100",auth).get("results",[])
    rows={int(x["listing_id"]):x for x in active}
    for lid in LINKS:
        item=rows.get(lid)
        if not item or item.get("state")!="active" or str(item.get("shop_id"))!=str(shop):
            raise ConnectionErrorSafe(f"Listing {lid} not active or not in connected shop; no changes")
        if item.get("title")!=EXPECTED_TITLES[lid]:
            raise ConnectionErrorSafe(f"Listing {lid} title has changed; no edits")
        p=item.get("price") or {}
        if p.get("amount")!=PRICES[lid] or p.get("currency_code")!="USD":
            raise ConnectionErrorSafe(f"Listing {lid} price differs; no edits")
        desc=item.get("description")
        if not isinstance(desc,str) or len(desc)<300:
            raise ConnectionErrorSafe(f"Listing {lid} description missing; no edits")
    # All four verified before first external write.
    for lid,details in LINKS.items():
        item=rows[lid]
        desc=item["description"]
        if HEAD.strip() in desc:
            if all(link in desc for link in details if link.startswith("https://")):
                print("RELATED_ETSY_LINKS_ALREADY_PRESENT:",lid)
                continue
            raise ConnectionErrorSafe("Existing cross-promotion block differs; not overwriting")
        appendix=HEAD+"\n".join(details)+"\n\nOr browse the whole shop: "+SHOP
        updated=desc.rstrip()+appendix
        if len(updated)>13000:
            raise ConnectionErrorSafe("New description exceeds Etsy safety limit")
        reply=request(f"{path}/{lid}",auth,"PATCH",{"description":updated})
        if int(reply.get("listing_id",0))!=lid:
            raise ConnectionErrorSafe(f"Unexpected Etsy response for {lid}")
        print("RELATED_ETSY_LINKS_ADDED:",lid,"NEW_LENGTH:",len(updated))
    again=request(path+"?state=active&limit=100",auth).get("results",[])
    newrows={int(x["listing_id"]):x for x in again}
    for lid in LINKS:
        item=newrows.get(lid)
        if not item or item.get("state")!="active":
            raise ConnectionErrorSafe(f"Listing {lid} no longer active")
        if item.get("title")!=EXPECTED_TITLES[lid]:
            raise ConnectionErrorSafe(f"Unexpected title change {lid}")
        p=item.get("price") or {}
        if p.get("amount")!=PRICES[lid] or p.get("currency_code")!="USD":
            raise ConnectionErrorSafe(f"Unexpected price change {lid}")
        desc=item.get("description") or ""
        if not all(link in desc for link in LINKS[lid] if link.startswith("https://")) or HEAD.strip() not in desc:
            raise ConnectionErrorSafe(f"Etsy has not confirmed cross-links for {lid}")
        if SHOP not in desc:
            raise ConnectionErrorSafe(f"Shop link missing from {lid}")
        print("VERIFIED_CROSS_LINKS:",lid,"ACTIVE_AND_PRICE_UNCHANGED")
    print("SUCCESS_FOUR_LISTINGS_INTERNAL_CROSS_PROMOTION")
    print("NO_PAID_ADS_NO_DISCOUNTS_NO_RENEWALS")
    with open(os.environ.get("GITHUB_STEP_SUMMARY","/dev/null"),"a",encoding="utf-8") as f:
        f.write("### Organic Etsy cross-promotion\n\n")
        for lid in LINKS:
            f.write(f"- [Listing {lid}](https://www.etsy.com/listing/{lid}) links to relevant shop products. Verified ACTIVE and original price.\n")
        f.write("\nNo ads, discounts or renewals were triggered.\n")
if __name__=="__main__":
    try:main()
    except ConnectionErrorSafe as exc:print("CROSS_PROMOTION_FAILED:",exc,file=sys.stderr);sys.exit(1)
    except Exception as exc:print("CROSS_PROMOTION_FAILED: unexpected "+type(exc).__name__,file=sys.stderr);sys.exit(1)
