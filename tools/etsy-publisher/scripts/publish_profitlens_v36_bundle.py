"""Idempotent publishing of the real ProfitLens v3.6 2-in-1 digital bundle.

Verify buyer ZIP from authenticated encrypted transfer BEFORE any Etsy write.
Never put buyer assets or credentials in public GitHub. Do not activate a
listing unless both software editions and the cover gallery are confirmed.
"""
import hashlib
import io
import json
import os
import sys
import urllib.parse
import zipfile
from urllib.parse import urlparse

import requests
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from pypdf import PdfReader
from check_connection import verify, ConnectionErrorSafe

API="https://api.etsy.com/v3"
STAGING="https://ribhlab.wordpress.com/wp-content/uploads/2026/11/ribhlab-profitlens-2in1-encrypted-transfer.pdf"
STAGING_SHA="dc9654cffd20437f489e615d2b5218a2a68af8edef905a3d18d0a765c86b77e4"
KEY_API="https://ribhlab-profitlens-bundle-v36-key.vercel.app/api/key"
AUD="ribhlab-profitlens-bundle-v36"
AAD=b"RibhLab-2in1-ProfitLens-v36"
ENCRYPTED_NAME="profitlens-bundle-2in1.enc"
BUYER_NAME="RibhLab_ProfitLens_v36_2in1_Buyer_Bundle.zip"
BUYER_SHA="e1968e03cf2e7707077610b97ff4c0111eeeab909299d166057570a6bd85189d"
HERO="https://ribhlab.wordpress.com/wp-content/uploads/2026/11/profitlens-2in1-bundle-etsy-cover.png"
HERO_SHA="84d24042f38d393c8a7f995b1f651b2253a3f7bfe53193a31da0fc7087998e14"
OFFLINE_SOURCE=4610490076
TEAM_SOURCE=4610734598
TITLE="ProfitLens Finance Dashboard Bundle | Offline HTML + Team Server, Self Hosted Finance App, Small Business Tracker"
TAGS=["finance dashboard","small business app","profit tracker","expense tracker","self hosted app","offline dashboard","team finance app","csv import tool","json backup","finance software","budget vs actual","business reporting","bundle deal"]
DESCRIPTION="""PROFITLENS 3.6 — 2-IN-1 FINANCE DASHBOARD BUNDLE
OFFLINE EDITION + SELF-HOSTED TEAM SERVER

Get both standalone ProfitLens software editions together in one digital bundle.

INDIVIDUAL VALUE: $69.90 when purchased separately.
BUNDLE PRICE: $48.93 (30% off the combined individual prices).

WHAT YOU RECEIVE — INSTANT DIGITAL DOWNLOAD
One ZIP bundle containing TWO separate, fully packaged products:
1) ProfitLens_v3_6_Offline_No_Server.zip
2) ProfitLens_v3_6_Team_With_Server.zip
Plus a READ_ME_FIRST_BUNDLE guide with installation and edition differences.

1. OFFLINE / NO-SERVER EDITION
A browser-based local HTML finance dashboard for individual use. No Excel program, cloud subscription, server, or constant internet connection required. Review business revenue, gross profit and margin, expenses, receivables, supplier payables, budgets, transparent decision scenarios, risk alerts and board-style reports. Import supported CSV data and use JSON backup/export. English default with seven included interface languages.

2. TEAM / SELF-HOSTED SERVER EDITION
A Python-based shared finance dashboard for business teams. Includes user sign-ins, Admin/Manager/Analyst/Viewer roles, organization-level shared data, CSV import management, SQLite storage/backup, reporting and team guides. You are responsible for installing and securely hosting the application.

COMPATIBILITY AND SETUP
• Offline edition: modern desktop browser; unzip and follow the included instructions.
• Team edition: Python 3.11+ and modern Chrome/Edge desktop browser, initial dependency download, and your own server/hosting. Windows setup and launch scripts plus deployment guides are included.
• This bundle is two separate editions. It does not provide automatic syncing between Offline and Team databases.
• This is NOT a pre-hosted SaaS service. There is no recurring cloud service included.
• CSV import requires your properly formatted financial data; the supplied sample values are fictitious. The currency is a display label and is not a currency converter.
• Calculations and decision simulations are illustrative reporting tools, not verified accounting statements, investment recommendations or professional financial advice.
• Product screenshots in the additional gallery images are taken from the supplied software with fictional demo data. The first promotional banner is a designed composite, not a live screenshot.
• Please review the package's included user guides and internal-use license terms before deploying to a live organization.

HOW TO DOWNLOAD
After payment, download the ZIP from Etsy, unzip it, then choose Offline or Team and follow its installation guide. Digital product only — no physical shipment.

SUPPORT
Contact RibhLabDigital through Etsy Messages for problems accessing a purchased file or following the supplied instructions."""
PRICE="48.93"
CATEGORY=12476

class Failed(Exception):
 pass

def require(ok,message):
 if not ok: raise Failed(message)

def checked_get(url, **kwargs):
 try: response=requests.get(url,timeout=55,allow_redirects=False,**kwargs)
 except requests.RequestException: raise Failed("Secure transfer network failed") from None
 require(response.ok, "Secure resource unavailable (HTTP "+str(response.status_code)+")")
 return response

def fetch_archive():
 req_url=os.environ["ACTIONS_ID_TOKEN_REQUEST_URL"]
 secret=os.environ["ACTIONS_ID_TOKEN_REQUEST_TOKEN"]
 joined="&" if "?" in req_url else "?"
 token=checked_get(req_url+joined+"audience="+AUD,headers={"Authorization":"Bearer "+secret},timeout=25).json().get("value")
 require(token and len(token)<18000,"GitHub OIDC grant unavailable")
 endpoint=checked_get(KEY_API,headers={"Authorization":"Bearer "+token},timeout=25)
 keyhex=endpoint.json().get("key","")
 require(len(keyhex)==64,"Secure transfer key invalid")
 key=bytes.fromhex(keyhex)
 encrypted=checked_get(STAGING,timeout=85).content
 require(len(encrypted)<10*1024*1024,"Encrypted archive unexpectedly large")
 require(hashlib.sha256(encrypted).hexdigest()==STAGING_SHA,"Encrypted staging checksum mismatch")
 pdf=PdfReader(io.BytesIO(encrypted))
 part=pdf.attachments.get(ENCRYPTED_NAME)
 require(part is not None,"Encrypted PDF attachment missing")
 sealed=part[0] if isinstance(part,list) else part
 require(sealed[:8]==b"RIBH2IN1","Encrypted transfer prefix invalid")
 raw=AESGCM(key).decrypt(sealed[8:20],sealed[20:],AAD)
 with zipfile.ZipFile(io.BytesIO(raw)) as transport:
  require(transport.testzip() is None,"Encrypted transport ZIP failed CRC")
  manifest=json.loads(transport.read("manifest.json"))
  require(manifest["title"]==TITLE and manifest["price"]==PRICE,"Wrong product manifest")
  customer=transport.read(BUYER_NAME)
  require(hashlib.sha256(customer).hexdigest()==BUYER_SHA,"Buyer bundle checksum mismatch")
  with zipfile.ZipFile(io.BytesIO(customer)) as buyer:
   require(buyer.testzip() is None,"Buyer bundle ZIP failed CRC")
   expected={"ProfitLens_v3_6_Offline_No_Server.zip","ProfitLens_v3_6_Team_With_Server.zip"}
   require(expected.issubset(set(buyer.namelist())),"Missing one of the two buyer software editions")
   for name in expected:
    with zipfile.ZipFile(io.BytesIO(buyer.read(name))) as inner:
     require(inner.testzip() is None,"Corrupt nested edition ZIP: "+name)
  require(len(customer)<20*1024*1024,"Etsy buyer ZIP too large")
 print("PASS: Verified AES-GCM secure transfer, both buyer edition ZIPs, and hashes.")
 return customer

def etsy(session,method,path,**kwargs):
 try:res=session.request(method,API+path,timeout=70,allow_redirects=False,**kwargs)
 except requests.RequestException: raise Failed("Etsy network failure on "+method) from None
 if not res.ok:raise Failed("Etsy "+method+" rejected with HTTP "+str(res.status_code)+" on "+path.split("?")[0])
 try:return res.json()
 except ValueError:raise Failed("Unexpected Etsy response") from None

def authorized():
 shop=verify()
 key=os.environ["ETSY_KEYSTRING"];shared=os.environ["ETSY_SHARED_SECRET"]
 token_req=requests.post(API+"/public/oauth/token",timeout=30,data={
  "grant_type":"refresh_token","client_id":key,"refresh_token":os.environ["ETSY_REFRESH_TOKEN"]})
 require(token_req.ok,"Etsy OAuth token refresh rejected")
 token=token_req.json().get("access_token")
 require(bool(token),"Etsy access token missing")
 s=requests.Session()
 s.headers.update({"x-api-key":key+":"+shared,"Authorization":"Bearer "+token})
 return s,shop

def matching_listing(s,shop):
 base=f"/application/shops/{shop}/listings"
 matches=[]
 for status in ("draft","active","inactive"):
  offset=0
  while offset<500:
   rows=etsy(s,"GET",base+"?"+urllib.parse.urlencode({"state":status,"limit":100,"offset":offset})).get("results",[])
   for item in rows:
    title=item.get("title","").strip()
    if title==TITLE:matches.append(item)
    elif "profitlens" in title.lower() and ("bundle" in title.lower() or "2-in-1" in title.lower()):
     raise Failed("Possible ProfitLens bundle listing with different title: duplicate safety stop")
   if len(rows)<100:break
   offset+=len(rows)
 require(len(matches)<=1,"Multiple bundle drafts found; refusing to duplicate")
 return matches[0] if matches else None

def image_bytes(url, sha=None):
 u=urlparse(url)
 require(u.scheme=="https" and (u.hostname=="ribhlab.wordpress.com" or
             u.hostname=="i.etsystatic.com" or (u.hostname and u.hostname.endswith(".etsystatic.com"))),
         "Unapproved image source")
 try:r=requests.get(url,timeout=45,allow_redirects=False)
 except requests.RequestException:raise Failed("Cannot download a listing preview") from None
 require(r.ok and 1024<len(r.content)<9*1024*1024,"Listing image missing or oversized")
 if sha:require(hashlib.sha256(r.content).hexdigest()==sha,"Promotional hero image hash mismatch")
 return r.content

def run():
 buyer=fetch_archive()
 sess,shop=authorized()
 base=f"/application/shops/{shop}/listings"
 existing=matching_listing(sess,shop)
 if existing:
  require(existing.get("state") in ("draft","active"),"Existing bundle not editable")
  lid=int(existing["listing_id"])
  state=existing["state"]
  print("REUSING_BUNDLE_LISTING:",lid,"STATE:",state)
 else:
  fields={"quantity":"999","title":TITLE,"description":DESCRIPTION,
    "price":PRICE,"taxonomy_id":str(CATEGORY),"type":"download",
    "who_made":"i_did","when_made":"2020_2026","is_supply":"false",
    "should_auto_renew":"false","tags":",".join(TAGS)}
  item=etsy(sess,"POST",base,data=fields)
  lid=int(item["listing_id"]);state="draft"
  print("CREATED_BUNDLE_DRAFT:",lid)
 path=base+"/"+str(lid)
 img_path=f"/application/listings/{lid}/images"
 def images():return etsy(sess,"GET",img_path).get("results",[])
 def files():return etsy(sess,"GET",path+"/files").get("results",[])
 buyerfiles=files()
 if not any(row.get("filename")==BUYER_NAME for row in buyerfiles):
  require(len(buyerfiles)<5,"Etsy digital file slots full")
  etsy(sess,"POST",path+"/files",data={"name":BUYER_NAME},
      files={"file":(BUYER_NAME,io.BytesIO(buyer),"application/zip")})
  print("UPLOADED_BUYER_BUNDLE")
 buyerfiles=files()
 require(any(row.get("filename")==BUYER_NAME for row in buyerfiles),"Buyer ZIP not verified in Etsy")
 print("BUYER_ZIP_VERIFIED:",len(buyerfiles))
 # Obtain exactly three real software previews from each previously published product.
 support=[]
 for source_id,prefer in [(OFFLINE_SOURCE,[2,3,4]),(TEAM_SOURCE,[1,2,3])]:
  arr=etsy(sess,"GET",f"/application/listings/{source_id}/images").get("results",[])
  ranks={int(row.get("rank",0)):row for row in arr}
  for rank in prefer:
   require(rank in ranks,"Missing real product screenshot rank "+str(rank))
   url=ranks[rank].get("url_fullxfull") or ranks[rank].get("url_570xN")
   require(url and url.startswith("https://"),"Invalid original screenshot URL")
   support.append(url)
 require(len(support)==6,"Supporting screenshot list incomplete")
 original=images()
 require(len(original)<=7,"Unexpected existing bundle gallery")
 # First marketing graphic is the user-approved first image, followed by real product screenshots.
 source=[("bundle-hero.png",HERO,"image/png",HERO_SHA)]+[
  ("source-%d.jpg"%idx,url,"image/jpeg",None) for idx,url in enumerate(support,2)]
 existing_ranks={int(i.get("rank",0)) for i in original}
 for rank,(filename,url,typ,sha) in enumerate(source,1):
  if rank in existing_ranks:
   print("IMAGE_RANK",rank,"PRESENT")
   continue
  data=image_bytes(url,sha)
  item=etsy(sess,"POST",path+"/images",data={"rank":str(rank)},
            files={"image":(filename,io.BytesIO(data),typ)})
  require(item.get("listing_image_id"),"Etsy upload returned no image ID")
  print("IMAGE_RANK",rank,"UPLOADED")
 current=images()
 ranks={int(i.get("rank",0)) for i in current}
 require(len(current)==7 and ranks==set(range(1,8)),"Gallery incomplete: draft retained")
 buyerfiles=files()
 require(any(row.get("filename")==BUYER_NAME for row in buyerfiles),"Buyer ZIP missing after gallery upload")
 if state!="active":
  status=etsy(sess,"PATCH",path,data={"type":"download","state":"active"})
  require(status.get("state")=="active","Etsy did not confirm live bundle")
  print("CONFIRMED_BUNDLE_ACTIVE:",lid)
 else:print("ALREADY_ACTIVE:",lid)
 print("PUBLIC_ETSY_URL: https://www.etsy.com/listing/"+str(lid))
 print("VERIFIED_IMAGES:",len(current),"VERIFIED_BUYER_FILES:",len(buyerfiles))
 with open(os.environ.get("GITHUB_STEP_SUMMARY","/dev/null"),"a",encoding="utf8") as f:
  f.write(f"### ProfitLens 2-in-1 Bundle\n\nListing **{lid}** Active, price **{PRICE}**, 7 images, buyer ZIP **{BUYER_NAME}**.\n")

if __name__=="__main__":
 try: run()
 except (Failed,ConnectionErrorSafe,zipfile.BadZipFile,ValueError,KeyError) as e:
  print("BUNDLE_PUBLISH_INCOMPLETE:",str(e)[:280],file=sys.stderr);sys.exit(1)
 except Exception as e:
  print("BUNDLE_PUBLISH_INCOMPLETE: unexpected "+type(e).__name__,file=sys.stderr);sys.exit(1)
