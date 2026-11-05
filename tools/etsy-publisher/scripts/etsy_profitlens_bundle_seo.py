"""Improve one existing RibhLab ProfitLens 2-in-1 Etsy listing organically.

Updates only title, descriptive opening, and 13 relevant tags.
Safety: exact shop/listing/title/price/assets expected, active remains active.
Does NOT create listings, change price, renew, discount or use Etsy Ads.
"""
import os,sys,re,json,urllib.parse,urllib.request,urllib.error
from check_connection import verify,ConnectionErrorSafe
BASE="https://api.etsy.com/v3"
LID=4610758074
OLD="ProfitLens Finance Dashboard Bundle | Offline HTML + Team Server, Self Hosted Finance App, Small Business Tracker"
NEW="Finance Dashboard Bundle | Offline HTML + Self-Hosted Team App for Small Business"
TAGS=["finance dashboard","finance app bundle","offline finance app","self hosted app",
      "team finance app","html dashboard","small business app","profit tracker",
      "expense tracker","csv import tool","sqlite backup","budget vs actual","business software"]
OLD_OPEN=("PROFITLENS 3.6 — 2-IN-1 FINANCE DASHBOARD BUNDLE\n"
          "OFFLINE EDITION + SELF-HOSTED TEAM SERVER\n\n"
          "Get both standalone ProfitLens software editions together in one digital bundle.\n\n")
NEW_OPEN=("FINANCE DASHBOARD BUNDLE — PROFITLENS 3.6 (2-IN-1)\n"
          "Offline HTML dashboard + self-hosted Team app, together in one instant digital download.\n"
          "Two separate software editions: a no-server browser dashboard for individual use "
          "and a Python/SQLite shared dashboard with user accounts and roles for business teams. "
          "No Excel workbook, hosted subscription or automatic sync between editions.\n\n")
def call(path,auth,method="GET",fields=None):
    data=None
    headers=dict(auth)
    if fields is not None:
        data=urllib.parse.urlencode(fields).encode("utf-8")
        headers["Content-Type"]="application/x-www-form-urlencoded"
    req=urllib.request.Request(BASE+path,headers=headers,method=method,data=data)
    try:
        with urllib.request.urlopen(req,timeout=35) as resp:return json.load(resp)
    except urllib.error.HTTPError as e:raise ConnectionErrorSafe(f"Etsy {method} returned HTTP {e.code}") from None
    except urllib.error.URLError:raise ConnectionErrorSafe("Etsy unreachable") from None
def main():
    if len(TAGS)!=13 or len(set(TAGS))!=13 or any(len(x)>20 for x in TAGS) or len(NEW)>140:
        raise ConnectionErrorSafe("SEO metadata validation failed")
    shop=verify()
    key=os.environ["ETSY_KEYSTRING"];shared=os.environ["ETSY_SHARED_SECRET"]
    refresh=os.environ["ETSY_REFRESH_TOKEN"]
    token=call("/public/oauth/token",{},"POST",{"grant_type":"refresh_token","client_id":key,"refresh_token":refresh})["access_token"]
    auth={"x-api-key":key+":"+shared,"Authorization":"Bearer "+token}
    listings=call(f"/application/shops/{shop}/listings?state=active&limit=100",auth).get("results",[])
    item=next((x for x in listings if int(x.get("listing_id",0))==LID),None)
    if not item or str(item.get("shop_id"))!=str(shop) or item.get("state")!="active":
        raise ConnectionErrorSafe("The verified bundle is not active in the connected shop")
    if item.get("title")==NEW:
        print("BUNDLE_ALREADY_OPTIMIZED:",LID)
        return
    if item.get("title")!=OLD:
        raise ConnectionErrorSafe("Bundle title changed since audit; no update")
    price=item.get("price") or {}
    if price.get("amount")!=4893 or price.get("divisor")!=100 or price.get("currency_code")!="USD":
        raise ConnectionErrorSafe("Bundle price changed from baseline; no update")
    images=call(f"/application/listings/{LID}/images",auth).get("results",[])
    files=call(f"/application/shops/{shop}/listings/{LID}/files",auth).get("results",[])
    if len(images)<7 or len(files)!=1 or len(item.get("tags",[]))!=13:
        raise ConnectionErrorSafe("Bundle gallery, digital attachment or tags changed; no update")
    desc=item.get("description") or ""
    if not desc.startswith(OLD_OPEN) or "This bundle is two separate editions" not in desc:
        raise ConnectionErrorSafe("Bundle description baseline changed; no update")
    revised=NEW_OPEN+desc[len(OLD_OPEN):]
    response=call(f"/application/shops/{shop}/listings/{LID}",auth,"PATCH",
                  {"title":NEW,"description":revised,"tags":",".join(TAGS)})
    if int(response.get("listing_id",0))!=LID:raise ConnectionErrorSafe("Unexpected updated listing ID")
    fresh=call(f"/application/shops/{shop}/listings?state=active&limit=100",auth).get("results",[])
    check=next((x for x in fresh if int(x.get("listing_id",0))==LID),None)
    if not check or check.get("state")!="active" or check.get("title")!=NEW:
        raise ConnectionErrorSafe("Title or active status not verified")
    if set(check.get("tags") or [])!=set(TAGS) or not str(check.get("description","")).startswith(NEW_OPEN):
        raise ConnectionErrorSafe("Tags/description verification failed")
    after=check.get("price") or {}
    if after.get("amount")!=4893 or after.get("currency_code")!="USD":
        raise ConnectionErrorSafe("Unexpected price change detected")
    print("BUNDLE_SEO_UPDATED:",LID)
    print("NEW_TITLE:",NEW)
    print("TAGS_VERIFIED:",len(TAGS))
    print("DESCRIPTION_OPENING_VERIFIED")
    print("PRICE_UNCHANGED: 48.93 USD")
    print("STATUS: ACTIVE")
    print("NO_ADS_NO_RENEWALS_NO_COUPONS")
    with open(os.environ.get("GITHUB_STEP_SUMMARY","/dev/null"),"a",encoding="utf-8") as f:
        f.write(f"### ProfitLens Bundle organic SEO\n\n[Etsy Listing {LID}](https://www.etsy.com/listing/{LID})\n\n")
        f.write("- Title: "+NEW+"\n- 13 differentiated search tags and clear 2-in-1 description\n")
        f.write("- Still Active, price 48.93 USD unchanged; 7 original images and buyer ZIP untouched\n")
if __name__=="__main__":
    try: main()
    except ConnectionErrorSafe as e:print("BUNDLE_SEO_FAILED:",e,file=sys.stderr);sys.exit(1)
    except Exception as e:print("BUNDLE_SEO_FAILED: unexpected "+type(e).__name__,file=sys.stderr);sys.exit(1)
