#!/usr/bin/env python3
"""Safely request review of the already-committed RivoMeasure 1.3.10 Production update.

No bundle upload, track mutation, localization change, image operation or
replacement of published code13. Uses a no-op Play edit with explicit
changesNotSentForReview=False; Google Play may still require the Play Console
'Publishing overview > Send for review' action. Never cancel an ongoing review.
"""
from __future__ import annotations

import json
import os
import sys
import time
from urllib.parse import quote

from google.auth.transport.requests import AuthorizedSession
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from publish import get_credentials

PACKAGE="com.ribhlab.ribhmeasure"
API="https://androidpublisher.googleapis.com/androidpublisher/v3"
EXPECTED_PENDING="RELEASE_LIFECYCLE_STATE_NOT_SENT_FOR_REVIEW"
PUBLISHED="RELEASE_LIFECYCLE_STATE_PUBLISHED"
IN_REVIEW="RELEASE_LIFECYCLE_STATE_IN_REVIEW"
READY="RELEASE_LIFECYCLE_STATE_APPROVED_NOT_PUBLISHED"
CONFIRM="SEND_EXACT_RIVOMEASURE_1310_CODE14_PRODUCTION_CHANGES_FOR_REVIEW_NO_CANCELLATION"


def emit(label, value):
    print(label+"="+json.dumps(value,sort_keys=True,ensure_ascii=False),flush=True)


def read(session,track):
    url=API+"/applications/"+quote(PACKAGE,safe="")+"/tracks/"+quote(track)+"/releases"
    response=session.get(url,timeout=25)
    if response.status_code!=200:
        raise RuntimeError(f"Read-only {track} lifecycle API returned HTTP {response.status_code}")
    result=[]
    for r in response.json().get("releases",[]):
        result.append({
            "name":r.get("releaseName",""),
            "state":r.get("releaseLifecycleState"),
            "codes":[int(x.get("versionCode",-1)) for x in r.get("activeArtifacts",[])]
        })
    return result


def classify(prod,alpha):
    good_old=any(r["codes"]==[13] and r["state"]==PUBLISHED for r in prod)
    pending=[r for r in prod if r["codes"]==[14]]
    safe_alpha=(len(alpha)==1 and alpha[0]["codes"]==[13] and alpha[0]["state"]==PUBLISHED)
    if not good_old or len(pending)!=1 or not safe_alpha:
        raise RuntimeError("Unexpected existing Production/Alpha release, refusing review changes")
    if any(any(c not in (13,14) for c in r["codes"]) for r in prod):
        raise RuntimeError("Unrecognized Production bundle; refusing review submission")
    return pending[0]["state"]


def main():
    if os.getenv("RIVOMEASURE_1310_SUBMIT_CONFIRM")!=CONFIRM:
        raise RuntimeError("Exact approved code14 review submission not authorized")
    credentials=get_credentials()
    session=AuthorizedSession(credentials)
    prod,alpha=read(session,"production"),read(session,"alpha")
    state=classify(prod,alpha)
    emit("RIVOMEASURE_1310_BEFORE_REVIEW",{
        "package":PACKAGE,"production":prod,"alpha":alpha,
        "code14Lifecycle":state,
    })
    if state in (IN_REVIEW,READY,PUBLISHED):
        emit("RIVOMEASURE_1310_REVIEW_RESULT",{
            "result":"ALREADY_SUBMITTED","state":state,"editCommitted":False})
        return
    if state!=EXPECTED_PENDING:
        raise RuntimeError("Code14 is not a known unsent-for-review release, no edit attempted")

    edits=build("androidpublisher","v3",credentials=credentials,
                cache_discovery=False).edits()
    eid=edits.insert(packageName=PACKAGE,body={}).execute()["id"]
    committed=False
    try:
        # No edits.tracks.update(), images, bundles, listings, or data-safety writes.
        # Explicitly disallow Google's default review-cancel behavior.
        edits.commit(
            packageName=PACKAGE,editId=eid,
            changesNotSentForReview=False,
            changesInReviewBehavior="ERROR_IF_IN_REVIEW"
        ).execute()
        committed=True
    finally:
        if not committed:
            try:edits.delete(packageName=PACKAGE,editId=eid).execute()
            except Exception:print("UNCOMMITTED_EDIT_CLEANUP_WARNING",file=sys.stderr)

    observed=EXPECTED_PENDING
    for attempt in range(5):
        if attempt:time.sleep(5)
        next_prod=read(session,"production")
        next_alpha=read(session,"alpha")
        observed=classify(next_prod,next_alpha)
        if observed!=EXPECTED_PENDING:
            break
    emit("RIVOMEASURE_1310_REVIEW_RESULT",{
        "package":PACKAGE,"versionCode":14,"noOpEditCommitted":True,
        "lifecycle":observed,
        "result":"REVIEW_SUBMITTED" if observed in (IN_REVIEW,READY,PUBLISHED)
                 else "PLAY_CONSOLE_SEND_FOR_REVIEW_REQUIRED",
        "productionReleaseChanged":False,
        "closedAlphaChanged":False,
    })
    if observed==EXPECTED_PENDING:
        raise RuntimeError("Play Console manual Send for review required; API edit did not submit changes")


if __name__=="__main__":
    try:main()
    except HttpError as e:
        try:message=json.loads(e.content.decode()).get("error",{}).get("message","")
        except Exception:message=type(e).__name__
        emit("RIVOMEASURE_1310_REVIEW_GOOGLE_ERROR",{
            "httpStatus":int(e.resp.status),"reason":message[:420]})
        sys.exit(2)
    except Exception as e:
        emit("RIVOMEASURE_1310_REVIEW_BLOCKED",{
            "exception":type(e).__name__,"reason":str(e)[:420]})
        sys.exit(1)
