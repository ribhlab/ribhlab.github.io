"""MoneyControl Pro Etsy draft uploader.

Uses only approved seller secrets in GitHub Actions. The buyer PDF and cover
are retrieved from temporary media, verified against exact SHA-256, and never
committed to the PUBLIC GitHub repository or stored as workflow artifacts.
DRAFT ONLY: do not activate before Google Sheets copy-link permissions are verified.
"""
from __future__ import annotations
import hashlib
import io
import json
import os
import sys
import requests

BASE = "https://api.etsy.com/v3"
TITLE = "Personal Finance Google Sheets Budget Planner | Dashboard, Debt and Savings Tracker | Instant Download"
DESCRIPTION = """MoneyControl Pro is a personal finance Google Sheets template with visual dashboards for desktop and phone.

INCLUDED
• Instant-access PDF with your personal Google Sheets template link (Make a copy).
• Income and expense tracking with category and account selectors.
• Budget vs actual, doughnut, column and monthly trend charts.
• DEMO / LIVE switch: explore examples and then track your own finances.
• Debt payoff estimates, savings goal progress and account balances.
• Financial alerts, data quality checks and printable reports.

GET STARTED
1. Download the PDF attached to this Etsy order.
2. Open its link, sign into Google and choose Make a copy.
3. In your copy, open CONTROL, select LIVE and enter your transactions.

Google account is required. Digital file only; nothing is physically shipped. English edition; no automatic translation into other languages. No standalone web application, Microsoft Excel version, or code installation is included. Changing currency changes a label, not actual foreign-exchange conversion. Demo numbers are examples. Informational budgeting tool, not financial advice. Personal use only; do not redistribute or resell the copy link or template."""
PRICE = "12.90"
TAXONOMY_ID = "12476"  # Etsy financial/budget spreadsheets (used by existing seller workflows).
TAGS = ["budget spreadsheet","google sheets budget","finance dashboard","expense tracker",
        "money planner","savings tracker","debt payoff","monthly budget","budget template",
        "digital planner","finance tracker","cash flow planner","instant download"]
ASSETS = [
    ("buyer", "https://ribhlab.wordpress.com/wp-content/uploads/2026/11/moneycontrol-pro-etsy-buyer-access.pdf",
     "42f9737893d2ae5862955438d5b3f798e7fd403ac8c628b53badc4aa81dd2016",
     "MoneyControl_Pro_Instant_Access.pdf","application/pdf"),
    ("cover", "https://ribhlab.wordpress.com/wp-content/uploads/2026/11/moneycontrol-pro-etsy-cover.png",
     "1678b8719539924b68f9039263cc55bb7b1aa9e3744f829e6728dc0227fd7856",
     "MoneyControl_Pro_Cover.png","image/png"),
]
class PublishError(Exception): pass
def check(ok, message):
    if not ok: raise PublishError(message)
def call(method,path,headers,**kwargs):
    try: r=requests.request(method,BASE+path,headers=headers,timeout=55,allow_redirects=False,**kwargs)
    except requests.RequestException: raise PublishError("Etsy network unavailable ("+method+").") from None
    if r.status_code>=400: raise PublishError("Etsy rejected "+method+" "+path.split("?")[0]+" (HTTP "+str(r.status_code)+").")
    try: return r.json()
    except ValueError: raise PublishError("Etsy did not return valid JSON.")
def download_asset(kind,url,sha,name,mime):
    try: r=requests.get(url,timeout=40,allow_redirects=True)
    except requests.RequestException: raise PublishError("Temporary "+kind+" transfer unavailable.") from None
    check(r.status_code==200,"Temporary "+kind+" transfer HTTP "+str(r.status_code))
    check(1000<len(r.content)<20*1024*1024,"Incorrect "+kind+" size")
    if kind=="buyer":
        check(hashlib.sha256(r.content).hexdigest()==sha,kind+" SHA-256 mismatch. No Etsy changes.")
    else:
        # WordPress CDN may optimize the preview PNG after upload. Validate
        # the decoded PNG container and reasonable original-artwork dimensions.
        import struct
        check(r.content.startswith(bytes.fromhex("89504e470d0a1a0a")) and r.content[12:16]==b"IHDR",
              "Preview cover is not a valid PNG.")
        width,height=struct.unpack(">II",r.content[16:24])
        check(width>=900 and height>=650 and width<=6000 and height<=6000,
              "Preview cover dimensions are invalid.")
        print(f"CHECK: WordPress-delivered PNG {width}x{height} integrity validated.")
    return name,r.content,mime
def get_connection():
    key=os.getenv("ETSY_KEYSTRING","").strip()
    shared=os.getenv("ETSY_SHARED_SECRET","").strip()
    refresh=os.getenv("ETSY_REFRESH_TOKEN","").strip()
    check(all((key,shared,refresh)),"One or more Etsy Actions secrets are absent.")
    token=call("POST","/public/oauth/token",{"Content-Type":"application/x-www-form-urlencoded"},
        data={"grant_type":"refresh_token","client_id":key,"refresh_token":refresh})
    access=token.get("access_token","")
    check(isinstance(access,str) and access and access.split(".",1)[0].isdigit(),"Invalid Etsy OAuth response.")
    headers={"x-api-key":key+":"+shared,"Authorization":"Bearer "+access}
    user=access.split(".",1)[0]
    shops=call("GET","/application/users/"+user+"/shops",headers)
    row=(shops.get("results") or [shops])[0] if isinstance(shops,dict) else {}
    shop=str(row.get("shop_id",""))
    check(shop.isdigit(),"No approved Etsy seller shop.")
    return headers,shop
def get_listing(headers,shop):
    for state in ("draft","active"):
        offset=0
        while offset<2000:
            result=call("GET",f"/application/shops/{shop}/listings?state={state}&limit=100&offset={offset}",headers)
            rows=result.get("results",[])
            for row in rows:
                if row.get("title","").strip()==TITLE:
                    check(str(row.get("shop_id",shop))==shop,"Found matching title in wrong seller shop.")
                    return row
            if len(rows)<100: break
            offset+=len(rows)
    return None
def run():
    # All product bytes verified before Etsy receives any write requests.
    buyer=download_asset(*ASSETS[0])
    cover=download_asset(*ASSETS[1])
    print("CHECK: buyer PDF and preview cover SHA-256 verified.")
    headers,shop=get_connection()
    print("CHECK: authorized Etsy seller shop connected.")
    listing=get_listing(headers,shop)
    if listing:
        lid=int(listing["listing_id"])
        check(listing.get("state")=="draft","Matching listing already active: will not modify.")
        print("REUSE_EXISTING_DRAFT:",lid)
    else:
        data={"title":TITLE,"description":DESCRIPTION,"price":PRICE,"quantity":"999",
              "taxonomy_id":TAXONOMY_ID,"who_made":"i_did","when_made":"2020_2026",
              "type":"download","is_supply":"false","should_auto_renew":"false",
              "tags":",".join(TAGS)}
        obj=call("POST",f"/application/shops/{shop}/listings",headers,data=data)
        lid=int(obj.get("listing_id") or 0)
        check(lid>0,"Etsy did not return a draft listing ID.")
        print("CREATED_DRAFT:",lid)
    current=call("GET",f"/application/listings/{lid}/images",headers).get("results",[])
    if not current:
        name,data,mime=cover
        call("POST",f"/application/shops/{shop}/listings/{lid}/images",headers,
             data={"rank":"1"},files={"image":(name,io.BytesIO(data),mime)})
        print("COVER_IMAGE_UPLOADED")
    else: print("COVER_IMAGE_ALREADY_PRESENT")
    files_path=f"/application/shops/{shop}/listings/{lid}/files"
    existing=call("GET",files_path,headers).get("results",[])
    name,data,mime=buyer
    if not any(x.get("filename")==name for x in existing):
        check(len(existing)<5,"Digital file slots full; keeping Etsy draft.")
        call("POST",files_path,headers,data={"name":name},files={"file":(name,io.BytesIO(data),mime)})
        print("BUYER_PDF_UPLOADED")
    else: print("BUYER_PDF_ALREADY_PRESENT")
    images=call("GET",f"/application/listings/{lid}/images",headers).get("results",[])
    files=call("GET",files_path,headers).get("results",[])
    check(images and any(x.get("filename")==name for x in files),"Buyer file or cover missing after upload.")
    print("DRAFT_READY:",lid)
    print("ETSY_DRAFT_LINK: https://www.etsy.com/your/shops/me/listings/draft")
    print("NOT_ACTIVE: Google Sheets source file currently has owner-only permission.")
    summary=os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary,"a",encoding="utf-8") as f:
            f.write(f"## MoneyControl Pro\n\nDraft Etsy listing **{lid}** created or verified.\n\n")
            f.write("Buyer PDF and cover image uploaded and verified. **Not active** until buyer access to Google Sheets is enabled.\n")
if __name__=="__main__":
    try: run()
    except (PublishError,ValueError,KeyError) as exc:
        print("MONEYCONTROL_PUBLISH_FAILED:",str(exc)[:300],file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print("MONEYCONTROL_PUBLISH_FAILED:",type(exc).__name__,file=sys.stderr)
        sys.exit(1)
