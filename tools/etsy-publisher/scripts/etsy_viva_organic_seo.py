"""Conservative organic Etsy SEO edits for one verified active seller listing.

No ads, no discounts, no renewals, no inventory changes, no media changes.
Abort on any unexpected listing changes instead of overwriting another editor.
"""
import os
import sys
import re
import urllib.error
import urllib.parse
import urllib.request
import json
from check_connection import verify, ConnectionErrorSafe

BASE="https://api.etsy.com/v3"
TARGET=4607532475
OLD="RibhLab Viva WordPress Magazine Theme | Responsive Blog Design with Arabic RTL"
NEW="WordPress Magazine Theme | Arabic RTL News & Blog Template — RibhLab Viva"
TAGS=[
"wordpress magazine","arabic wordpress","rtl wordpress theme",
"news website theme","blog theme template","wordpress news theme",
"magazine wp theme","responsive wp theme","gutenberg blog theme",
"editorial website","arabic blog theme","digital wp theme",
"wordpress template"
]
PREFIX="RibhLab Viva is a responsive WordPress magazine, news and blog theme with Arabic RTL support. It is a digital theme download, not a hosted website or installation service."

def api(path, headers, method="GET", data=None):
    req=urllib.request.Request(BASE+path,headers=headers,method=method,data=data)
    try:
        with urllib.request.urlopen(req,timeout=35) as response: return json.load(response)
    except urllib.error.HTTPError as exc:
        raise ConnectionErrorSafe(f"Etsy {method} rejected by provider (HTTP {exc.code}).") from None
    except urllib.error.URLError:
        raise ConnectionErrorSafe("Etsy API unreachable.") from None

def verify_item(shop, headers):
    for state in ["active","draft","inactive"]:
        offset=0
        while offset<500:
            q=urllib.parse.urlencode({"state":state,"limit":100,"offset":offset})
            batch=api(f"/application/shops/{shop}/listings?{q}",headers).get("results",[])
            for item in batch:
                if item.get("listing_id")==TARGET:
                    return item
            if len(batch)<100:break
            offset+=len(batch)
    raise ConnectionErrorSafe("RibhLab Viva listing not found.")

def main():
    if len(TAGS)!=13 or any(len(t)>20 for t in TAGS) or len(NEW)>140:
        raise ConnectionErrorSafe("Invalid SEO edits.")
    shop=verify()
    key=os.environ["ETSY_KEYSTRING"];shared=os.environ["ETSY_SHARED_SECRET"]
    refresh=os.environ["ETSY_REFRESH_TOKEN"]
    token=api("/public/oauth/token",{"Content-Type":"application/x-www-form-urlencoded"},"POST",
        urllib.parse.urlencode({"grant_type":"refresh_token","client_id":key,"refresh_token":refresh}).encode())["access_token"]
    headers={"x-api-key":key+":"+shared,"Authorization":"Bearer "+token}
    item=verify_item(shop,headers)
    if str(item.get("shop_id"))!=str(shop) or item.get("state")!="active":
        raise ConnectionErrorSafe("Target listing is not active in connected shop.")
    oldtitle=item.get("title","").strip()
    if oldtitle==NEW:
        print("VIVA_SEO_ALREADY_UPDATED",TARGET)
        return
    if oldtitle!=OLD:
        raise ConnectionErrorSafe("Viva listing title differs from known baseline; refusing to overwrite.")
    desc=item.get("description","")
    if not isinstance(desc,str) or len(desc)<350 or "WordPress" not in desc:
        raise ConnectionErrorSafe("Viva description baseline is missing/changed.")
    if not isinstance(item.get("tags"),list) or len(item["tags"])<8:
        raise ConnectionErrorSafe("Viva tags baseline missing.")
    # Retain the existing detailed product description and disclosures.
    # Replace the stale launch price teaser at the very beginning if present.
    desc=desc.lstrip()
    desc=re.sub(r"^🎉 SPECIAL LAUNCH OFFER — ONLY \$25!\s*Planned regular price after launch: \$29\.\s*","",desc)
    if not desc.startswith(PREFIX):
        desc=PREFIX+"\n\n"+desc
    form=urllib.parse.urlencode({"title":NEW,"description":desc,"tags":",".join(TAGS)}).encode("utf-8")
    updated=api(f"/application/shops/{shop}/listings/{TARGET}",
                {**headers,"Content-Type":"application/x-www-form-urlencoded"},
                "PATCH",form)
    if str(updated.get("listing_id"))!=str(TARGET):
        raise ConnectionErrorSafe("Etsy did not confirm listing ID after update.")
    check=verify_item(shop,headers)
    if check.get("state")!="active" or check.get("title")!=NEW:
        raise ConnectionErrorSafe("Etsy did not confirm Active status and updated title.")
    if len(check.get("tags") or [])!=13:
        raise ConnectionErrorSafe("Updated listing tags did not return expected count.")
    print("SEO_VIVA_UPDATED",TARGET)
    print("NEW_TITLE:",NEW)
    print("TAGS_COUNT:",len(check["tags"]))
    print("DESCRIPTION_FRONT:",str(check.get("description",""))[:170])
    print("STILL_ACTIVE",TARGET)
    print("NO_ADS_OR_PAID_ACTIONS")
    with open(os.environ.get("GITHUB_STEP_SUMMARY","/dev/null"),"a",encoding="utf-8") as f:
        f.write("## RibhLab Viva Organic Etsy SEO\n\n")
        f.write(f"- [Active listing {TARGET}](https://www.etsy.com/listing/{TARGET})\n")
        f.write(f"- **Title:** {NEW}\n- **Tags:** 13 verified\n")
        f.write("- Updated opening description; preserved other product details.\n")
        f.write("- No ads, promotions, price edits, renewals, or new listings.\n")

if __name__=="__main__":
    try:main()
    except ConnectionErrorSafe as err:print("SEO_VIVA_FAILED:",err,file=sys.stderr);sys.exit(1)
    except Exception as err:print("SEO_VIVA_FAILED: unexpected "+type(err).__name__,file=sys.stderr);sys.exit(1)
