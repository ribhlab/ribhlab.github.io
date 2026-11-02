"""Create or locate a single CashFlow Command Center Pro v2.2 Etsy draft.
Safety: never activate without image and buyer ZIP uploads; no paid assets in public Git.
"""
import os, sys, json, urllib.parse, urllib.request, urllib.error
from check_connection import verify, ConnectionErrorSafe
BASE = "https://api.etsy.com/v3"
TITLE = "13 Week Cash Flow Excel Template | CFO Cockpit, Cash Risk Alerts, AR AP, Scenario & Decision Dashboard"
DESCRIPTION = """RIBHLAB CASHFLOW COMMAND CENTER PRO 2.2 — PROFESSIONAL EXCEL LIQUIDITY PLANNER

Understand when your small business may run short of cash — and what trade-offs could improve its situation. Two edit-ready Microsoft Excel (.xlsx) workbooks (blank + fully fictional demo), 13 worksheets, 10 real Excel chart objects, and an optional VBA code module for users who want to add PDF export and navigation in their own copy.

WHAT'S INCLUDED
• CFO COCKPIT: premium KPI dashboard with opening liquidity, week-13 balance, minimum cash position, live warning ribbon, scenario comparison, weekly cash risk heatmap and 13-week cash charts.
• DECISION LAB: independently linked what-if simulator. Explore illustrative changes in AR collection, payment reductions, and a one-time future receipt; simulate week-by-week closing cash without modifying underlying invoice inputs.
• DATA QUALITY: formula checks for duplicate IDs, receipts exceeding invoices, unusual amounts, over-buffer issues and forecast reconciliation.
• 13-WEEK FORECAST: weekly cash inflows/outflows, closing position, minimum buffer, risk levels and stress outcomes.
• AR PIPELINE / AP PIPELINE: expected collections and supplier payment schedules with status and outstanding amount tracking.
• OTHER FLOWS, ACTUALS, VARIANCE, SETTINGS, original DASHBOARD and DATA CHARTS.
• OPTIONAL VBA source as a .BAS file for users who want to import navigation/one-click PDF export into an .xlsm copy. The .xlsx is completely usable without VBA. The macros are not pre-installed and were not desktop-tested in this environment.

HOW IT WORKS
1. Download and unzip. Open the BLANK workbook in Microsoft Excel desktop.
2. Set your forecast start date, cash balance, minimum buffer, currency label and scenario.
3. Enter only FUTURE/unsettled expected AR, AP and operating flows in the provided input tables.
4. Review CFO COCKPIT and experiment in DECISION LAB. Use ACTUALS and VARIANCE for independent reporting only.

BEFORE BUYING
• This is a financial planning tool, NOT a bank data integration, an automatic accounting system, an AI prediction engine or a guarantee of future cash balances. No live data connections or real customer accounts.
• Scenario stress and what-if assumptions are deterministic. Actual cash and dates must be independently reconciled.
• Currency is a label; there is no FX converter.
• Windows/Mac Microsoft Excel desktop recommended. Google Sheets, Apple Numbers and mobile operation not verified.
• Only .xlsx templates are ready out of the ZIP. To use optional VBA source, you must manually import into a trusted .xlsm copy. No macros are needed for calculation.
• All screenshots use entirely fictional data. Product screenshots show actual Excel workbook outputs, not a separate app.
• Digital product only, no physical shipment. For your own/internal business use, no redistribution as a competing product. Contact us through Etsy Messages with file problems.

AI-assisted workbook development, original RibhLab template and artwork.

VERSION 2.2 QA NOTE: The what-if collection improvement now respects invoice outstanding balances, the demo transaction types have been reconciled with money directions, and the workbook includes duplicate-ID and additional data-quality checks. Excel Desktop and optional VBA automation have not been physically tested; VBA is optional and shipped as a separate .bas source module, not built into the .xlsx file.

VERSION 2.2 REGRESSION NOTE: Comparisons remain calculable even if an active scenario collection or expense factor is set to zero (preventing prior division-by-zero chart issues). Native Excel and optional VBA still require desktop verification."""
TAGS=["13 week cash flow","cash flow forecast","excel cash flow","cashflow dashboard","finance spreadsheet","cfo dashboard","liquidity planner","business finance","weekly cashflow","ar ap tracker","cash flow template","cash flow excel","financial planner"]
def send(path,headers,data=None,method="GET"):
    try:
        req=urllib.request.Request(BASE+path,headers=headers,data=data,method=method)
        with urllib.request.urlopen(req,timeout=35) as r: return json.load(r)
    except urllib.error.HTTPError as exc: raise ConnectionErrorSafe(f"Etsy {method} request failed (HTTP {exc.code}).") from None
    except urllib.error.URLError: raise ConnectionErrorSafe("Etsy API is unreachable.") from None
def main():
    shop=verify()
    key=os.environ["ETSY_KEYSTRING"];secret=os.environ["ETSY_SHARED_SECRET"]
    token=send("/public/oauth/token",{"Content-Type":"application/x-www-form-urlencoded"},urllib.parse.urlencode({"grant_type":"refresh_token","client_id":key,"refresh_token":os.environ["ETSY_REFRESH_TOKEN"]}).encode(),"POST")["access_token"]
    headers={"x-api-key":key+":"+secret,"Authorization":"Bearer "+token}
    base=f"/application/shops/{shop}/listings"
    for state in ("draft","active","inactive"):
        offset=0
        while offset<500:
            data=send(base+"?"+urllib.parse.urlencode({"state":state,"limit":100,"offset":offset}),headers)
            rows=data.get("results") or []
            for item in rows:
                if item.get("title","").strip()==TITLE:
                    print("EXISTING_CASHFLOW_LISTING_ID:",item["listing_id"],"STATE:",state)
                    print("DO NOT CREATE ANOTHER DRAFT.")
                    return
            if len(rows)<100: break
            offset+=len(rows)
    fields={"title":TITLE,"description":DESCRIPTION,"price":"19.95","quantity":"999","taxonomy_id":"12476","who_made":"i_did","when_made":"2020_2026","type":"download","is_supply":"false","should_auto_renew":"false","tags":",".join(TAGS)}
    result=send(base,{**headers,"Content-Type":"application/x-www-form-urlencoded"},urllib.parse.urlencode(fields).encode(),"POST")
    lid=result.get("listing_id")
    if not lid:raise ConnectionErrorSafe("Etsy draft response omitted listing_id.")
    print("CREATED_CASHFLOW_DRAFT_ID:",lid)
    print("DRAFT ONLY. Images and paid buyer file NOT uploaded. Not live.")
    with open(os.environ.get("GITHUB_STEP_SUMMARY","/dev/null"),"a",encoding="utf-8") as w:
        w.write(f"### CashFlow Command Center Pro v2.2 — Draft {lid}\n\nImages and digital buyer ZIP have NOT been uploaded, so the listing is not live.\n")
if __name__=="__main__":
    try:main()
    except ConnectionErrorSafe as e: print("ERROR:",e,file=sys.stderr);sys.exit(1)
    except Exception as e: print("ERROR: Unexpected problem: "+type(e).__name__,file=sys.stderr);sys.exit(1)
