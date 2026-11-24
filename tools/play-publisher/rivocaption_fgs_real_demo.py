#!/usr/bin/env python3
"""Record actual user-initiated WorkManager foreground DATA_SYNC model download in the signed RivoCaption APK."""
import os, subprocess, time, json, sys
from pathlib import Path
from rivocaption_real_media import adb, dump_ui, tap, capture

OUT=Path("/tmp/rivocaption-fgs-demo")
APK=Path("/tmp/rivocaption-034.apk")

def log(tag, **kwargs):
    print(tag+"="+json.dumps(kwargs,ensure_ascii=False),flush=True)

def screenrecord():
    cmd=["adb","shell","screenrecord","--time-limit","90","--bit-rate","1200000","--size","540x960",
         "/sdcard/Movies/RivoCaption-FGS-DataSync-Demo.mp4"]
    return subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)

def notification_evidence(stage):
    lines=adb("shell","dumpsys","notification","--noredact")
    parts=[line.strip()[:350] for line in lines.splitlines() if "RivoCaption" in line or "rivocaption_model_downloads" in line or "androidx.work.impl.foreground" in line]
    log("FGS_NOTIFICATION_EVIDENCE",stage=stage,related=parts[:20])
    (OUT/("notification-"+stage+".txt")).write_text("\n".join(parts),encoding="utf-8")
    return bool(parts)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    # Exactly reuse the previously successful, 5-screenshot, native Android path.
    # It disables Wi-Fi while launching; the Google emulator's Pixel Launcher can
    # ANR if networking is initialized during the first app rendering.
    # This verifies that the correct signed application truly works before recording.
    capture(APK,OUT)
    nodes=dump_ui(OUT,"fgs-editor-loaded")
    if tap(nodes,"Got it"):
        nodes=dump_ui(OUT,"fgs-editor-after-onboarding")
    if not tap(nodes,"AI"):
        raise RuntimeError("Genuine RivoCaption AI speech tab not found")
    # Network is only needed for user-initiated offline-model transfer.
    # Enable after Android app UI is stable, not during launcher boot.
    adb("shell","svc","wifi","enable")
    time.sleep(3)
    rec=screenrecord()
    time.sleep(2)
    try:
        found=False
        for attempt in range(7):
            nodes=dump_ui(OUT,"fgs-ai-download-attempt-"+str(attempt))
            if tap(nodes,"Got it"):
                continue
            if tap(nodes,"Download speech model"):
                found=True
                break
            adb("shell","input","swipe","500","1660","500","870","520")
            time.sleep(1)
        if not found:
            raise RuntimeError("Real signed RivoCaption model download control not reachable")
        nodes=dump_ui(OUT,"fgs-download-consent")
        if not tap(nodes,"Start background download"):
            raise RuntimeError("User-initiated download consent button not visible")
        log("FGS_USER_INITIATED_DOWNLOAD",status="confirmed")
        time.sleep(8)
        notifications=notification_evidence("running")
        adb("shell","input","swipe","400","0","400","1450","450")
        time.sleep(3)
        dump_ui(OUT,"fgs-notification-shade")
        time.sleep(12)
        notification_evidence("later")
        adb("shell","input","keyevent","4")
        adb("shell","input","keyevent","3")
        time.sleep(3)
        notification_evidence("background")
        adb("shell","input","swipe","400","0","400","1450","450")
        time.sleep(3)
        dump_ui(OUT,"fgs-user-sees-background-progress")
        if not notifications:
            raise RuntimeError("No RivoCaption notification verified, so do not pretend foreground service demo was captured")
    finally:
        try:
            rec.wait(timeout=105)
        except subprocess.TimeoutExpired:
            adb("shell","pkill","-2","screenrecord")
            rec.wait(timeout=15)
        adb("pull","/sdcard/Movies/RivoCaption-FGS-DataSync-Demo.mp4",str(OUT/"RivoCaption-FGS-DataSync-Demo.mp4"),timeout=90)
        f=OUT/"RivoCaption-FGS-DataSync-Demo.mp4"
        log("FGS_REAL_VIDEO_CAPTURED",size=f.stat().st_size,valid=f.stat().st_size>150000)
    if f.stat().st_size<=150000:
        raise RuntimeError("Recorded MP4 too small; refuse declaration asset")
if __name__=="__main__":
    main()
