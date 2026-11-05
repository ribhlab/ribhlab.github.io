"""Publish ProfitLens Team Server v3.6 to the owner's Etsy shop.

Etsy customer files are never pushed to GitHub or public WordPress media.
The public WordPress transfers are promotional images only. Digital buyer ZIP
must come from a separate GitHub OIDC-verified private Vercel endpoint.
Do not activate if any asset is missing.
"""
import hashlib
import io
import json
import os
import sys
import urllib.parse
import zipfile
import requests
from check_connection import verify, ConnectionErrorSafe

BASE="https://api.etsy.com/v3"
TEAM_TITLE="ProfitLens Team Finance Dashboard, Self-Hosted Profit and Expense Tracker with User Roles"
BUYER_NAME="ProfitLens_v3_6_Team_With_Server.zip"
BUYER_SHA="5575e7567ba0cf4ffc8755fb76fe3963768914f50c7a0a17f00a86aa573f31eb"
PACKAGE_SHA="c19d9e8eee24b2a0640ef8b45d73404796df7062524cd650651497d7d0a38f54"
PACKAGE_URL="https://ribhlab-profitlens-team-v36-transfe.vercel.app/api/package"
OIDC_AUD="ribhlab-profitlens-team-v36-transfer"
ROOT="products/profitlens-team-server-v36/"
IMAGE_BASE="https://ribhlab.wordpress.com/wp-content/uploads/2026/11/ribhlab-profitlens-team-v36-"
ASSETS=[
("01_team_dashboard.jpg","f5ec0532e6dcc79937863e280111e68ca5fcd25c6e081d6a05e2e1ba6a6ee314"),
("02_user_management.jpg","b9c2cbc1cee0cbeebfb11bcda5c4972be40aa6b613e4cb2e142ac6ffa8da848c"),
("03_team_sign_in.jpg","92ca4520ada086922226b19f135af18dcd39c040f4a91bdd4dfc1321ec257fbd"),
("04_working_capital.jpg","9373623d73c8de8d17eea8dbb0288f68444f8be88fdb2e429a706f1278965b21"),
("05_profitability.jpg","61dcd1ac633ec2af6da6ea4d982214070ec8baeea918aa5c3378d112fc7447e9"),
("06_budget_vs_actual.jpg","60bd75ca3854f0c894cef2f31622239ea2629255750e45fe581cf2310cefb21b"),
("07_shared_csv_import.jpg","01fc5ae7e258dfe9367ce54a26dd7bdff7db43e74600f1c25bd153a88eb513e8"),
("08_board_report.jpg","abd778a7565370f4f0419dd1ddb726c6a9978b11c4eba2ad9eae253c4812d4e0"),
("09_team_backups.jpg","be47bcf3e2c07e017c8436c5909a921b5d6c64180a710ffaa015721f7d9ef5ab"),
("10_start_here.jpg","70ff18ebb55e497e2327cd367392e58f8bd8c55e01dabf6ddeff499dfdc6aa64"),
("11_team_promotional_overview.jpg","bfdf35c8ba43dd6ac9ae97ce2ec50b8efc9cf02a8b537d809dec5ec9688a47b6")
]
TAGS=["team finance app","finance dashboard","self hosted app","user roles","gross profit tracker","expense tracker","invoice aging report","receivables tracker","payables tracker","budget vs actual","csv finance tool","board report","sqlite backup"]
DESCRIPTION="""ProfitLens Team 3.6 is a self-hosted finance dashboard for business teams. Run the included Python server in your own environment and give authorized staff individual browser sign-ins to one shared finance workspace. Review sales, margins, operating expenses, overdue invoices and budget variances in one place.

TEAM WORKSPACE

• Assign Admin, Manager, Analyst and Viewer roles. Admin manages accounts, company details and SQLite backups. Admin and Manager can apply shared CSV imports. Analyst and Viewer can view and export.
• Use individual accounts and temporary passwords for staff. Staff set their own passwords at first sign-in.
• Store shared finance data in the server's SQLite database. Export JSON financial data or download a full account database backup as Admin.
• Use English by default; French, Arabic, Spanish, German, Portuguese and Italian are also included, with right-to-left Arabic layout.

FINANCE FEATURES

• Revenue, gross profit, gross margin, operating contribution and outstanding balances.
• Customer and supplier aging in Working Capital, monthly Budget vs Actual.
• Profitability and Expense Control, illustrative decision scenarios, and rule-based priorities.
• CSV import preview, transaction search, row export, board reporting, and printable PDF via browser.

WHAT YOU RECEIVE

One instant digital-download ZIP: Team Python server and HTML dashboard, Windows setup and server launch scripts, Team PDF buyer guide, seven-language quick-start guide, eight blank CSV templates, fictional example files, English/Arabic example reports, plus internal-use licence. All listing screenshots use the actual Team application with fictional demo data.

SETUP AND COMPATIBILITY

Requires Python 3.11+ and a current Chrome or Edge desktop browser. Initial setup downloads Python dependencies. On Windows, extract the ZIP, open TEAM, run SETUP_TEAM_WINDOWS.bat, create an administrator in Admin Center, and run START_TEAM_SERVER.bat. Use http://127.0.0.1:8765 locally. Remote users require self-managed hosting and HTTPS. An advanced Docker/Caddy example is supplied. Setup and local import/backups were checked in Chromium on Linux. Windows launcher tests are documented in the supplied guide.

WORKING WITH YOUR DATA

Supports UTF-8 CSV templates and reconciled source data. Maximum 50,000 rows per table and 9 MiB of combined data via the browser interface. AR/AP represent balance snapshots. Currency is a display label, not a currency converter. Scenario values are illustrative. This is not a cloud SaaS product.

LICENSE AND SUPPORT

One organization may use and customize the software internally for authorized staff. Developed by RibhLab with AI-assisted coding. Contact RibhLabDigital via Etsy messages for order support."""

class PublishError(Exception):
 pass

def require(test,what):
 if not test: raise PublishError(what)

def api(s,method,path,**kwargs):
 try:r=s.request(method,BASE+path,timeout=65,allow_redirects=False,**kwargs)
 except requests.RequestException:raise PublishError("Network issue calling Etsy "+method) from None
 if not r.ok:raise PublishError("Etsy "+method+" rejected with HTTP "+str(r.status_code))
 try:return r.json()
 except ValueError:raise PublishError("Invalid Etsy response") from None

def grant():
 shop=verify()
 key=os.environ["ETSY_KEYSTRING"];secret=os.environ["ETSY_SHARED_SECRET"]
 r=requests.post(BASE+"/public/oauth/token",data={
   "grant_type":"refresh_token","client_id":key,
   "refresh_token":os.environ["ETSY_REFRESH_TOKEN"]},timeout=30)
 require(r.ok,"Etsy refresh failed")
 token=r.json().get("access_token")
 require(token,"Etsy access token unavailable")
 s=requests.Session()
 s.headers.update({"x-api-key":key+":"+secret,"Authorization":"Bearer "+token})
 return s,shop

def find_existing(s,shop):
 found=[]
 base=f"/application/shops/{shop}/listings"
 for state in ("draft","active","inactive"):
  offset=0
  while offset<500:
   q=urllib.parse.urlencode({"state":state,"limit":100,"offset":offset})
   rows=api(s,"GET",base+"?"+q).get("results",[])
   for row in rows:
    title=row.get("title","").strip()
    if title==TEAM_TITLE:found.append(row)
    elif "profitlens" in title.lower() and "team" in title.lower() and ("3.6" in title or "server" in title.lower()):
     raise PublishError("Possible duplicate Team listing with different title; stop.")
   if len(rows)<100:break
   offset+=len(rows)
 require(len(found)<=1,"Multiple Team listings already exist.")
 return found[0] if found else None

def private_bundle():
 url=os.environ["ACTIONS_ID_TOKEN_REQUEST_URL"]
 token=os.environ["ACTIONS_ID_TOKEN_REQUEST_TOKEN"]
 p="&" if "?" in url else "?"
 try:
  resp=requests.get(url+p+"audience="+OIDC_AUD,headers={"Authorization":"Bearer "+token},timeout=20)
  require(resp.ok,"GitHub OIDC token issue")
  jwt=resp.json()["value"]
  response=requests.get(PACKAGE_URL,headers={"Authorization":"Bearer "+jwt},timeout=90)
  require(response.ok,"Private product archive not available (HTTP "+str(response.status_code)+")")
  raw=response.content
  require(hashlib.sha256(raw).hexdigest()==PACKAGE_SHA,"Private product archive hash mismatch")
  bundle=zipfile.ZipFile(io.BytesIO(raw))
  require(bundle.testzip() is None,"Corrupt Team product package")
  manifest=json.loads(bundle.read(ROOT+"listing.json"))
  require(manifest["title"]==TEAM_TITLE and len(manifest["images"])==11,"Wrong Team package")
  filebytes=bundle.read(ROOT+"files/"+BUYER_NAME)
  require(hashlib.sha256(filebytes).hexdigest()==BUYER_SHA,"Buyer ZIP does not match expected SHA")
  return filebytes
 except requests.RequestException:raise PublishError("Secure transfer connection failed.") from None

def main():
 s,shop=grant()
 base=f"/application/shops/{shop}/listings"
 existing=find_existing(s,shop)
 if existing:
  require(existing.get("state") in ("active","draft"),"Existing listing is inactive; manual review needed")
  lid=int(existing["listing_id"]);state=existing["state"]
  print("REUSING_TEAM_LISTING:",lid,"STATE:",state)
 else:
  fields={"quantity":"999","title":TEAM_TITLE,"description":DESCRIPTION,
    "price":"39.95","taxonomy_id":"12476","type":"download",
    "who_made":"i_did","when_made":"2020_2026","is_supply":"false",
    "should_auto_renew":"false","tags":",".join(TAGS)}
  result=api(s,"POST",base,data=fields)
  lid=result.get("listing_id")
  require(lid,"Etsy did not return draft ID")
  state="draft"
  print("CREATED_TEAM_DRAFT_ID:",lid)
 listing_path=f"{base}/{lid}"
 img_path=f"/application/listings/{lid}/images"
 def images():return api(s,"GET",img_path).get("results",[])
 def files():return api(s,"GET",listing_path+"/files").get("results",[])
 current=images()
 require(len(current)<=11,"Unexpected extra Team gallery images")
 ranks={int(x.get("rank",0)) for x in current}
 for rank,(name,expected_hash) in enumerate(ASSETS,1):
  if rank in ranks:
   print("IMAGE_RANK",rank,"EXISTS")
   continue
  try:r=requests.get(IMAGE_BASE+name,timeout=40)
  except requests.RequestException:raise PublishError("Image staging download unavailable for rank "+str(rank)) from None
  require(r.ok and hashlib.sha256(r.content).hexdigest()==expected_hash,"Image "+str(rank)+" checksum invalid")
  api(s,"POST",listing_path+"/images",data={"rank":str(rank)},files={"image":(name,io.BytesIO(r.content),"image/jpeg")})
  print("IMAGE_RANK",rank,"UPLOADED")
 current=images()
 require(len(current)==11 and {int(x.get("rank",0)) for x in current}==set(range(1,12)),"Images incomplete; keeping draft.")
 print("VERIFIED_IMAGES:",len(current))
 expected_files=files()
 if not any(x.get("filename")==BUYER_NAME for x in expected_files):
  try:customer=private_bundle()
  except PublishError as exc:
   print("SECURE_TRANSFER_PENDING:",str(exc))
   print("DRAFT_RETAINS_IMAGES: https://www.etsy.com/listing/"+str(lid))
   raise
  require(len(expected_files)<5,"Etsy digital file slots full")
  api(s,"POST",listing_path+"/files",data={"name":BUYER_NAME},files={"file":(BUYER_NAME,io.BytesIO(customer),"application/zip")})
  print("BUYER_ZIP_UPLOADED")
 else:
  print("BUYER_ZIP_ALREADY_PRESENT")
 filelist=files()
 require(any(x.get("filename")==BUYER_NAME for x in filelist),"Buyer ZIP not verified; keeping draft")
 print("VERIFIED_BUYER_FILES:",len(filelist))
 if state!="active":
  activated=api(s,"PATCH",listing_path,data={"type":"download","state":"active"})
  require(activated.get("state")=="active","Etsy did not confirm active")
  print("CONFIRMED_TEAM_ACTIVE:",lid)
 else:print("ALREADY_ACTIVE:",lid)
 print("PUBLIC_ETSY_URL: https://www.etsy.com/listing/"+str(lid))
 with open(os.environ.get("GITHUB_STEP_SUMMARY","/dev/null"),"a",encoding="utf-8") as h:
  h.write(f"## ProfitLens Team 3.6\n\nListing {lid} **Active**, {len(current)} images and {len(filelist)} buyer attachments.\\n")

if __name__=="__main__":
 try:main()
 except (PublishError,ConnectionErrorSafe,KeyError,ValueError,zipfile.BadZipFile) as e:
  print("TEAM_PUBLISH_INCOMPLETE:",str(e)[:220],file=sys.stderr);sys.exit(1)
 except Exception as e:
  print("TEAM_PUBLISH_INCOMPLETE: Unexpected "+type(e).__name__,file=sys.stderr);sys.exit(1)
