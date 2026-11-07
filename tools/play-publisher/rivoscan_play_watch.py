#!/usr/bin/env python3
"""Read-only check for a SAVED Google Play release before owner art is applied.

Do not create a Play Edit while the owner is uploading an AAB in the Console.
The read-only releases endpoint cannot observe an in-progress upload or an AAB
saved outside a release track; keep waiting until a versionCode is visible.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path

PACKAGE="com.ribhlab.rivoscan"
EXPECTED_LOGO="67cd03f1d7e91e50ed398cc03c0a77482721e23053831df13984dbe3dffd9ce3"
EXPECTED_FEATURE="53c4af468ee27d6fba11dabc6b2ca9cee46b0ea331bfe410283b32786491e51c"
REQUEST=Path(__file__).parent/"store-listings/rivoscan-owner-assets-sync.json"

def validate_request(request:dict)->dict:
    if set(request)!={"enabled","appId","applied","iconSha256","featureSha256"}:
        raise ValueError("Owner assets request has unexpected fields")
    if request["appId"]!=PACKAGE or request["iconSha256"]!=EXPECTED_LOGO or request["featureSha256"]!=EXPECTED_FEATURE:
        raise ValueError("Owner assets request identifies wrong app or image hashes")
    if type(request["enabled"]) is not bool or type(request["applied"]) is not bool:
        raise ValueError("Owner assets request enable/applied must be booleans")
    return request

def visible_versions(report:dict)->list[dict]:
    versions=[]
    if report.get("package")!=PACKAGE:return versions
    for track,details in report.get("tracks",{}).items():
        if details.get("result")!="OK":continue
        for release in details.get("releases",[]):
            for code in release.get("versionCodes",[]):
                if str(code).isdigit() and int(code)>0:
                    versions.append({"track":track,"versionCode":int(code)})
    return sorted(versions,key=lambda item:(item["versionCode"],item["track"]))

def write_output(output:Path|None,ready:bool):
    if output:
        with output.open("a",encoding="utf-8") as f:f.write("ready="+("true" if ready else "false")+"\n")

def main(argv=None)->int:
    p=argparse.ArgumentParser()
    p.add_argument("--request",type=Path,default=REQUEST)
    p.add_argument("--github-output",type=Path)
    args=p.parse_args(argv)
    request=validate_request(json.loads(args.request.read_text(encoding="utf-8")))
    if not request["enabled"] or request["applied"]:
        state="DISABLED" if not request["enabled"] else "OWNER_ASSETS_ALREADY_APPLIED"
        write_output(args.github_output,False)
        print("RIVOSCAN_PLAY_WATCH="+json.dumps({"state":state,"package":PACKAGE}))
        return 0
    from audit_releases import audit
    report=audit(PACKAGE)
    available=visible_versions(report)
    status="SAVED_RELEASE_VISIBLE" if available else "WAITING_FOR_SAVED_TRACK_RELEASE"
    output={"state":status,"package":PACKAGE,"releaseVersions":available}
    print("RIVOSCAN_PLAY_WATCH="+json.dumps(output,sort_keys=True))
    if os.getenv("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"],"a",encoding="utf-8") as f:
            f.write("### RivoScan Play upload watch\n")
            f.write("- "+status+"\n")
            if available:f.write("- Saved versions: "+", ".join(str(v["versionCode"])+" ("+v["track"]+")" for v in available)+"\n")
            else:f.write("- No saved version is yet visible in a tracked release. This check cannot observe upload progress in Play Console.\n")
    write_output(args.github_output,bool(available))
    return 0
if __name__=="__main__":
    try:raise SystemExit(main())
    except Exception as e:
        print("PLAY_WATCH_FAILED: "+type(e).__name__)
        raise SystemExit(1)
