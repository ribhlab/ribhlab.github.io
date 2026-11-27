#!/usr/bin/env python3
"""RivoNFC 0.6.4 code11 guarded Production + genuine store images/ads disclosures.

Updates ONLY com.ribhlab.rivonfc Production, en-US phone screenshots, and
existing Play listing full descriptions en-US/fr-FR/ar. Original icon, feature
graphic, other apps and Internal Testing remain unchanged. No publication if
Play Console Ads/Data safety attestations are not independently confirmed.

All writes are one uncommitted Google Play edit until validation succeeds.
Commit ERROR_IF_IN_REVIEW never silently cancels other Google reviews.
"""
from __future__ import annotations
import hashlib
import io
import json
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from google.auth.transport.requests import AuthorizedSession
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from PIL import Image, ImageStat
import requests

from publish import get_credentials
from rivonfc_064_promote import latest_bundle_guard

PKG="com.ribhlab.rivonfc"
OLD="9"
NEW="11"
MEDIA=Path("rivonfc-code11-store")
CONFIRM="RIVONFC_064_PLAY_ADS_DATASAFETY_VERIFIED"
REQUIRED_CAPTURE="signed-release-APK-Android35-adb-no-synthetic-content"
EXPECTED_PUBLIC={
    "https://ribhlab.github.io/rivonfc/privacy/":"Google Mobile Ads",
    "https://ribhlab.github.io/app-ads.txt":
        "google.com, pub-7945572016731367, DIRECT, f08c47fec0942fa0",
}
COPY={
    "en-US":"Advertising: this version displays a bottom banner and occasional full-screen ads at natural navigation breaks, only when privacy choices permit. Ads never interrupt an active NFC read or write. Optional rewarded ads are voluntary. Details: https://ribhlab.github.io/rivonfc/privacy/",
    "fr-FR":"Publicité : cette version affiche une bannière en bas et des annonces plein écran occasionnelles lors de la navigation, selon les choix de confidentialité. Aucune publicité n'interrompt la lecture ou l'écriture NFC. Les vidéos récompensées sont facultatives. https://ribhlab.github.io/rivonfc/privacy/",
    "ar":"الإعلانات: يعرض هذا الإصدار إعلان بانر داخل حاوية أسفل التطبيق وإعلانات بينية متباعدة عند التنقل بين الأقسام وبعد إعدادات الخصوصية. لا تقاطع الإعلانات عمليات قراءة أو كتابة NFC. إعلانات المكافآت اختيارية. https://ribhlab.github.io/rivonfc/privacy/",
}
EXPECTED_TITLES={"en-US":"RivoNFC: NFC Tools","fr-FR":"RivoNFC : Outils NFC","ar":"RivoNFC"}
RELEASE_NOTES=[
    {"language":"en-US","text":"Responsive NFC Scan dashboard with no scrolling; dedicated contained bottom banner; safer, consent-aware occasional interstitials; privacy improvements."},
    {"language":"fr-FR","text":"Accueil NFC adaptatif, bannière confinée en bas de l'écran, annonces plein écran moins fréquentes, et options de confidentialité."},
    {"language":"ar","text":"تحسين واجهة NFC بلا تمرير عمودي، حاوية ثابتة للإعلان السفلي، وإعلانات بينية متباعدة وفق إعدادات الخصوصية."},
]

def emit(name,value):
    print(name+"="+json.dumps(value,ensure_ascii=False,sort_keys=True),flush=True)

def verify_compliance_gate():
    if os.getenv("RIVONFC_064_COMPLIANCE_APPROVAL")!=CONFIRM:
        raise RuntimeError("Google Play Contains ads / Data safety forms not independently verified")
    # These independent booleans must come from user's Play Console inspection;
    # automated SDK checks cannot authenticate the live submitted declarations.
    if (os.getenv("RIVONFC_064_ADS_CONSOLE_VERIFIED")!="true" or
        os.getenv("RIVONFC_064_DATA_SAFETY_CONSOLE_VERIFIED")!="true" or
        os.getenv("RIVONFC_064_AD_ID_CONSOLE_VERIFIED")!="true"):
        raise RuntimeError("Google Play policy answers not independently confirmed in Console")

def verify_urls():
    for url,required in EXPECTED_PUBLIC.items():
        response=requests.get(url,timeout=20,allow_redirects=True)
        if (response.status_code!=200 or response.url.split("/")[2]!="ribhlab.github.io"
            or required not in response.text):
            raise RuntimeError("RivoNFC public policy / app-ads.txt URL invalid: "+url)

def verify_real_signed_screens():
    manifest=json.loads((MEDIA/"CAPTURE-MANIFEST.json").read_text(encoding="utf-8"))
    if (manifest.get("package")!=PKG or manifest.get("versionCode")!=11 or
        manifest.get("versionName")!="0.6.4" or
        manifest.get("capture")!=REQUIRED_CAPTURE or
        manifest.get("noLiveAdRequests") is not True or
        manifest.get("simulatedNfcReads") is not False or
        manifest.get("size")!="1080x1920"):
        raise RuntimeError("Store media are not real original-key signed code11 captures")
    records=manifest.get("screens",[])
    expected=["01-scan.png","02-write.png","03-tools.png","04-history.png"]
    if [r.get("file") for r in records]!=expected:
        raise RuntimeError("Store screenshot set is missing an actual code11 NFC screen")
    hashes=set()
    for record,heading in zip(records,("RivoNFC","Create & write","Tag tools","Activity")):
        filename=record["file"]
        raw=(MEDIA/filename).read_bytes()
        sha=hashlib.sha256(raw).hexdigest()
        if sha!=record.get("sha256") or sha in hashes or len(raw)<16_000:
            raise RuntimeError("Duplicate, modified or blank signed code11 screenshot: "+filename)
        hashes.add(sha)
        with Image.open(io.BytesIO(raw)) as im:
            if im.format!="PNG" or im.size!=(1080,1920):
                raise RuntimeError("Invalid native screenshot size or type")
            if max(ImageStat.Stat(im.convert("RGB").resize((96,160))).stddev)<9:
                raise RuntimeError("Screenshot is visually blank: "+filename)
        ui_file=MEDIA/record["hierarchy"]
        root=ET.parse(ui_file).getroot()
        nodes=list(root.iter("node"))
        texts=" ".join(n.attrib.get("text","")+" "+
            n.attrib.get("content-desc","") for n in nodes)
        if heading.casefold() not in texts.casefold() or "advertisement" not in texts.casefold():
            raise RuntimeError("Real Android accessibility hierarchy mismatch "+filename)
        if filename=="01-scan.png" and any(
            n.attrib.get("scrollable")=="true" for n in nodes):
            raise RuntimeError("Scan page has unwanted vertical scrolling")
    return expected

def current(edits,kw):
    return {t["track"]:t for t in edits.tracks().list(**kw).execute().get("tracks",[])}

def exact_one(track, code):
    rel=track.get("releases",[]) if track else []
    return len(rel)==1 and rel[0].get("status")=="completed" and [
        str(v) for v in rel[0].get("versionCodes",[])]==[code]

def media_ids(edits,kw,typ):
    return [x.get("id") for x in edits.images().list(
        **kw,language="en-US",imageType=typ).execute().get("images",[])]

def submit():
    # A dry-run validates the exact planned code11 Play edit and then discards it.
    # It never submits the release or represents legal policy declarations as saved.
    dry_run = os.environ.get("RIVONFC_064_DRY_RUN") == "true"
    if not dry_run:
        verify_compliance_gate()
    verify_urls()
    pngs=verify_real_signed_screens()
    creds=get_credentials()
    edits=build("androidpublisher","v3",credentials=creds,
                cache_discovery=False).edits()
    eid=edits.insert(packageName=PKG,body={}).execute()["id"]
    kw={"packageName":PKG,"editId":eid}
    committed=False
    try:
        before=current(edits,kw)
        if not exact_one(before.get("production"),OLD):
            raise RuntimeError("Unexpected RivoNFC Production track, refusing overwrite")
        if not exact_one(before.get("internal"),OLD):
            raise RuntimeError("RivoNFC Internal track changed, refusing overwrite")
        for name,track in before.items():
            if name not in ("production","internal") and any(
                int(v)>11 for r in track.get("releases",[])
                for v in r.get("versionCodes",[])):
                raise RuntimeError("Newer RivoNFC release exists on another track")
        bundles=[str(b["versionCode"]) for b in edits.bundles().list(**kw).execute().get("bundles",[])]
        latest_bundle_guard(bundles)
        media_before={typ:media_ids(edits,kw,typ) for typ in
                      ("icon","featureGraphic","phoneScreenshots")}
        if (len(media_before["icon"])!=1 or
            len(media_before["featureGraphic"])!=1 or
            len(media_before["phoneScreenshots"])<2):
            raise RuntimeError("Existing RivoNFC Play icon/feature/screenshots are incomplete")
        listings=edits.listings().list(**kw).execute().get("listings",[])
        found={row["language"]:row for row in listings}
        for language,title in EXPECTED_TITLES.items():
            if found.get(language,{}).get("title")!=title:
                raise RuntimeError("Existing localized RivoNFC Play title mismatch: "+language)
        emit("RIVONFC_064_PRODUCTION_PREFLIGHT",{
            "package":PKG,"newCode":11,"oldProduction":before["production"]["releases"],
            "oldInternal":before["internal"]["releases"],
            "signedVersionRealScreens":pngs,
            "oldScreens":len(media_before["phoneScreenshots"]),
            "adsDataSafetyAndAdvertisingIdVerifiedInConsole":not dry_run,
            "dryRunOnly":dry_run,
            "otherAppsTouched":False,
        })
        original=before["production"]["releases"][0]
        release={"name":"RivoNFC 0.6.4 — consent-aware AdMob and layout",
                 "status":"completed","versionCodes":[NEW],
                 "releaseNotes":RELEASE_NOTES}
        for preserve in ("countryTargeting","inAppUpdatePriority"):
            if preserve in original:release[preserve]=original[preserve]
        edits.tracks().update(**kw,track="production",body={
            "track":"production","releases":[release]}).execute()
        edits.images().deleteall(**kw,language="en-US",
                                 imageType="phoneScreenshots").execute()
        for filename in pngs:
            result=edits.images().upload(
                **kw,language="en-US",imageType="phoneScreenshots",
                media_body=MediaFileUpload(str(MEDIA/filename),mimetype="image/png")
            ).execute(num_retries=3)
            if not result.get("image",{}).get("id"):
                raise RuntimeError("Play did not accept genuine NFC "+filename)
        for language,copy in COPY.items():
            old=found[language]["fullDescription"]
            if len(old+"\n\n"+copy)>4000:
                raise RuntimeError("Play long description length overflow in "+language)
            # Do not overwrite the existing feature descriptions or localizations.
            if copy not in old:
                edits.listings().patch(**kw,language=language,
                    body={"fullDescription":old.rstrip()+"\n\n"+copy}).execute()
        after=current(edits,kw)
        for name,track in before.items():
            if name!="production" and after.get(name)!=track:
                raise RuntimeError("Another Google Play track changed inside edit")
        if (media_ids(edits,kw,"icon")!=media_before["icon"] or
            media_ids(edits,kw,"featureGraphic")!=media_before["featureGraphic"] or
            len(media_ids(edits,kw,"phoneScreenshots"))!=4):
            raise RuntimeError("Real screenshot or unchanged Play artwork requirement failed")
        edits.validate(**kw).execute()
        if dry_run:
            emit("RIVONFC_064_DRY_RUN_VALIDATED", {
                "package": PKG, "versionCode": 11,
                "plannedPhoneScreenshots": len(pngs),
                "releaseChangesNotCommitted": True,
                "existingPlayTracksRemainUnchanged": True,
                "adsDataSafetyAndAdvertisingIdNeedConsoleVerification": True,
            })
            return
        edits.commit(**kw,changesInReviewBehavior="ERROR_IF_IN_REVIEW").execute()
        committed=True
    finally:
        if not committed:
            try:edits.delete(**kw).execute()
            except Exception:
                print("RIVONFC_064_UNCOMMITTED_EDIT_DISCARD_WARNING",file=sys.stderr)
    # Play API edit accepted is NOT identical to public Google review approval.
    sess=AuthorizedSession(creds)
    resp=sess.get("https://androidpublisher.googleapis.com/androidpublisher/v3/"
        "applications/"+PKG+"/tracks/production/releases",timeout=25)
    lifecycle="UNKNOWN_OR_API_BLOCKED"
    if resp.status_code==200:
        for rel in resp.json().get("releases",[]):
            if 11 in [v.get("versionCode") for v in rel.get("activeArtifacts",[])]:
                lifecycle=rel.get("releaseLifecycleState","UNKNOWN")
                break
    emit("RIVONFC_064_PRODUCTION_RECEIPT",{
        "package":PKG,"versionCode":11,
        "playEditCommitted":True,"genuineScreenshots":4,
        "releaseLifecycle":lifecycle,
        "closedAlphaUnchanged":True,"internalUnchanged":True,
        "actualPublicReleaseRequiresGoogleApproval":True,
    })

if __name__=="__main__":
    try:submit()
    except HttpError as exc:
        try:reason=json.loads(exc.content.decode()).get("error",{}).get("message","")
        except Exception:reason=type(exc).__name__
        emit("RIVONFC_064_GOOGLE_PLAY_BLOCKED",{
            "httpStatus":int(exc.resp.status),"reason":reason[:480]})
        sys.exit(2)
    except Exception as exc:
        emit("RIVONFC_064_PRODUCTION_BLOCKED",{
            "type":type(exc).__name__,"reason":str(exc)[:480]})
        sys.exit(1)
