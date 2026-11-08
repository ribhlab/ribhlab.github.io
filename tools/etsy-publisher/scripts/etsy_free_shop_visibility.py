"""Free Etsy shop optimization: storefront title, message, and browse sections.
Runs against only the authorized RibhLabDigital shop, never ad/fees/inventory.
Requires shops_w: if absent, exits safely with an explicit permissions report.
Revalidated after the seller confirmed completing the Etsy OAuth reauthorization.
Fresh seller confirmation: re-check granted shops_w and execute guarded updates.
Verify current GitHub Actions credential after seller supplied existing approved Etsy Keystring.
Latest explicit seller request: verify current shop write authorization and apply guarded improvements if allowed.
"""
import os,sys,json,urllib.error,urllib.parse,urllib.request
from check_connection import verify,ConnectionErrorSafe
BASE="https://api.etsy.com/v3"
OLD_TITLE="Premium WordPress Themes & Digital Templates"
PREVIOUS_TITLE="Finance Dashboards, WordPress Themes & Digital Tools"
NEW_TITLE="Finance Dashboards & Small Business Reporting Tools"
OLD_ANNOUNCEMENT="Welcome to RibhLabDigital!"
PREVIOUS_ANNOUNCEMENT=(
"Welcome to RibhLabDigital! Explore original digital downloads for small businesses "
"and creators: ProfitLens Offline HTML financial dashboard, ProfitLens Team self-hosted "
"Python/SQLite app, the 2-in-1 Finance Bundle, and RibhLab Viva WordPress Magazine "
"Theme with Arabic RTL. Compare the product screenshots, inclusions and setup "
"requirements on each listing before purchasing. Digital products only; no physical "
"delivery or hosted subscription is included. Questions? Send us an Etsy message."
)
NEW_ANNOUNCEMENT=(
"Welcome to RibhLabDigital! Explore ProfitLens 3.6 digital finance software "
"for small businesses: an offline HTML profit and expense dashboard, a self-hosted "
"Python/SQLite team reporting app with roles, and a 2-in-1 bundle containing both "
"editions. Review the screenshots, buyer files, setup requirements and compatibility "
"on each product page. These are digital downloads, not Excel workbooks or hosted "
"subscriptions. Questions? Send us an Etsy message."
)
EXPECTED={4610490076:("Finance Dashboards",None),4610734598:("Finance Dashboards",None),
          4610758074:("Finance Bundles",None)}

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
            # Never output tokens, HTTP headers, or raw untrusted API error messages.
            try:
                raw=exc.read(2048).decode("utf-8","replace").lower()
            except Exception:
                raw=""
            diagnostic=("scope" if "scope" in raw else
                        "permission" if "permission" in raw or "forbidden" in raw else
                        "access" if "access" in raw else
                        "other_http_"+str(exc.code))
            print("ETSY_WRITE_ERROR_CATEGORY:",diagnostic)
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
    granted=set(str(exchange.get("scope") or "").split())
    safe_scopes=sorted(granted.intersection({"listings_r","listings_w","shops_r","shops_w"}))
    print("ETSY_GRANTED_SCOPES:",",".join(safe_scopes) if granted else "not_reported")
    if granted and "shops_w" not in granted:
        print("ETSY_TOKEN_LACKS_SHOPS_W: update ETSY_REFRESH_TOKEN with the newly reauthorized token")
        print("NO_CHANGES_MADE")
        return
    headers={"x-api-key":key+":"+secret,"Authorization":"Bearer "+token}
    details=call("/application/shops/"+shop,headers)
    if details.get("shop_name")!="RibhLabDigital":
        raise ConnectionErrorSafe("Unexpected Etsy shop; no modifications")
    items=call(f"/application/shops/{shop}/listings?state=active&limit=100",headers).get("results",[])
    by_id={int(x["listing_id"]):x for x in items}
    if not all(i in by_id and str(by_id[i].get("shop_id"))==str(shop)
               and by_id[i].get("state")=="active" for i in EXPECTED):
        raise ConnectionErrorSafe("The three verified finance products are not all active; no shop edits.")
    sections=call(f"/application/shops/{shop}/sections",headers).get("results",[])
    known={row.get("title"):int(row["shop_section_id"]) for row in sections}
    print("SHOP_ACTIVE_PRODUCTS_VERIFIED:",len(EXPECTED))
    print("SHOP_CURRENT_TITLE:",details.get("title"))
    print("SHOP_CURRENT_SECTIONS:",json.dumps(known))
    if details.get("title") not in (OLD_TITLE,PREVIOUS_TITLE,NEW_TITLE):
        raise ConnectionErrorSafe("Shop title baseline changed; no overwrite")
    announcement=details.get("announcement") or ""
    is_old=(announcement.lstrip().startswith("Welcome to RibhLabDigital!")
            and "WordPress themes" in announcement
            and "SPECIAL LAUNCH OFFER" in announcement)
    if announcement not in (PREVIOUS_ANNOUNCEMENT,NEW_ANNOUNCEMENT) and not is_old:
        raise ConnectionErrorSafe("Shop announcement differs from the verified live baseline; no overwrite")
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
    # Organize only verified active finance products; leave other shop assets untouched.
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
        current=by_id[lid]
        sid=known[label]
        current_section=current.get("shop_section_id")
        if current_section and int(current_section)==sid:
            print("LISTING_SECTION_ALREADY_SET:",lid,label)
            continue
        if current_section not in (None,0):
            raise ConnectionErrorSafe(f"Listing {lid} moved by a seller during this task, stopping")
        patched=call(f"/application/shops/{shop}/listings/{lid}",headers,"PATCH",{"shop_section_id":sid})
        if int(patched.get("listing_id") or 0)!=lid:
            raise ConnectionErrorSafe("Etsy listing section update lacked confirmation")
        if int(patched.get("shop_section_id") or 0)!=sid:
            raise ConnectionErrorSafe("Etsy accepted listing update without assigning shop_section_id")
        print("LISTING_SECTION_ASSIGNED:",lid,label)
    final=call(f"/application/shops/{shop}/listings?state=active&limit=100",headers).get("results",[])
    latest={int(x["listing_id"]):x for x in final}
    if not all(int(latest[lid].get("shop_section_id") or 0)==known[label] for lid,(label,_) in EXPECTED.items()):
        raise ConnectionErrorSafe("Shop section audit incomplete")
    print("ALL_3_ACTIVE_FINANCE_PRODUCTS_ORGANIZED_IN_PUBLIC_SHOP")
    # User no longer sells WordPress themes. Remove only the verified, fully empty
    # legacy SECTION, never a listing or a category containing any listings.
    final_sections=call(f"/application/shops/{shop}/sections",headers).get("results",[])
    legacy=[s for s in final_sections if s.get("title")=="WordPress Themes"]
    if legacy:
        if len(legacy)!=1 or int(legacy[0].get("shop_section_id") or 0)!=61234865:
            raise ConnectionErrorSafe("Unexpected WordPress section identity; no deletion")
        legacy_id=61234865
        if int(legacy[0].get("active_listing_count") if legacy[0].get("active_listing_count") is not None else -1)!=0:
            raise ConnectionErrorSafe("Legacy WordPress section is not empty; no deletion")
        for state in ("active","draft","inactive","expired","sold_out"):
            offset=0
            while offset<500:
                q=urllib.parse.urlencode({"state":state,"limit":100,"offset":offset})
                rows=call(f"/application/shops/{shop}/listings?{q}",headers).get("results",[])
                if any(int(x.get("shop_section_id") or 0)==legacy_id for x in rows):
                    raise ConnectionErrorSafe("A listing uses the legacy WordPress section; no deletion")
                if len(rows)<100:
                    break
                offset+=100
        req=urllib.request.Request(
            f"{BASE}/application/shops/{shop}/sections/{legacy_id}",
            headers=headers,method="DELETE")
        try:
            with urllib.request.urlopen(req,timeout=35) as result:
                status=result.status
        except urllib.error.HTTPError as exc:
            raise ConnectionErrorSafe(f"Could not remove empty legacy section (HTTP {exc.code})") from None
        if status!=204:
            raise ConnectionErrorSafe("Etsy did not confirm empty section deletion")
        after_sections=call(f"/application/shops/{shop}/sections",headers).get("results",[])
        if any(int(x.get("shop_section_id") or 0)==legacy_id for x in after_sections):
            raise ConnectionErrorSafe("Legacy WordPress section still present after DELETE")
        print("REMOVED_EMPTY_WORDPRESS_SECTION:",legacy_id)
    else:
        print("NO_LEGACY_WORDPRESS_SECTION_PRESENT")
    # Report only existence of optional buyer guidance. Never log messages
    # that could contain shop-specific private details.
    latest_shop=call("/application/shops/"+shop,headers)
    print("DIGITAL_SALE_MESSAGE_PRESENT:",bool(latest_shop.get("digital_sale_message")))
    # Clean outdated WordPress marketing text only if actually present.
    # Preserve all other, potentially seller-customized customer messages.
    revised={
      "digital_sale_message": (
          "Thanks for choosing RibhLabDigital! Your order is a digital download, "
          "not a physical shipment. Download the purchased ZIP from the Purchases "
          "section of your Etsy account in a web browser. Extract the ZIP and "
          "follow the included README and setup guide. Each software edition "
          "has specific requirements listed in its Etsy description. If you "
          "have trouble accessing or opening the files, message us on Etsy."),
      "sale_message": (
          "Thank you for shopping at RibhLabDigital! Please check the listing's "
          "digital download and setup instructions. Need help with the delivered "
          "files? Send us a message through Etsy."),
    }
    for field in ("digital_sale_message",):
        current=str(latest_shop.get(field) or "")
        if "wordpress" not in current.lower() and "ribhLab viva" not in current.lower():
            print("NO_OLD_WORDPRESS_TEXT_IN_MESSAGE:",field)
            continue
        answer=call("/application/shops/"+shop,headers,"PUT",{field:revised[field]},allow403=True)
        if "_insufficient_shop_scopes" in answer:
            raise ConnectionErrorSafe("Shop message rewrite was not authorized; no other message changes")
        latest_shop=call("/application/shops/"+shop,headers)
        if str(latest_shop.get(field) or "")!=revised[field]:
            raise ConnectionErrorSafe("Etsy did not confirm shop message update for "+field)
        print("OLD_WORDPRESS_MESSAGE_REPLACED:",field)
    print("GENERAL_SALE_MESSAGE_MENTIONS_OLD_BRAND:",any(x in str(latest_shop.get("sale_message") or "").lower() for x in ("wordpress","ribhlab viva")))
    print("GENERAL_SALE_MESSAGE_LEFT_UNCHANGED: requires storefront UI review if old brand remains")


    print("NO_ADS_NO_PAID_RENEWALS_NO_DISCOUNTS_NO_PRICE_CHANGES")

if __name__=="__main__":
    try:main()
    except ConnectionErrorSafe as e:print("SHOP_OPTIMIZE_FAILED:",e,file=sys.stderr);sys.exit(1)
    except Exception as e:print("SHOP_OPTIMIZE_FAILED: unexpected "+type(e).__name__,file=sys.stderr);sys.exit(1)
