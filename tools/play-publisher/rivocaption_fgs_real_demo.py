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
    # Active notification records only. A channel declaration by itself does
    # NOT prove that a foreground service or visible notification is running.
    records=[line.strip()[:650] for line in lines.splitlines()
             if "com.rivocaption.editor" in line
             and ("NotificationRecord(" in line or "NotificationRecord{" in line)]
    related=[line.strip()[:350] for line in lines.splitlines()
             if "RivoCaption" in line or "rivocaption_model_downloads" in line or "com.rivocaption.editor" in line]
    log("FGS_NOTIFICATION_EVIDENCE",stage=stage,activeRecords=records[:10],related=related[:25])
    (OUT/("notification-"+stage+".txt")).write_text("\n".join(records+related),encoding="utf-8")
    return bool(records)

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
    # The emulator test user grants notification permission just as they
    # could via Android's permission prompt, so the reviewer sees progress.
    adb("shell","pm","grant","com.rivocaption.editor","android.permission.POST_NOTIFICATIONS")
    log("ANDROID_TEST_USER_NOTIFICATION_PERMISSION",status="granted")
    # Network is only needed for user-initiated offline-model transfer.
    # Enable after Android app UI is stable, not during launcher boot.
    adb("shell","svc","wifi","enable")
    time.sleep(3)
    rec=screenrecord()
    time.sleep(2)
    try:
        # Select the actual 128-MB higher accuracy model so the foreground
        # transfer lasts long enough to show a visible ongoing notification.
        selected=False
        for attempt in range(5):
            nodes=dump_ui(OUT,"speech-model-selector-"+str(attempt))
            if tap(nodes,"English (fast)"):
                options=dump_ui(OUT,"speech-model-choices")
                if tap(options,"English (higher accuracy)"):
                    selected=True
                break
            adb("shell","input","swipe","500","1580","500","850","450")
            time.sleep(1)
        if not selected:
            raise RuntimeError("Could not select real higher-accuracy offline speech model")
        found=False
        for attempt in range(7):
            nodes=dump_ui(OUT,"fgs-ai-download-attempt-"+str(attempt))
            if tap(nodes,"Got it"):
                continue
            if tap(nodes,"Download speech model"):
                found=True
                break
            # The speech model selector is at y≈1440 and the model caption
            # at y≈1650. The button is just below the viewport; a 790px
            # swipe overshoots straight to the Translation panel. Scroll in
            # small, reversible increments to show the actual Download button.
            labels={n.get("text","") for n in nodes}
            if "ON-DEVICE TRANSLATION" in labels and not any(x.startswith("Model: ") for x in labels):
                adb("shell","input","swipe","500","1000","500","1340","480")
                log("FGS_MODEL_SCROLL",direction="backward",attempt=attempt)
            else:
                adb("shell","input","swipe","500","1570","500","1270","480")
                log("FGS_MODEL_SCROLL",direction="forward",attempt=attempt)
            time.sleep(1)
        if not found:
            raise RuntimeError("Real signed RivoCaption model download control not reachable")
        nodes=dump_ui(OUT,"fgs-download-consent")
        if not tap(nodes,"Start background download"):
            raise RuntimeError("User-initiated download consent button not visible")
        log("FGS_USER_INITIATED_DOWNLOAD",status="confirmed")
        notifications=False
        for attempt in range(9):
            time.sleep(2)
            if notification_evidence("running-"+str(attempt)):
                notifications=True
                break
        adb("shell","input","swipe","400","0","400","1450","450")
        time.sleep(3)
        visible=dump_ui(OUT,"fgs-notification-shade")
        readable=[str(n.get(k,"")) for n in visible for k in ("text","content-desc")]
        visible_notice=any("RivoCaption" in x or "Model download" in x or "English" in x for x in readable)
        log("FGS_VISIBLE_NOTIFICATION_SHADE",found=visible_notice,matching=[x for x in readable if "RivoCaption" in x or "download" in x.lower()][:14])
        time.sleep(12)
        notification_evidence("later")
        adb("shell","input","keyevent","4")
        adb("shell","input","keyevent","3")
        time.sleep(3)
        notification_evidence("background")
        adb("shell","input","swipe","400","0","400","1450","450")
        time.sleep(3)
        dump_ui(OUT,"fgs-user-sees-background-progress")
        if not notifications or not visible_notice:
            raise RuntimeError("Active RivoCaption notification was NOT demonstrated in real Android UI; refuse to publish misleading FGS demo")
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
