#!/usr/bin/env python3
"""Inspect uploaded RivoScan AAB version codes and the actual Play tracks.

Does not upload, update, commit, or publish anything. Requires an API edit for
Play's official bundle inventory; deletes the edit in all cases. Avoid running
while a Play Console edit/upload remains unsaved.
"""
import json
import sys
from publish import get_credentials

PACKAGE = "com.ribhlab.rivoscan"
def inspect():
    from googleapiclient.discovery import build
    edits = build("androidpublisher", "v3", credentials=get_credentials(), cache_discovery=False).edits()
    edit = edits.insert(packageName=PACKAGE, body={}).execute()
    edit_id = edit["id"]
    try:
        bundles = edits.bundles().list(packageName=PACKAGE, editId=edit_id).execute().get("bundles", [])
        tracks = edits.tracks().list(packageName=PACKAGE, editId=edit_id).execute().get("tracks", [])
        versions = sorted({
            int(item["versionCode"]) for item in bundles
            if isinstance(item, dict) and str(item.get("versionCode", "")).isdigit()
        })
        tracks_out = []
        for t in tracks:
            name = t.get("track")
            if name not in ("qa", "internal", "alpha", "beta", "production") and not name:
                continue
            releases = []
            for rel in t.get("releases", []):
                codes = [int(c) for c in rel.get("versionCodes", []) if str(c).isdigit()]
                releases.append({"status":rel.get("status"),"versionCodes":codes})
            tracks_out.append({"track":name,"releases":releases})
        return {"package":PACKAGE, "bundleVersionCodes":versions, "tracks":tracks_out,
                "note":"Inventory is saved Play content only; an unsaved Play Console draft may be invisible."}
    finally:
        try:
            edits.delete(packageName=PACKAGE, editId=edit_id).execute()
        except Exception:
            print("WARNING: could not delete read-only inspection edit", file=sys.stderr)
def main():
    try:
        print("RIVOSCAN_PLAY_INVENTORY=" + json.dumps(inspect(), sort_keys=True))
    except Exception as exc:
        status = getattr(getattr(exc,"resp",None),"status",None)
        print("RIVOSCAN_PLAY_INVENTORY_ERROR="+json.dumps({"error":type(exc).__name__,"httpStatus":status}))
        return 1
    return 0
if __name__=="__main__":
    raise SystemExit(main())
