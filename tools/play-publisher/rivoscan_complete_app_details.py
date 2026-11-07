#!/usr/bin/env python3
"""Complete verified, editable RivoScan store metadata using Play Android Publisher.

Only default language, website and developer support email are in scope.
Does not access content-rating, app-access, ads or target-age policy forms.
"""
from __future__ import annotations
import json
import sys

PACKAGE="com.ribhlab.rivoscan"
DESIRED={
    "defaultLanguage":"en-US",
    "contactWebsite":"https://ribhlab.github.io/rivoscan/",
    "contactEmail":"rachid022note4@gmail.com",
}

def update_details(edits):
    edit=edits.insert(packageName=PACKAGE,body={}).execute()
    eid=edit["id"]
    committed=False
    try:
        current=edits.details().get(packageName=PACKAGE,editId=eid).execute()
        changed={k:v for k,v in DESIRED.items() if current.get(k)!=v}
        if not changed:
            return {"result":"ALREADY_CORRECT","changedFields":[]}
        # PATCH, not UPDATE, so any contact phone or unrecognized values remain.
        edits.details().patch(packageName=PACKAGE,editId=eid,body=changed).execute()
        edits.validate(packageName=PACKAGE,editId=eid).execute()
        edits.commit(packageName=PACKAGE,editId=eid).execute()
        committed=True
        return {"result":"STORE_DETAILS_COMMITTED","changedFields":sorted(changed)}
    finally:
        if not committed:
            try:
                edits.delete(packageName=PACKAGE,editId=eid).execute()
            except Exception:
                print("WARNING: could not discard noncommitted Play metadata edit",file=sys.stderr)

def main():
    try:
        from googleapiclient.discovery import build
        from publish import get_credentials
        service=build("androidpublisher","v3",credentials=get_credentials(),cache_discovery=False)
        result=update_details(service.edits())
        print("RIVOSCAN_APP_DETAILS="+json.dumps(result,sort_keys=True))
        return 0
    except Exception as exc:
        status=getattr(getattr(exc,"resp",None),"status",None)
        print("RIVOSCAN_APP_DETAILS_ERROR="+json.dumps({
            "error":type(exc).__name__,"httpStatus":status},sort_keys=True),file=sys.stderr)
        return 1
if __name__=="__main__":
    raise SystemExit(main())
