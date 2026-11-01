"""Create or reuse a DRAFT listing for verified Debt Freedom Pro v3.
No digital buyer files are put into the public repository, and no listing is activated.
"""
import json, os, re, sys, urllib.parse, urllib.request, urllib.error
from check_connection import verify, ConnectionErrorSafe

BASE="https://api.etsy.com/v3"
TITLE="Debt Payoff Spreadsheet for Excel | Snowball vs Avalanche Calculator, Debt Tracker with 9 Live Charts"
DESCRIPTION="""DEBT FREEDOM PRO v3 — A VISUAL, FORMULA-DRIVEN EXCEL DEBT PAYOFF WORKBOOK

Plan a route toward paying off debt using two dynamic strategies and nine native Excel charts. The updated version introduces VISUAL STUDIO — a dedicated chart dashboard with a live debt-share doughnut, creditor balance bars, Snowball vs Avalanche payoff curves, principal-vs-interest columns and total interest-cost comparison.

WHAT YOU DOWNLOAD
• One ZIP digital download, including two .xlsx workbooks: a clean blank version and a fully fictional example.
• Nine translated quick-start guides (EN, AR, FR, ES, DE, PT, IT, RO, ZH). The workbook interface remains in English.
• A quick-start note and a usage licence. No physical item is shipped.

THE EXCEL MODEL
✓ 12 debt account slots: name, opening balance, annual APR and minimum monthly payment
✓ 120-month Snowball (smallest opening balance first) and Avalanche (highest APR first) forecasts
✓ Automatic reallocation of monthly payment capacity as balances reach zero
✓ Monthly interest and principal split, and payoff month/year estimate
✓ Comparison of estimated lifetime interest for both strategies
✓ VISUAL STUDIO: five live charts, strategy selector (Snowball or Avalanche), and 12/24/36/60/120-month display options
✓ DASHBOARD: four KPI groups, forecast line and three more live analytical charts
✓ 200-row separate payment register for actual receipts/payments
✓ No Excel macros or VBA code required

HOW TO USE
1. Download and unzip; open the BLANK .xlsx workbook in desktop Microsoft Excel.
2. Fill the highlighted input cells in CONTROL and DEBTS.
3. Check the results in DASHBOARD and VISUAL STUDIO, including doughnut and bar charts.
4. Compare both strategies. Record real payments separately in PAYMENT LOG.

BEFORE YOU BUY
• This is a Microsoft Excel workbook, NOT a mobile app. Google Sheets, Apple Numbers, and mobile compatibility have not been tested.
• Demo screenshots use fictional names, dates and amounts; the customer workbook starts blank.
• Real lending contracts may calculate daily interest, minimum payments, fees, rate changes and allocation in a different way. This is an illustrative monthly APR/12 model with a fixed total payment budget.
• The model displays up to 120 months; loans that do not amortize within the horizon require a different plan.
• The PAYMENT LOG does not automatically refresh projected starting debt values. Update DEBTS using your latest creditor balances for a new plan.
• The currency field is a display label, not a foreign exchange converter.
• There is no debt consolidation, counseling, credit repair, financial advice, or guaranteed payoff outcome included.
• Buyers may edit and use the files for their own purposes but may not repackage and resell the templates as standalone digital files.
• Please contact RibhLabDigital through Etsy Messages if a supplied file is missing or defective. Applicable consumer rights and Etsy policies apply.

INSTANT DIGITAL DOWNLOAD. NO PHYSICAL SHIPMENT."""
TAGS=["debt payoff tracker","debt snowball","debt avalanche","debt spreadsheet","excel debt planner","budget spreadsheet","payoff calculator","credit card payoff","loan payoff tracker","debt free planner","debt payoff charts","personal finance","money tracker excel"]

def call(path, headers, data=None, method="GET"):
    req=urllib.request.Request(BASE+path,data=data,headers=headers,method=method)
    try:
        with urllib.request.urlopen(req,timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as ex:
        # Do not log sensitive provider responses.
        raise ConnectionErrorSafe("Etsy "+method+" was rejected (HTTP "+str(ex.code)+").") from None
    except urllib.error.URLError:
        raise ConnectionErrorSafe("Cannot reach Etsy API.") from None

def main():
    shop_id=verify()
    key=os.environ["ETSY_KEYSTRING"]
    shared=os.environ["ETSY_SHARED_SECRET"]
    refresh=os.environ["ETSY_REFRESH_TOKEN"]
    payload=call("/public/oauth/token",{"Content-Type":"application/x-www-form-urlencoded"},
        urllib.parse.urlencode({"grant_type":"refresh_token","client_id":key,"refresh_token":refresh}).encode(),"POST")
    token=payload.get("access_token")
    if not token:raise ConnectionErrorSafe("Unable to refresh Etsy access.")
    auth={"Authorization":"Bearer "+token,"x-api-key":key+":"+shared}
    base="/application/shops/"+shop_id+"/listings"
    # Fail closed if the shop list cannot be checked. Avoid duplicate listings.
    for state in ("draft","active"):
        offset=0
        while offset<500:
            d=call(base+"?"+urllib.parse.urlencode({"state":state,"limit":100,"offset":offset}),auth)
            listings=d.get("results") or []
            for row in listings:
                if row.get("title","").strip()==TITLE:
                    lid=row["listing_id"]
                    print("EXISTING_LISTING_ID:",lid,"STATE:",state)
                    print("URL: https://www.etsy.com/listing/"+str(lid))
                    return
            if len(listings)<100:break
            offset+=100
    form={"quantity":"999","title":TITLE,"description":DESCRIPTION,"price":"12.99",
          "who_made":"i_did","when_made":"2020_2026","taxonomy_id":"12476",
          "type":"download","is_supply":"false","should_auto_renew":"false","tags":",".join(TAGS)}
    obj=call(base, {**auth,"Content-Type":"application/x-www-form-urlencoded"},
        urllib.parse.urlencode(form).encode("utf-8"),"POST")
    lid=obj.get("listing_id")
    if not lid:raise ConnectionErrorSafe("Etsy did not return a draft ID.")
    print("CREATED_DRAFT_ID:",lid)
    print("DRAFT ONLY. No images, paid files, or activation yet.")
    print("URL: https://www.etsy.com/listing/"+str(lid))
    with open(os.environ.get("GITHUB_STEP_SUMMARY","/dev/null"),"a",encoding="utf-8") as f:
        f.write("### Etsy Draft — Debt Freedom Pro v3\\n\\n")
        f.write("Created draft #"+str(lid)+". Paid files and images **not** uploaded. Do not activate yet.\\n")

if __name__=="__main__":
    try:main()
    except ConnectionErrorSafe as e:
        print("ERROR:",str(e),file=sys.stderr);sys.exit(1)
    except Exception as e:
        print("ERROR: Unexpected failure ("+type(e).__name__+").",file=sys.stderr);sys.exit(1)
