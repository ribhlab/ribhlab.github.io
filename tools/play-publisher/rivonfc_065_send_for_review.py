#!/usr/bin/env python3
"""Send only already-committed RivoNFC v0.6.5 code12 for review; no track writes.

Requires exact published code11 + single not-sent code12 Production release.
Never cancel any Google review, touch other apps, Media, policy declarations,
SDK versions, or metadata. In-review/approved/published -> read-only no-op.
"""
from __future__ import annotations
import json
import os
import sys
import time
from google.auth.transport.requests import AuthorizedSession
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from publish import get_credentials

PKG="com.ribhlab.rivonfc"
API="https://androidpublisher.googleapis.com/androidpublisher/v3/applications/"
PUBLISHED="RELEASE_LIFECYCLE_STATE_PUBLISHED"
UNSENT="RELEASE_LIFECYCLE_STATE_NOT_SENT_FOR_REVIEW"
IN_REVIEW="RELEASE_LIFECYCLE_STATE_IN_REVIEW"
APPROVED="RELEASE_LIFECYCLE_STATE_APPROVED_NOT_PUBLISHED"
CONFIRM="SEND_ONLY_ALREADY_COMMITTED_RIVONFC_CODE12_ICON_SAFE_FOR_GOOGLE_REVIEW"

def emit(name,data):
    print(name+"="+json.dumps(data,ensure_ascii=False,sort_keys=True),flush=True)

def read(session,track):
    url=API+PKG+"/tracks/"+track+"/releases"
    for attempt in range(5):
        resp=session.get(url,timeout=30)
        if resp.status_code==200:break
        if resp.status_code not in (403,429,500,503) or attempt==4:
            raise RuntimeError("Google Play read-only "+track+" release API HTTP "+str(resp.status_code))
        time.sleep(3)
    return [{
        "state":r.get("releaseLifecycleState",""),
        "name":r.get("releaseName",""),
        "codes":[int(x.get("versionCode",-1)) for x in r.get("activeArtifacts",[])]
    } for r in resp.json().get("releases",[])]

def current_state(production):
    if any(any(c not in (11,12) for c in rel["codes"]) for rel in production):
        raise RuntimeError("Unexpected Production release codes; refusing unsafe submission")
    old=[x for x in production if x["codes"]==[11] and x["state"]==PUBLISHED]
    newer=[x for x in production if x["codes"]==[12]]
    if len(old)!=1 or len(newer)!=1:
        raise RuntimeError("Expected exactly published code11 and staged code12; review of another release is not allowed")
    return newer[0]["state"]

def main():
    if os.getenv("RIVONFC_065_REVIEW_CONFIRM")!=CONFIRM:
        raise RuntimeError("RivoNFC-specific code12 review authorization absent")
    credentials=get_credentials()
    session=AuthorizedSession(credentials)
    before=read(session,"production")
    state=current_state(before)
    emit("RIVONFC_065_REVIEW_PREFLIGHT",{"package":PKG,"production":before,"code12":state})
    if state in (IN_REVIEW,APPROVED,PUBLISHED):
        emit("RIVONFC_065_REVIEW_RECEIPT",{
            "package":PKG,"code":12,"alreadyUnderReviewOrPublished":True,
            "code12State":state,"playEditCommitted":False})
        return
    if state!=UNSENT:
        raise RuntimeError("Code12 is not in expected not-sent state, abort without changes")
    edit=build("androidpublisher","v3",credentials=credentials,
               cache_discovery=False).edits()
    eid=edit.insert(packageName=PKG,body={}).execute()["id"]
    kw={"packageName":PKG,"editId":eid}
    committed=False
    try:
        # No app bundle, listing, image, policy, locale or track modifications.
        # Publishing a no-op edit asks Google to review the already-committed update.
        edit.commit(
            **kw,
            changesNotSentForReview=False,
            changesInReviewBehavior="ERROR_IF_IN_REVIEW"
        ).execute()
        committed=True
    finally:
        if not committed:
            try:edit.delete(**kw).execute()
            except Exception:print("RIVONFC_065_ABORTED_EMPTY_EDIT_WARNING",file=sys.stderr)

    latest=UNSENT
    for i in range(6):
        if i:time.sleep(5)
        prod=read(session,"production")
        latest=current_state(prod)
        if latest!=UNSENT:break
    emit("RIVONFC_065_REVIEW_RECEIPT",{
        "package":PKG,"code":12,"noOpEditCommitted":True,
        "code12State":latest,
        "result":"REVIEW_SUBMITTED" if latest in (IN_REVIEW,APPROVED,PUBLISHED)
                 else "PLAY_CONSOLE_SEND_FOR_REVIEW_REQUIRED",
        "version11PublishedNotRemoved":True,
        "noOtherAppTouched":True,
    })
    if latest==UNSENT:
        raise RuntimeError("Google requires manual Publishing overview > Send for review")

if __name__=="__main__":
    try:main()
    except HttpError as exc:
        try:message=json.loads(exc.content.decode()).get("error",{}).get("message","")
        except Exception:message=type(exc).__name__
        emit("RIVONFC_065_REVIEW_PLAY_API_ERROR",{
            "httpStatus":int(exc.resp.status),"reason":message[:450]})
        sys.exit(2)
    except Exception as exc:
        emit("RIVONFC_065_REVIEW_BLOCKED",{
            "type":type(exc).__name__,"reason":str(exc)[:450]})
        sys.exit(1)
