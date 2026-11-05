"""Replace the seven Etsy photos of ONE existing ProfitLens 2-in-1 bundle listing.

- Verifies shop, listing ACTIVE, price and the actual digital buyer ZIP.
- Validates staged marketing PNG byte-by-byte by known SHA-256 before ANY edits.
- Uses Etsy's documented 'overwrite=true' at ranks 7 down to 1, never creates listings.
- Checks final seven photos' alt text/rank and leaves buyer ZIP intact.
- Keeps all credentials in existing GitHub Actions secrets; no private assets in repo.
"""
import hashlib
import io
import os
import sys
import urllib.parse
import time
import requests
from check_connection import verify, ConnectionErrorSafe

API="https://api.etsy.com/v3"
LID=4610758074
BUYER="RibhLab_ProfitLens_v36_2in1_Buyer_Bundle.zip"
PREFIX="https://ribhlab.wordpress.com/wp-content/uploads/2026/11/"
PRODUCT_IMAGES=[
 ("etsy-profitlens-bundle-1-profitlens_finance_dashboard_bundle.png",
  "84d24042f38d393c8a7f995b1f651b2253a3f7bfe53193a31da0fc7087998e14",
  "ProfitLens bundle: Offline HTML finance dashboard plus self-hosted Team Server edition, promotional graphic."),
 ("etsy-profitlens-bundle-2-choose_your_profitlens_edition.png",
  "5d1e74d019d7817f9f4e158bdd365cce4167cf06e47c40e924ded1ac25303c72",
  "Comparison: ProfitLens Offline single-user local dashboard and Team Server shared finance workspace."),
 ("etsy-profitlens-bundle-3-offline_finance_dashboard_edition.png",
  "de8d0dd98ff3e97fcd150de61a0ceaf39bf48df0c013000a550b59b0fcaa7f44",
  "ProfitLens Offline HTML dashboard for individual analysis, CSV imports and JSON backups."),
 ("etsy-profitlens-bundle-4-neon_team_server_finance_suite.png",
  "04077f3f51eba7cfe9c895f0ee0c062182147f1a7980c07e786b1042812a8292",
  "ProfitLens self-hosted Team Server edition with roles, sign-in and shared reporting."),
 ("etsy-profitlens-bundle-5-what_s_inside_the_2_in_1_bundle.png",
  "4e52b42308aa5e097a1ce674a6d369273e6afbc07574d917d0d63a5bed8c4964",
  "Contents of the two-edition ProfitLens software bundle: Offline ZIP and Team Server ZIP."),
 ("etsy-profitlens-bundle-6-finance_dashboard_bundle_editions.png",
  "f924bd1c144c58be0966006b108744469ed67ceb60f87df8b525e746c4ef05ec",
  "Choose ProfitLens Offline for solo work or self-hosted Team Server for shared workflows."),
 ("etsy-profitlens-bundle-7-profitlens_onboarding_guide.png",
  "e2619c1b34c635103529cc5a890d3d4208745670166995058d284f6f79d11d31",
  "ProfitLens setup overview: local browser HTML or separately installed self-hosted Python Team Server.")
]
MARKER="ProfitLens 2-in-1 bundle marketing graphic"
DISCLAIMER=("IMAGES: The promotional gallery contains designed composite graphics based on the included "
            "ProfitLens Offline and Team Server editions. The interface previews and example financial "
            "amounts are illustrative and use fictional demo data; layout details may differ in your installed software.\n\n")
class PublishError(Exception):pass
def must(check,why):
 if not check:raise PublishError(why)
def request(session,method,path,**kw):
 try:r=session.request(method,API+path,timeout=80,allow_redirects=False,**kw)
 except requests.RequestException:raise PublishError("Etsy API connection issue") from None
 must(r.ok, f"Etsy {method} returned HTTP {r.status_code} for {path.split('?')[0]}")
 try:return r.json()
 except ValueError:raise PublishError("Unexpected Etsy JSON response") from None
def verified_session():
 shop=verify()
 key=os.environ["ETSY_KEYSTRING"]
 secret=os.environ["ETSY_SHARED_SECRET"]
 refresh=os.environ["ETSY_REFRESH_TOKEN"]
 try:r=requests.post(API+"/public/oauth/token",timeout=35,data={
    "grant_type":"refresh_token","client_id":key,"refresh_token":refresh})
 except requests.RequestException:raise PublishError("Etsy OAuth connection issue") from None
 must(r.ok,"Etsy refresh rejected")
 token=r.json().get("access_token")
 must(token,"No Etsy access token")
 sess=requests.Session()
 sess.headers.update({"Authorization":"Bearer "+token,"x-api-key":key+":"+secret})
 return sess,shop
def listing(session,shop):
 base=f"/application/shops/{shop}/listings"
 for state in ("active","draft"):
  offset=0
  while offset<500:
   q=urllib.parse.urlencode({"state":state,"limit":100,"offset":offset})
   rows=request(session,"GET",base+"?"+q).get("results",[])
   for item in rows:
    if int(item.get("listing_id",0))==LID:
     must(str(item.get("shop_id"))==str(shop),"Listing shop mismatch")
     must(item.get("state")=="active","Listing not active; refusing to edit")
     title=str(item.get("title","")).lower()
     must(("profitlens" in title or "finance dashboard" in title) and "bundle" in title,
       "Listing title mismatch, refusing to edit")
     price=item.get("price") or {}
     must(price.get("amount")==4893 and price.get("divisor")==100 and price.get("currency_code")=="USD",
          "Listing price changed from 48.93 USD")
     return item
   if len(rows)<100:break
   offset+=len(rows)
 raise PublishError("Target listing absent from connected Etsy shop")
def download_images():
 cache=[]
 for number,(filename,expected,alt) in enumerate(PRODUCT_IMAGES,1):
  url=PREFIX+filename
  try:r=requests.get(url,timeout=45,allow_redirects=False)
  except requests.RequestException:raise PublishError(f"Staging photo {number} inaccessible") from None
  must(r.ok,f"Staging photo {number} HTTP {r.status_code}")
  img=r.content
  must(50_000<len(img)<6_000_000,f"Staging photo {number} has invalid length")
  must(img[:8]==b"\x89PNG\r\n\x1a\n",f"Staging photo {number} is not PNG")
  must(hashlib.sha256(img).hexdigest()==expected,f"Staging photo {number} hash mismatch")
  cache.append((filename,img,alt))
  print("PHOTO_STAGING_VERIFIED:",number,len(img))
 return cache
def image_list(sess):
 return request(sess,"GET",f"/application/listings/{LID}/images").get("results",[])
def buyer_list(sess,shop):
 return request(sess,"GET",f"/application/shops/{shop}/listings/{LID}/files").get("results",[])
def main():
 # Download and verify every marketing photo BEFORE Etsy writes.
 pics=download_images()
 sess,shop=verified_session()
 item=listing(sess,shop)
 buyers=buyer_list(sess,shop)
 must(len(buyers)>=1 and any(x.get("filename")==BUYER for x in buyers),
      "Digital 2-in-1 buyer ZIP is missing; no image modification")
 current=image_list(sess)
 must(len(current)==7 and {int(x.get("rank",0)) for x in current}==set(range(1,8)),
      f"Expected exactly 7 original gallery images, found {len(current)}; no changes")
 # If exactly the new gallery is already present, do not re-upload.
 already=all(any(int(x.get("rank",0))==i and alt in str(x.get("alt_text",""))
     for x in current) for i,(_,_,alt) in enumerate(pics,1))
 if already:
  print("GALLERY_ALREADY_UPDATED")
 else:
  # 'overwrite=true' replaces the image AT rank; prevents accidental duplicate photos.
  for i in range(7,0,-1):
   filename,img,alt=pics[i-1]
   uploaded=request(sess,"POST",f"/application/shops/{shop}/listings/{LID}/images",
      data={"rank":str(i),"overwrite":"true","alt_text":alt},
      files={"image":(filename,io.BytesIO(img),"image/png")})
   must(uploaded.get("listing_image_id"),f"Upload at rank {i} returned no image ID")
   print("REPLACED_IMAGE_RANK:",i,"ID:",uploaded["listing_image_id"])
  for n in range(8):
   actual=image_list(sess)
   if (len(actual)==7 and all(any(int(x.get("rank",0))==i and alt in str(x.get("alt_text",""))
       for x in actual) for i,(_,_,alt) in enumerate(pics,1))):
    break
   if n==7:raise PublishError("Etsy image upload completed but rank/alt verification pending; inspect listing")
   time.sleep(3)
 final=image_list(sess)
 must(len(final)==7,"Unexpected final gallery size")
 must(all(any(int(x.get("rank",0))==i and alt in str(x.get("alt_text",""))
     for x in final) for i,(_,_,alt) in enumerate(pics,1)),
     "Photo rank/alt verification failed")
 # Existing description said additional images were true screenshots. They are now composites;
 # add a precise disclosure but leave title, price, buyer files and status untouched.
 listing_now=listing(sess,shop)
 desc=str(listing_now.get("description") or "")
 if not desc.startswith("IMAGES: The promotional gallery"):
  modified=request(sess,"PATCH",f"/application/shops/{shop}/listings/{LID}",
     data={"description":DISCLAIMER+desc})
  must(int(modified.get("listing_id",0))==LID,"Description disclosure update not confirmed")
  print("PROMOTIONAL_COMPOSITE_DISCLOSURE_ADDED")
 buyer_after=buyer_list(sess,shop)
 must(any(x.get("filename")==BUYER for x in buyer_after),"Buyer ZIP disappeared after gallery update")
 confirmed=listing(sess,shop)
 print("SUCCESS: BUNDLE_IMAGES_ALL_VERIFIED 7")
 print("SUCCESS: FIRST_RANK_PROFITLENS_BUNDLE_COVER")
 print("SUCCESS: BUYER_ZIP_PRESENT",len(buyer_after))
 print("SUCCESS: LISTING_ACTIVE PRICE_48_93_USD",LID)
 print("PUBLIC_ETSY_URL: https://www.etsy.com/listing/"+str(LID))
 with open(os.environ.get("GITHUB_STEP_SUMMARY","/dev/null"),"a",encoding="utf-8") as f:
  f.write(f"### ProfitLens 2-in-1 Etsy photo refresh\n\nListing **{LID}** Active. "
          "Seven approved marketing images verified in new order; first image is 2-in-1 cover. "
          "Buyer ZIP retained, price unchanged ($48.93). Transparent promotional-graphic disclosure added.\n")
if __name__=="__main__":
 try:main()
 except (PublishError,ConnectionErrorSafe,KeyError,ValueError) as e:
  print("BUNDLE_PHOTOS_UPDATE_FAILED:",str(e)[:260],file=sys.stderr);sys.exit(1)
 except Exception as e:
  print("BUNDLE_PHOTOS_UPDATE_FAILED: unexpected "+type(e).__name__,file=sys.stderr);sys.exit(1)
