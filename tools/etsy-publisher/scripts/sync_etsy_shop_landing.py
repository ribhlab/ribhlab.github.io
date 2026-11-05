"""Keep the public RibhLabDigital marketing page aligned with *verified ACTIVE* Etsy listings.

This is zero-paid-cost organic promotion. Read-only Etsy operations, no listing edits.
Refuses to publish missing-image/missing-file products or empty API results.
Updates only the English organic shop landing page; GitHub Actions commits changes.
"""
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from check_connection import verify, ConnectionErrorSafe

BASE="https://api.etsy.com/v3"
PAGE=Path("public/en/etsy-shop.html")
CURATED={
  4610734598: {
    "headline":"Self-Hosted Team Finance Dashboard",
    "summary":"ProfitLens Team 3.6 runs from a Python server in your own environment, with browser access for authorized staff. It provides team roles including Admin, Manager, Analyst and Viewer, alongside profitability, invoice aging, expenses and budget reporting. This is a self-hosted product, unlike the offline single-user version.",
    "badges":["SELF-HOSTED","PYTHON SERVER","TEAM ROLES"]
  },
  4610490076: {
    "headline":"Offline HTML Finance Dashboard",
    "summary":"ProfitLens Offline v3.6 is an HTML finance dashboard for desktop browsers. Review profitability, expenses, overdue invoices and KPIs; import CSV and save JSON backups. It is not an Excel workbook or a subscription service.",
    "badges":["HTML", "OFFLINE", "CSV / JSON"]
  },
  4607532475: {
    "headline":"WordPress Magazine & Blog Theme",
    "summary":"RibhLab Viva is a responsive WordPress theme for magazine and news websites with Arabic RTL support. Check the Etsy product page for installation steps, included resources and current compatibility requirements.",
    "badges":["WORDPRESS","ARABIC RTL","RESPONSIVE"]
  }
}

def api(path, headers=None, payload=None):
    url=BASE+path
    req=urllib.request.Request(url,headers=headers or {},data=payload,method="POST" if payload else "GET")
    try:
        with urllib.request.urlopen(req,timeout=35) as r:
            return json.load(r)
    except urllib.error.HTTPError as err:
        raise ConnectionErrorSafe(f"Etsy API error {err.code} during read/refresh.") from None
    except urllib.error.URLError:
        raise ConnectionErrorSafe("Etsy API unreachable.") from None

def text(value,lim=300):
    value=re.sub(r"\s+"," ",str(value or "")).strip()
    return html.escape(value[:lim],quote=True)

def collect(shop,headers):
    active=[]
    offset=0
    while offset<2000:
        query=urllib.parse.urlencode({"state":"active","limit":100,"offset":offset})
        items=api(f"/application/shops/{shop}/listings?{query}",headers).get("results",[])
        for item in items:
            try:
                lid=int(item["listing_id"])
                if str(item.get("shop_id"))!=str(shop):continue
                images=api(f"/application/listings/{lid}/images",headers).get("results",[])
                files=api(f"/application/shops/{shop}/listings/{lid}/files",headers).get("results",[])
            except (ValueError,KeyError,TypeError,ConnectionErrorSafe):
                # Keep the old page rather than advertise an incomplete product.
                print("SKIP_UNVERIFIED",str(item.get("listing_id","unknown")))
                continue
            cover=sorted(images,key=lambda v:v.get("rank",999))
            url=(cover[0].get("url_570xN") or cover[0].get("url_fullxfull")) if cover else ""
            if not url or not url.startswith("https://i.etsystatic.com/") or not files:
                print("SKIP_INCOMPLETE",lid,"IMAGES",len(images),"BUYER_FILES",len(files))
                continue
            active.append({"id":lid,"title":str(item.get("title","")),
                           "description":str(item.get("description","")),
                           "tags":[str(t) for t in (item.get("tags") or [])],
                           "image":url,"created":item.get("created_timestamp") or 0})
        if len(items)<100:break
        offset+=len(items)
    active.sort(key=lambda item:(-int(item["created"] or 0),-item["id"]))
    if not active:
        raise ConnectionErrorSafe("No fully verified ACTIVE Etsy listings. Not editing page.")
    return active

def card(item):
    lid=item["id"]
    src=CURATED.get(lid)
    title=text(src["headline"] if src else item["title"],130)
    badges=(src["badges"] if src else item["tags"][:3]) or ["DIGITAL DOWNLOAD"]
    description=src["summary"] if src else re.sub(r"\s+"," ",item["description"]).strip()[:290]
    description=text(description,330)
    label=" ".join("<span class=\"pill\">"+text(t,26)+"</span>" for t in badges)
    href=f"https://www.etsy.com/listing/{lid}"
    image=text(item["image"],400)
    alt=text(item["title"],140)
    return (
      "<article data-etsy-listing=\""+str(lid)+"\">\n"+
      '<a href="'+href+'" target="_blank" rel="noopener noreferrer">'+
      '<img src="'+image+'" alt="'+alt+'" loading="lazy" width="570" height="380"></a>\n'+
      '<div class="body"><div>'+label+'</div><h3>'+title+'</h3>\n'+
      '<p>'+description+'</p>\n'+
      '<a class="btn" href="'+href+'" target="_blank" rel="noopener noreferrer">Explore on Etsy ↗</a></div>\n'+
      "</article>"
    )

def update_site(items):
    current=PAGE.read_text(encoding="utf-8")
    first='<section class="grid">'
    start=current.find(first)
    end=current.find("</section>",start)
    if start<0 or end<0:raise ConnectionErrorSafe("Shop page card section marker missing.")
    new_cards=first+"\n"+"\n".join(card(item) for item in items)+"\n</section>"
    modified=current[:start]+new_cards+current[end+len("</section>"):]
    ld={"@context":"https://schema.org","@type":"ItemList","name":"RibhLabDigital Digital Products on Etsy",
        "itemListElement":[{"@type":"ListItem","position":i+1,"url":f"https://www.etsy.com/listing/{x['id']}","name":x["title"][:140]} for i,x in enumerate(items)]}
    block='<script type="application/ld+json">'+json.dumps(ld,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')+'</script>'
    modified,count=re.subn(r'<script type="application/ld\+json">.*?</script>',lambda _:block,modified,count=1,flags=re.S)
    if count!=1:raise ConnectionErrorSafe("JSON-LD metadata section missing.")
    if modified!=current:
        PAGE.write_text(modified,encoding="utf-8")
        print("SHOP_PAGE_UPDATED",len(items),"active products")
    else:
        print("SHOP_PAGE_ALREADY_CURRENT",len(items),"active products")
    for item in items:print("PROMOTED",item["id"],item["title"][:130])

def main():
    shop=verify()
    key=os.environ["ETSY_KEYSTRING"]
    shared=os.environ["ETSY_SHARED_SECRET"]
    body=urllib.parse.urlencode({"grant_type":"refresh_token","client_id":key,"refresh_token":os.environ["ETSY_REFRESH_TOKEN"]}).encode()
    access=api("/public/oauth/token",{"Content-Type":"application/x-www-form-urlencoded"},body)["access_token"]
    headers={"x-api-key":key+":"+shared,"Authorization":"Bearer "+access}
    update_site(collect(shop,headers))

if __name__=="__main__":
    try:main()
    except ConnectionErrorSafe as err:
        print("SHOP_SYNC_FAILED:",err,file=sys.stderr);sys.exit(1)
    except Exception as err:
        print("SHOP_SYNC_FAILED: Unexpected "+type(err).__name__,file=sys.stderr);sys.exit(1)
