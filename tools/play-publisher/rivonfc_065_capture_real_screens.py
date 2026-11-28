#!/usr/bin/env python3
"""Only genuine Google Play upload-key-signed RivoNFC 0.6.5 app screenshots.

Uses adb and Android 35; no Photoshop, compositing, fictional NFC tags, or
synthetic in-app content. Disconnect before launch to avoid real ad impressions.
Captures Scan, Write, Tools and History from installed signed code12 APK.
"""
from __future__ import annotations
import hashlib
import json
import re
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path

PACKAGE="com.ribhlab.rivonfc"
OUT=Path("rivonfc-code12-store")
APK=Path("signed/RivoNFC-0.6.5-RivoScan-SIGNED.apk")
SCREENS=(
    ("01-scan", "RivoNFC", None),
    ("02-write", "Create & write", "Write"),
    ("03-tools", "Tag tools", "Tools"),
    ("04-history", "Activity", "History"),
)

def adb(*args,binary=False,check=True):
    result=subprocess.run(["adb",*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                          timeout=90,check=False)
    if check and result.returncode:
        raise RuntimeError("adb "+ " ".join(args) + " failed: "+
                           result.stderr.decode(errors="replace")[-280:])
    return result.stdout if binary else result.stdout.decode(errors="replace")

def dump(name):
    for attempt in range(9):
        adb("shell","rm","-f","/sdcard/rivonfc-real.xml",check=False)
        adb("shell","uiautomator","dump","/sdcard/rivonfc-real.xml",check=False)
        raw=adb("exec-out","cat","/sdcard/rivonfc-real.xml",binary=True,check=False)
        start=raw.find(b"<?xml")
        if start>=0 and b"<hierarchy" in raw[start:]:
            try:
                root=ET.fromstring(raw[start:])
                nodes=list(root.iter("node"))
                if len(nodes)>=12:
                    (OUT/(name+".xml")).write_bytes(raw[start:])
                    return nodes
            except ET.ParseError:pass
        time.sleep(3)
    raise RuntimeError("Actual Android UI hierarchy is unavailable for "+name)

def text(nodes):
    return " ".join(n.attrib.get("text","")+" "+n.attrib.get("content-desc","")
                    for n in nodes)

def press_tab(nodes,label):
    matching=[]
    for n in nodes:
        val=(n.attrib.get("text","")+" "+
             n.attrib.get("content-desc","")).strip()
        if label.casefold()!=val.casefold():continue
        b=list(map(int,re.findall(r"\d+",n.attrib.get("bounds",""))))
        if len(b)==4 and b[2]>b[0] and b[3]>b[1]:
            matching.append((b[1],(b[0]+b[2])//2,(b[1]+b[3])//2))
    if not matching:raise RuntimeError("Real bottom navigation tab missing: "+label)
    _,x,y=max(matching) # Use bottom navigation if a home CTA has same label.
    adb("shell","input","tap",str(x),str(y))
    time.sleep(3)

def capture(name,nodes):
    raw=adb("exec-out","screencap","-p",binary=True)
    if not raw.startswith(b"\x89PNG\r\n\x1a\n") or len(raw)<16_000:
        raise RuntimeError("Invalid real PNG screenshot "+name)
    size=(int.from_bytes(raw[16:20],"big"),int.from_bytes(raw[20:24],"big"))
    if size!=(1080,1920):
        raise RuntimeError("Screen size not 1080x1920: "+str(size))
    path=OUT/(name+".png")
    path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()

def main():
    if not APK.is_file() or APK.stat().st_size<10_000_000:
        raise RuntimeError("Exact code12 original-key signed APK missing")
    OUT.mkdir(parents=True,exist_ok=True)
    adb("wait-for-device")
    adb("shell","wm","size","1080x1920")
    adb("shell","wm","density","480")
    # Prevent live account AdMob impressions during automated Play screenshot QA.
    adb("shell","svc","wifi","disable",check=False)
    adb("shell","svc","data","disable",check=False)
    adb("install","-r",str(APK.resolve()))
    details=adb("shell","dumpsys","package",PACKAGE)
    if "versionCode=12" not in details or "versionName=0.6.5" not in details:
        raise RuntimeError("Installed binary is NOT RivoNFC code12 0.6.5")
    adb("shell","am","force-stop",PACKAGE,check=False)
    adb("shell","am","start","-W","-n",PACKAGE+"/.MainActivity")
    time.sleep(13)
    adb("shell","pidof",PACKAGE)

    entries=[]
    last=None
    for name, expected, tab in SCREENS:
        if tab is not None:
            current=dump("before-"+name)
            press_tab(current,tab)
        nodes=dump(name)
        body=text(nodes).casefold()
        if expected.casefold() not in body:
            raise RuntimeError("Opened UI does not show correct "+name+" screen")
        if "ADVERTISEMENT".casefold() not in body:
            raise RuntimeError("Bounded bottom advertising slot is absent on "+name)
        if name=="01-scan" and any(n.attrib.get("scrollable")=="true" for n in nodes):
            raise RuntimeError("Real Scan home should not vertically scroll")
        digest=capture(name,nodes)
        if digest==last:
            raise RuntimeError("Two consecutive app screen captures are identical")
        last=digest
        entries.append({"file":name+".png","sha256":digest,
                        "hierarchy":name+".xml"})
        adb("shell","pidof",PACKAGE)
        print("RIVONFC_065_REAL_SIGNED_SCREEN="+name+" SHA256="+digest,flush=True)

    if len({x["sha256"] for x in entries})!=4:
        raise RuntimeError("All four signed APK screenshot captures must differ")
    manifest={
        "package":PACKAGE,"versionName":"0.6.5","versionCode":12,
        "screens":entries,"size":"1080x1920",
        "capture":"signed-release-APK-Android35-adb-no-synthetic-content",
        "noLiveAdRequests":True,"simulatedNfcReads":False,
    }
    (OUT/"CAPTURE-MANIFEST.json").write_text(
        json.dumps(manifest,ensure_ascii=False,indent=2,sort_keys=True)+"\n",
        encoding="utf-8")
    (OUT/"SHA256SUMS.txt").write_text(
        "".join(x["sha256"]+"  "+x["file"]+"\n" for x in entries))
    print("RIVONFC_065_REAL_SIGNED_SCREENSHOTS=4",flush=True)

if __name__=="__main__":
    main()
