"""Improve Etsy visibility for the verified ProfitLens Team edition.
One guarded title + search tag update, with price and buyer files untouched.
"""
import json,os,sys,urllib.parse,urllib.request,urllib.error
from check_connection import verify,ConnectionErrorSafe
BASE="https://api.etsy.com/v3"
LID=4610734598
OLD="ProfitLens Team Finance Dashboard, Self-Hosted Profit and Expense Tracker with User Roles"
NEW="Self-Hosted Finance Dashboard for Teams | Python App with User Roles"
TAGS=["team finance app","self hosted finance","python dashboard","finance dashboard",
      "user role manager","invoice aging report","profit tracker","expense tracker",
      "receivables tracker","budget vs actual","csv import tool","sqlite backup",
      "financial reporting"]
def api(path,auth,method="GET",data=None):
    headers=auth.copy();body=None
    if data is not None:
        headers["Content-Type"]="application/x-www-form-urlencoded"
        body=urllib.parse.urlencode(data).encode("utf8")
    req=urllib.request.Request(BASE+path,headers=headers,data=body,method=method)
    try:
        with urllib.request.urlopen(req,timeout=35) as resp:return json.load(resp)
    except urllib.error.HTTPError as error:raise ConnectionErrorSafe(f"Etsy {method} HTTP {error.code}") from None
    except urllib.error.URLError:raise ConnectionErrorSafe("Etsy connection unavailable") from None
def main():
    if len(NEW)>140 or len(TAGS)!=13 or len(set(TAGS))!=13 or any(len(x)>20 for x in TAGS):
        raise ConnectionErrorSafe("Invalid SEO metadata")
    shop=verify()
    key=os.environ["ETSY_KEYSTRING"];secret=os.environ["ETSY_SHARED_SECRET"]
    refresh=os.environ["ETSY_REFRESH_TOKEN"]
    token=api("/public/oauth/token",{},"POST",{"grant_type":"refresh_token","client_id":key,"refresh_token":refresh})["access_token"]
    auth={"x-api-key":key+":"+secret,"Authorization":"Bearer "+token}
    base=f"/application/shops/{shop}/listings"
    rows=api(base+"?state=active&limit=100",auth).get("results",[])
    item=next((x for x in rows if int(x.get("listing_id",0))==LID),None)
    if not item or str(item.get("shop_id"))!=str(shop) or item.get("state")!="active":
        raise ConnectionErrorSafe("Target team listing not Active in expected shop")
    if item.get("title")==NEW and set(item.get("tags") or [])==set(TAGS):
        print("TEAM_SEO_ALREADY_CURRENT:",LID)
        return
    if item.get("title")!=OLD:
        raise ConnectionErrorSafe("Team title changed since baseline; no edits")
    price=item.get("price") or {}
    if price.get("amount")!=3995 or price.get("currency_code")!="USD":
        raise ConnectionErrorSafe("Team price baseline changed; no edits")
    images=api(f"/application/listings/{LID}/images",auth).get("results",[])
    files=api(f"/application/shops/{shop}/listings/{LID}/files",auth).get("results",[])
    if len(images)!=11 or len(files)!=1:
        raise ConnectionErrorSafe("Expected Team gallery and buyer file missing; no edits")
    result=api(f"{base}/{LID}",auth,"PATCH",{"title":NEW,"tags":",".join(TAGS)})
    if int(result.get("listing_id",0))!=LID:raise ConnectionErrorSafe("Unexpected update response")
    newrows=api(base+"?state=active&limit=100",auth).get("results",[])
    final=next((x for x in newrows if int(x.get("listing_id",0))==LID),None)
    if not final or final.get("state")!="active" or final.get("title")!=NEW or set(final.get("tags") or [])!=set(TAGS):
        raise ConnectionErrorSafe("Team SEO update unconfirmed")
    if (final.get("price") or {}).get("amount")!=3995:
        raise ConnectionErrorSafe("Team price changed unexpectedly")
    print("TEAM_TITLE_AND_TAGS_UPDATED:",LID)
    print("NEW_TITLE:",NEW)
    print("VERIFIED_13_TAGS:",len(TAGS))
    print("TEAM_LISTING_ACTIVE: yes, PRICE_USD: 39.95, ORIGINAL_MEDIA_AND_FILES_UNCHANGED")
    print("NO_PAID_ADS_NO_RENEWALS_NO_DISCOUNTS")
if __name__=="__main__":
    try:main()
    except ConnectionErrorSafe as e:print("TEAM_SEO_FAILED:",e,file=sys.stderr);sys.exit(1)
    except Exception as e:print("TEAM_SEO_FAILED: unexpected "+type(e).__name__,file=sys.stderr);sys.exit(1)
