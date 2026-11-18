#!/usr/bin/env python3
"""Create Play graphics from TradingFiew's ORIGINAL logo and REAL rendered UI.

The screenshots come from the public TradingFiew site (same UI served in its
Trusted Web Activity). Never synthesize OHLC prices, alerts or screenshots.
"""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import io
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import cairosvg

def font(size,heavy=False):
    path=("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if heavy
          else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    return ImageFont.truetype(path,size)

def prepare_graphics(source:Path,out:Path):
    icon_svg=source/"tradingfiew-icon.svg"
    if not icon_svg.is_file():raise ValueError("Missing original app logo")
    original=cairosvg.svg2png(url=str(icon_svg),output_width=512,output_height=512)
    icon=Image.open(io.BytesIO(original)).convert("RGBA")
    if icon.size!=(512,512):raise ValueError("Logo size is not 512x512")
    icon.save(out/"icon.png")
    # Feature image: branding based on existing logo, not a fake app screenshot.
    size=(1024,500)
    feature=Image.new("RGB",size)
    pixel=feature.load()
    for y in range(size[1]):
        mix=y/(size[1]-1)
        for x in range(size[0]):
            n=x/(size[0]-1)
            pixel[x,y]=(int(8+7*mix+4*n),int(19+9*mix+5*n),int(34+12*mix+6*n))
    d=ImageDraw.Draw(feature)
    for x in range(0,1024,46):
        d.line((x,0,x,500),fill=(23,48,65),width=1)
    for y in range(0,500,46):
        d.line((0,y,1024,y),fill=(23,48,65),width=1)
    d.rounded_rectangle((42,72,302,332),radius=55,fill=(11,25,49),outline=(51,87,106),width=2)
    icon_240=icon.resize((224,224),Image.Resampling.LANCZOS)
    feature.paste(icon_240,(60,90),icon_240)
    d.text((345,155),"TradingFiew",font=font(66,True),fill=(239,249,255))
    d.text((350,246),"MARKET CHARTS  •  SMC  •  ALERTS",
           font=font(21,True),fill=(68,219,166))
    d.rounded_rectangle((350,308,945,313),radius=2,fill=(61,87,103))
    d.text((350,343),"Interactive charts & educational analysis",
           font=font(23),fill=(178,199,219))
    d.line([(65,420),(140,396),(218,408),(290,370),(352,386),(426,344)],
           fill=(64,219,161),width=7,joint="curve")
    feature.save(out/"feature-1024x500.png",format="PNG",optimize=True)
    assert feature.size==(1024,500)
    return {"icon":str(out/"icon.png"),"feature":str(out/"feature-1024x500.png")}

def screenshots(out:Path):
    from playwright.sync_api import sync_playwright
    site="https://tradingfiew.github.io/"
    errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=["--no-sandbox","--disable-dev-shm-usage"])
        ctx=browser.new_context(
            viewport={"width":360,"height":640},
            device_scale_factor=3,
            is_mobile=True,has_touch=True,
            color_scheme="dark",locale="en-US",
            reduced_motion="reduce",
            user_agent=("Mozilla/5.0 (Linux; Android 14; Pixel 7) "
             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36")
        )
        page=ctx.new_page()
        page.set_default_timeout(25000)
        selected=None
        for symbol,tf in (("USTEC","5m"),("BTCUSDT","15m"),("XAUUSD","1h"),("ETHUSDT","5m")):
            url=f"{site}?symbol={symbol}&tf={tf}&terminal"
            try:
                page.goto(url,wait_until="domcontentloaded",timeout=45000)
                page.wait_for_function(
                    "() => Boolean(window.TradingFiewChartAPI?.getSnapshot?.()?.candleTime) && document.getElementById('chartState')?.classList.contains('hidden')",
                    timeout=30000
                )
                selected={"symbol":symbol,"timeframe":tf,"url":url}
                break
            except Exception as error:
                errors.append({"symbol":symbol,"error":type(error).__name__})
        if not selected:
            browser.close()
            raise RuntimeError("No market delivered real candles for screenshots; refusing to fabricate UI: "+str(errors))
        page.wait_for_timeout(1300)
        saved=[]
        shots=[
            ("01-real-chart.png","chart"),
            ("02-real-market-watch.png","markets"),
            ("03-real-analysis.png","analysis")
        ]
        for name,view in shots:
            selector=f'[data-terminal-view="{view}"]'
            page.locator(selector).first.click(timeout=10000)
            page.wait_for_timeout(1000)
            if page.locator(selector).first.get_attribute("aria-pressed")!="true":
                raise RuntimeError("Mobile UI did not switch to "+view)
            target=out/name
            page.screenshot(path=str(target),full_page=False,animations="disabled")
            with Image.open(target) as image:
                if image.size!=(1080,1920):
                    raise RuntimeError(f"Actual {view} screenshot invalid dimensions: {image.size}")
                rgb=image.convert("RGB")
                if len(set(rgb.resize((32,32)).getdata()))<20:
                    raise RuntimeError("Screenshot appears blank: "+view)
            saved.append(name)
        browser.close()
    return {"source":site,"selectedMarket":selected,
            "screenshots":saved,"capturedAt":datetime.now(timezone.utc).isoformat(),
            "captureMethod":"Real public web application rendered in mobile Chromium; no mocked data",
            "attemptErrors":errors}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    graphics=prepare_graphics(args.source,args.out)
    screens=screenshots(args.out)
    manifest={"graphics":graphics,**screens}
    (args.out/"verification.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print("TRADINGFIEW_REAL_MEDIA_CREATED="+json.dumps(manifest,ensure_ascii=False),flush=True)

if __name__=="__main__":main()
