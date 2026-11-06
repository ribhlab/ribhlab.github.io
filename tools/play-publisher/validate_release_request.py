#!/usr/bin/env python3
"""Validate a committed RivoScan release request; never reads credentials."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from publish_existing import validate, parser as release_parser

EXPECTED = "com.ribhlab.rivoscan"


def parse_request(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Release request must be an object")
    if data.get("package") != EXPECTED:
        raise ValueError("Only RivoScan can be published by this workflow")
    enabled = data.get("enabled", False)
    if type(enabled) is not bool:
        raise ValueError("enabled must be a boolean")
    if not enabled:
        return {"enabled": "false"}
    allowed = {"enabled", "package", "versionCode", "track", "status",
               "notes", "productionConfirmation", "commitConfirmation"}
    if any(key not in allowed for key in data):
        raise ValueError("Unexpected release-request field")
    if data.get("commitConfirmation") != "COMMIT":
        raise ValueError("Release request must explicitly authorize a COMMIT")
    code = data.get("versionCode")
    if type(code) is not int:
        raise ValueError("versionCode must be an integer")
    notes = data.get("notes", "")
    if not isinstance(notes, str) or "\n" in notes or "\r" in notes:
        raise ValueError("Notes must be single-line text")
    a = release_parser().parse_args([
        "--package", EXPECTED,
        "--version-code", str(code),
        "--track", data.get("track", "internal"),
        "--status", data.get("status", "draft"),
        "--notes", notes,
        "--confirm-commit", data["commitConfirmation"],
        "--confirm-production", data.get("productionConfirmation", ""),
    ])
    validate(a)
    return {
        "enabled": "true",
        "version_code": str(a.version_code),
        "track": a.track,
        "status": a.status,
        "production_confirmation": a.confirm_production,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--file", required=True, type=Path)
    p.add_argument("--github-output", type=Path, required=True)
    a = p.parse_args()
    result = parse_request(a.file)
    # Append validated, single-line values to the official GitHub step output file.
    with a.github_output.open("a", encoding="utf-8") as f:
        for key, value in result.items():
            f.write(f"{key}={value}\n")
    print("RELEASE_REQUEST_VALIDATED:", json.dumps(result))


if __name__ == "__main__":
    main()
