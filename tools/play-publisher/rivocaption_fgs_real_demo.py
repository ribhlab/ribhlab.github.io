#!/usr/bin/env python3
"""Record actual user-initiated WorkManager foreground DATA_SYNC model download in the signed RivoCaption APK."""
import os, subprocess, time, json, sys
from pathlib import Path
from rivocaption_real_media import adb, dump_ui, tap, setup_sample_video, open_video_in_picker

OUT=Path("/tmp/rivocaption-fgs-demo")
APK=Path("/tmp/rivocaption-034.apk")

def log(tag, **kwargs):
    print(tag+"="+json.dumps(kwargs,ensure_ascii=False),flush=True)

def screenrecord():
    cmd=["adb","shell","screenrecord","--time-limit","125","--bit-rate","1200000","--size","540x960",
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
    adb("shell","wm","size","1080x1920")
    adb("shell","wm","density","440")
    # Create sample media before app launch, to avoid CPU stress on Android Launcher
    # while recording the foreground-service demonstration.
    setup_sample_video(OUT)
    adb("install","-r",str(APK),timeout=180)
    adb("shell","svc","wifi","enable")
    adb("shell","svc","data","enable")
    adb("shell","am","force-stop","com.rivocaption.editor")
    adb("shell","am","start","-W","-n","com.rivocaption.editor/.MainActivity")
    # Keep only authentic screenshots. An emulator may show a transient Pixel
    # Launcher ANR; dismiss it and restart the real, original-signed application.
    ready=False
    for attempt in range(6):
        time.sleep(9 if attempt == 0 else 6)
        nodes=dump_ui(OUT,"startup-"+str(attempt))
        names={n.get("text","") for n in nodes}
        if "Your creative studio" in names:
            ready=True
            break
        if "Pixel Launcher isn't responding" in names or "RivoCaption isn't responding" in names:
            tap(nodes,"Wait")
            time.sleep(5)
        adb("shell","am","start","-W","-n","com.rivocaption.editor/.MainActivity")
    if not ready:
        raise RuntimeError("Real RivoCaption home UI did not stabilize after ANR recovery")
    rec=screenrecord()
    time.sleep(2)
    try:
        open_video_in_picker(OUT)
        time.sleep(6)
        nodes=dump_ui(OUT,"fgs-after-import")
        if tap(nodes,"Got it"): nodes=dump_ui(OUT,"fgs-after-immersive")
        if not tap(nodes,"Download speech model"):
            nodes=dump_ui(OUT,"fgs-looking-for-download")
            raise RuntimeError("Actual signed app does not display Download speech model")
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
            rec.wait(timeout=135)
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
