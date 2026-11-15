"""Activate ONLY the verified Etsy MoneyControl draft after anonymous buyer access passes.

The Google Sheets CONTROL tab must be anonymously exportable as CSV. This
gate prevents charging a buyer for an inaccessible Make-a-Copy link.
"""
import os
import sys
import requests
from publish_moneycontrol_pro_draft import call,get_connection,get_listing,PublishError,TITLE,check

SHEET_ID="16ugLL1UtQPhXrFiQz1lzOeVL2yQa2Xo_z5nUFS4m7_4"
LISTING_ID=4617919674
PDF_NAME="MoneyControl_Pro_Instant_Access.pdf"
def verify_buyer_access():
    url=f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=120"
    try: r=requests.get(url,timeout=30,allow_redirects=True,
        headers={"User-Agent":"MoneyControl-Buyer-Access-Check/1.0"})
    except requests.RequestException: raise PublishError("Google Sheets access cannot be tested.") from None
    content_type=r.headers.get("Content-Type","").lower()
    body=r.content[:12000].decode("utf-8-sig","ignore").upper()
    check(r.status_code==200 and "csv" in content_type and
          "MONEYCONTROL PRO" in body and "DATA MODE" in body,
          "BLOCKED: source Google Sheet is not anonymously viewable. Change Share > General access to Anyone with the link > Viewer before activating.")
    print("BUYER_ACCESS_VERIFIED: public read-only CSV of the exact CONTROL sheet is accessible.")
def run():
    verify_buyer_access()
    headers,shop=get_connection()
    listing=get_listing(headers,shop)
    check(listing and int(listing.get("listing_id",0))==LISTING_ID,
          "Expected exact Etsy listing not found; refusing activation.")
    state=listing.get("state")
    if state=="active":
        print("ALREADY_ACTIVE:",LISTING_ID)
        print("ETSY_URL: https://www.etsy.com/listing/"+str(LISTING_ID))
        return
    check(state=="draft","Listing is not a draft.")
    images=call("GET",f"/application/listings/{LISTING_ID}/images",headers).get("results",[])
    files=call("GET",f"/application/shops/{shop}/listings/{LISTING_ID}/files",headers).get("results",[])
    check(len(images)>=1,"No preview image. Refuse to activate.")
    check(any(x.get("filename")==PDF_NAME for x in files),"Buyer PDF missing. Refuse to activate.")
    print("CHECK: preview image and buyer PDF exist.")
    x=call("PATCH",f"/application/shops/{shop}/listings/{LISTING_ID}",headers,data={"type":"download","state":"active"})
    if x.get("state")!="active":
        y=get_listing(headers,shop)
        check(y and int(y.get("listing_id",0))==LISTING_ID and y.get("state")=="active",
              "Etsy did not confirm activation.")
    print("ACTIVATED_LIVE:",LISTING_ID)
    print("ETSY_PUBLIC_URL: https://www.etsy.com/listing/"+str(LISTING_ID))
    out=os.environ.get("GITHUB_STEP_SUMMARY")
    if out:
        with open(out,"a",encoding="utf-8") as f:
            f.write("## MoneyControl Pro live publication\n\n")
            f.write("Listing **"+str(LISTING_ID)+"** is ACTIVE; buyer PDF, image and public Sheets access checked.\n")
if __name__=="__main__":
    try:run()
    except PublishError as e:
        print("ACTIVATION_BLOCKED:",str(e)[:350],file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print("ACTIVATION_FAILED:",type(e).__name__,file=sys.stderr)
        sys.exit(1)
