#!/usr/bin/env python3
"""Record real code19 RivoCaption mediaProcessing foreground service on Android 15.
No mock application frames. Fail if the actual processing service cannot be observed.
"""
from __future__ import annotations
import json, subprocess, time
from pathlib import Path
import rivocaption_real_media as ui

OUT=Path("/tmp/rivocaption-media-processing")
APK=Path("/tmp/rivocaption-045.apk")
PACKAGE="com.rivocaption.editor"
VIDEO="RivoCaption-FGS-MediaProcessing-Demo.mp4"

def log(name,**kw):
    print(name+"="+json.dumps(kw,ensure_ascii=False),flush=True)

def voiced_sample(out):
    speech=out/"sample-speech.wav"
    sentence=("Hello RivoCaption. This is a real example of converting speech from a video "
              "into subtitles with offline artificial intelligence. "
              "The process is started by the user and remains visible. ")
    subprocess.run(["espeak-ng","-v","en-us","-s","145","-w",str(speech),
                    sentence*5],check=True,timeout=60)
    sample=out/"RivoCaptionDemo.mp4"
    subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y",
        "-f","lavfi","-i","testsrc2=size=720x1280:rate=24",
        "-i",str(speech),"-t","50","-shortest",
        "-c:v","libx264","-preset","ultrafast","-pix_fmt","yuv420p",
        "-c:a","aac","-b:a","128k","-movflags","+faststart",str(sample)],
        check=True,timeout=150)
    if sample.stat().st_size<80000:
        raise RuntimeError("Audio/video sample creation failed")
    ui.adb("shell","mkdir","-p","/sdcard/Movies")
    ui.adb("push",str(sample),"/sdcard/Movies/RivoCaptionDemo.mp4")
    ui.adb("shell","am","broadcast","-a","android.intent.action.MEDIA_SCANNER_SCAN_FILE",
        "-d","file:///sdcard/Movies/RivoCaptionDemo.mp4")
    log("GENUINE_AUDIO_VIDEO_SAMPLE",bytes=sample.stat().st_size)

def get_nodes(stage):
    return ui.dump_ui(OUT,stage)

def tap_label(label,limit=8):
    for i in range(limit):
        nodes=get_nodes("search-"+label.replace(" ","-").lower()+str(i))
        if ui.tap(nodes,label,partial=True):
            return True
        # Short scroll; on the compact AI panel the button can be below fold.
        ui.adb("shell","input","swipe","520","1540","520","1220","430")
        time.sleep(1)
    return False

def visible_text():
    nodes=get_nodes("state-"+str(int(time.time())))
    return [str(n.get(k,"")) for n in nodes for k in ("text","content-desc") if n.get(k,"")]

def evidence(stage):
    # Real running service and app notification; no staged notification or fake screenshot.
    a=ui.adb("shell","dumpsys","activity","services",PACKAGE,timeout=30)
    n=ui.adb("shell","dumpsys","notification","--noredact",timeout=30)
    svc="WhisperRecognitionService" in a
    related=[x.strip()[:400] for x in n.splitlines() if PACKAGE in x
             and ("NotificationRecord" in x or "NotificationRecord{" in x)]
    (OUT/("fgs-"+stage+".txt")).write_text(a[:20000]+"\n--- NOTIFICATIONS ---\n"+n[:20000],"utf-8")
    log("REAL_MEDIA_PROCESSING_FOREGROUND",stage=stage,whisperService=svc,notification=bool(related),records=related[:3])
    return svc or bool(related)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    if not APK.is_file():
        raise RuntimeError("Real code19 APK missing")
    ui.adb("shell","wm","size","1080x1920")
    ui.adb("shell","wm","density","440")
    ui.adb("install","-r",str(APK),timeout=240)
    ui.adb("shell","svc","wifi","disable")
    ui.adb("shell","svc","data","disable")
    ui.adb("shell","am","force-stop",PACKAGE)
    ui.adb("shell","am","start","-W","-n",PACKAGE+"/.MainActivity")
    time.sleep(14)
    nodes=get_nodes("real-code19-home")
    if not any("studio" in str(n.get("text","")).lower() for n in nodes):
        raise RuntimeError("Real code19 RivoCaption home not visible")
    voiced_sample(OUT)
    ui.open_video_in_picker(OUT)
    time.sleep(3)
    nodes=get_nodes("after-media-picker")
    if ui.tap(nodes,"Got it"):
        time.sleep(2)
    if not tap_label("AI",4):
        raise RuntimeError("Real AI tab missing")
    # The default "Accurate" model is approximately 466 MB. Select the REAL
    # Fast/Balanced 142-MB model so the recorded foreground demo is repeatable.
    if not tap_label("Settings",3):
        raise RuntimeError("Real RivoCaption settings could not be opened")
    changed=False
    for k in range(6):
        nodes=get_nodes("whisper-quality-fast-"+str(k))
        if ui.tap(nodes,"Fast"):
            changed=True
            break
        ui.adb("shell","input","swipe","520","1510","520","1120","420")
        time.sleep(1)
    if not changed:
        raise RuntimeError("Real Whisper Fast/Balanced model chip not reachable")
    if not ui.tap(get_nodes("after-fast-choice"),"Done"):
        raise RuntimeError("RivoCaption settings Done button missing")
    log("REAL_WHISPER_FAST_BALANCED_SELECTED",status=True)
    ui.adb("shell","pm","grant",PACKAGE,"android.permission.POST_NOTIFICATIONS")
    ui.adb("shell","svc","wifi","enable")
    time.sleep(3)
    abis=ui.adb("shell","getprop","ro.product.cpu.abilist").strip()
    log("EMULATOR_SUPPORTED_ABIS",abis=abis)
    if "arm64-v8a" not in abis.split(","):
        raise RuntimeError("Emulator does not support the ARM64 Whisper native speech decoder")
    nodes=get_nodes("before-voice-model")
    labels=[n.get("text","") for n in nodes]
    if not any("Start transcription" in s for s in labels):
        if not tap_label("Download model & transcribe",4):
            raise RuntimeError("No genuine offline speech model download action")
        nodes=get_nodes("download-confirmation")
        if not ui.tap(nodes,"Download in background"):
            raise RuntimeError("Download consent not found")
        log("REAL_MODEL_DOWNLOAD_STARTED",status=True)
        ready=False
        for k in range(100):
            time.sleep(3)
            labels=visible_text()
            if any("Start transcription" in s for s in labels):
                ready=True
                break
            if k%10==0:
                log("MODEL_WAIT",seconds=3*(k+1),ui=labels[:15])
        if not ready:
            raise RuntimeError("Whisper speech model not installed; cannot demonstrate processing")
    # Return to UI with real selected video; record before pressing the real button.
    nodes=get_nodes("media-transcription-ready")
    if not any("Start transcription" in str(n.get("text","")) for n in nodes):
        raise RuntimeError("Cannot see user-initiated offline transcription button")
    output=OUT/VIDEO
    remote="/sdcard/Movies/"+VIDEO
    rec=subprocess.Popen(["adb","shell","screenrecord","--time-limit","100","--bit-rate","1300000",
        "--size","540x960",remote],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    time.sleep(2)
    observed=False
    try:
        if not ui.tap(nodes,"Start transcription"):
            raise RuntimeError("Real user transcription control not clickable")
        log("REAL_USER_STARTED_OFFLINE_MEDIA_PROCESSING",status=True)
        for k in range(16):
            time.sleep(1.4)
            if evidence("transcribing-"+str(k)):
                observed=True
                break
        # Expose the ongoing native notification to Google Play review.
        ui.adb("shell","input","swipe","380","0","380","1340","490")
        time.sleep(3)
        shown=visible_text()
        log("REAL_MEDIA_PROCESSING_NOTIFICATION_SHADE",labels=shown[:70])
        time.sleep(5)
        ui.adb("shell","input","keyevent","4")
        time.sleep(3)
        if not observed:
            raise RuntimeError("Real code19 mediaProcessing foreground service not observed; refuse to publish fake proof")
    finally:
        ui.adb("shell","pkill","-2","screenrecord")
        try: rec.wait(timeout=20)
        except subprocess.TimeoutExpired:
            rec.kill()
            rec.wait(timeout=5)
        ui.adb("pull",remote,str(output),timeout=90)
    if output.stat().st_size < 120000:
        raise RuntimeError("Real mediaProcessing screen recording missing/tiny")
    log("RIVOCAPTION_REAL_CODE19_MEDIA_PROCESSING_VIDEO_VERIFIED",bytes=output.stat().st_size,
        foregroundServiceObserved=observed,filename=VIDEO)

if __name__=="__main__":
    main()
