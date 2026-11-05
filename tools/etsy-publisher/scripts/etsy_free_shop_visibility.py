"""Free Etsy shop optimization: storefront title, message, and browse sections.
Runs against only the authorized RibhLabDigital shop, never ad/fees/inventory.
Requires shops_w: if absent, exits safely with an explicit permissions report.
"""
import os,sys,json,urllib.error,urllib.parse,urllib.request
from check_connection import verify,ConnectionErrorSafe
BASE="https://api.etsy.com/v3"
OLD_TITLE="Premium WordPress Themes & Digital Templates"
NEW_TITLE="Finance Dashboards, WordPress Themes & Digital Tools"
OLD_ANNOUNCEMENT="Welcome to RibhLabDigital!"
NEW_ANNOUNCEMENT=(
"Welcome to RibhLabDigital! Explore original digital downloads for small businesses "
"and creators: ProfitLens Offline HTML financial dashboard, ProfitLens Team self-hosted "
"Python/SQLite app, the 2-in-1 Finance Bundle, and RibhLab Viva WordPress Magazine "
"Theme with Arabic RTL. Compare the product screenshots, inclusions and setup "
"requirements on each listing before purchasing. Digital products only; no physical "
"delivery or hosted subscription is included. Questions? Send us an Etsy message."
)
EXPECTED={4610490076:("Finance Dashboards",None),4610734598:("Finance Dashboards",None),
          4610758074:("Finance Bundles",None),4607532475:("WordPress Themes",61234865)}

def call(path,headers,method="GET",form=None,allow403=False):
    h=headers.copy()
    body=None
    if form is not None:
        h["Content-Type"]="application/x-www-form-urlencoded"
        body=urllib.parse.urlencode(form).encode("utf-8")
    req=urllib.request.Request(BASE+path,headers=h,data=body,method=method)
    try:
        with urllib.request.urlopen(req,timeout=45) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        if allow403 and exc.code in (401,403):
            return {"_insufficient_shop_scopes":exc.code}
        raise ConnectionErrorSafe(f"Etsy {method} refused (HTTP {exc.code}) on supported shop endpoint") from None
    except urllib.error.URLError:
        raise ConnectionErrorSafe("Etsy connection not available") from None

def main():
    if len(NEW_TITLE)>55 or any(len(s)>24 for s in ("Finance Dashboards","Finance Bundles")):
        raise ConnectionErrorSafe("Invalid Etsy shop title or section length")
    shop=verify()
    key=os.environ["ETSY_KEYSTRING"]
    secret=os.environ["ETSY_SHARED_SECRET"]
    exchange=call("/public/oauth/token",{},"POST",
             {"grant_type":"refresh_token","client_id":key,"refresh_token":os.environ["ETSY_REFRESH_TOKEN"]})
    token=exchange["access_token"]
    headers={"x-api-key":key+":"+secret,"Authorization":"Bearer "+token}
    details=call("/application/shops/"+shop,headers)
    if details.get("shop_name")!="RibhLabDigital":
        raise ConnectionErrorSafe("Unexpected Etsy shop; no modifications")
    items=call(f"/application/shops/{shop}/listings?state=active&limit=100",headers).get("results",[])
    by_id={int(x["listing_id"]):x for x in items}
    if not all(i in by_id and str(by_id[i].get("shop_id"))==str(shop)
               and by_id[i].get("state")=="active" for i in EXPECTED):
        raise ConnectionErrorSafe("The four expected active RibhLab products are not present.")
    sections=call(f"/application/shops/{shop}/sections",headers).get("results",[])
    known={row.get("title"):int(row["shop_section_id"]) for row in sections}
    if known.get("WordPress Themes")!=61234865:
        raise ConnectionErrorSafe("Unexpected WordPress section state")
    print("SHOP_ACTIVE_PRODUCTS_VERIFIED:",len(EXPECTED))
    print("SHOP_CURRENT_TITLE:",details.get("title"))
    print("SHOP_CURRENT_SECTIONS:",json.dumps(known))
    if details.get("title") not in (OLD_TITLE,NEW_TITLE):
        raise ConnectionErrorSafe("Shop title baseline changed; no overwrite")
    if details.get("announcement") not in (OLD_ANNOUNCEMENT,NEW_ANNOUNCEMENT):
        raise ConnectionErrorSafe("Shop announcement changed; no overwrite")
    if details.get("title")!=NEW_TITLE or details.get("announcement")!=NEW_ANNOUNCEMENT:
        updated=call("/application/shops/"+shop,headers,"PUT",
            {"title":NEW_TITLE,"announcement":NEW_ANNOUNCEMENT},allow403=True)
        if "_insufficient_shop_scopes" in updated:
            print("SHOPS_WRITE_PERMISSION_MISSING: HTTP",updated["_insufficient_shop_scopes"])
            print("REQUIRES_EXPLICIT_SELLER_REAUTH_WITH_SHOPS_W; NO CHANGES MADE")
            return
        verify_shop=call("/application/shops/"+shop,headers)
        if verify_shop.get("title")!=NEW_TITLE or verify_shop.get("announcement")!=NEW_ANNOUNCEMENT:
            raise ConnectionErrorSafe("Shop update not confirmed")
        print("SHOP_TITLE_UPDATED:",NEW_TITLE)
        print("SHOP_ANNOUNCEMENT_UPDATED_AND_VERIFIED")
    else:
        print("SHOP_TITLE_AND_ANNOUNCEMENT_ALREADY_CURRENT")
    # Organize visible shop navigation; the existing WordPress section is left unchanged.
    for name in ("Finance Dashboards","Finance Bundles"):
        if name not in known:
            record=call(f"/application/shops/{shop}/sections",headers,"POST",{"title":name})
            sid=record.get("shop_section_id")
            if not sid:
                raise ConnectionErrorSafe("Etsy did not create section "+name)
            known[name]=int(sid)
            print("SHOP_SECTION_CREATED:",name,sid)
        else:
            print("SHOP_SECTION_EXISTS:",name,known[name])
    for lid,(label,old_id) in EXPECTED.items():
        if lid==4607532475: continue
        current=by_id[lid]
        sid=known[label]
        current_section=current.get("shop_section_id")
        if current_section and int(current_section)==sid:
            print("LISTING_SECTION_ALREADY_SET:",lid,label)
            continue
        if current_section not in (None,0):
            raise ConnectionErrorSafe(f"Listing {lid} moved by a seller during this task, stopping")
        patched=call(f"/application/shops/{shop}/listings/{lid}",headers,"PATCH",{"section_id":sid})
        if int(patched.get("listing_id") or 0)!=lid:
            raise ConnectionErrorSafe("Etsy listing section update lacked confirmation")
        print("LISTING_SECTION_ASSIGNED:",lid,label)
    final=call(f"/application/shops/{shop}/listings?state=active&limit=100",headers).get("results",[])
    latest={int(x["listing_id"]):x for x in final}
    if not all(int(latest[lid].get("shop_section_id") or 0)==known[label] for lid,(label,_) in EXPECTED.items()):
        raise ConnectionErrorSafe("Shop section audit incomplete")
    print("ALL_4_PRODUCTS_ORGANIZED_IN_PUBLIC_SHOP")
    print("NO_ADS_NO_PAID_RENEWALS_NO_DISCOUNTS_NO_PRICE_CHANGES")

if __name__=="__main__":
    try:main()
    except ConnectionErrorSafe as e:print("SHOP_OPTIMIZE_FAILED:",e,file=sys.stderr);sys.exit(1)
    except Exception as e:print("SHOP_OPTIMIZE_FAILED: unexpected "+type(e).__name__,file=sys.stderr);sys.exit(1)
