"""Read-only verification of the Etsy OAuth grant and its shop connection.

No product is created, changed, uploaded, or published.
Never print raw tokens, secrets, or Etsy response bodies in GitHub Actions logs.
"""
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://api.etsy.com/v3"


class ConnectionErrorSafe(Exception):
    pass


def load_required():
    required = ("ETSY_KEYSTRING", "ETSY_SHARED_SECRET", "ETSY_REFRESH_TOKEN")
    missing = [name for name in required if not os.environ.get(name, "").strip()]
    if missing:
        raise ConnectionErrorSafe("Missing repository secret(s): " + ", ".join(missing))
    return [os.environ[name].strip() for name in required]


def get_json(request, stage):
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            data = response.read(1024 * 1024)
    except urllib.error.HTTPError as exc:
        # Do NOT print Etsy's response: it may contain account or token details.
        raise ConnectionErrorSafe(f"{stage} rejected by Etsy (HTTP {exc.code}).") from None
    except urllib.error.URLError:
        raise ConnectionErrorSafe(f"{stage} could not reach Etsy.") from None
    try:
        return json.loads(data)
    except (ValueError, UnicodeDecodeError):
        raise ConnectionErrorSafe(f"{stage} returned an invalid response.") from None


def get_shop_id(key, shared, access):
    user_id = access.split(".", 1)[0]
    if not re.fullmatch(r"\d{1,20}", user_id):
        raise ConnectionErrorSafe("Etsy returned an access token without a valid user ID prefix.")
    req = urllib.request.Request(
        f"{BASE}/application/users/{user_id}/shops",
        headers={"x-api-key": key + ":" + shared, "Authorization": "Bearer " + access},
    )
    payload = get_json(req, "Read-only shop lookup")
    if isinstance(payload, dict) and payload.get("shop_id"):
        result = payload
    elif isinstance(payload, dict) and isinstance(payload.get("results"), list) and payload["results"]:
        result = payload["results"][0]
    else:
        raise ConnectionErrorSafe("Etsy did not return a shop for the authorized account.")
    shop_id = str(result.get("shop_id", ""))
    if not re.fullmatch(r"\d{1,20}", shop_id) or shop_id == "0":
        raise ConnectionErrorSafe("Shop lookup did not provide a valid shop ID.")
    return shop_id


def verify():
    key, shared, refresh = load_required()
    body = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "client_id": key,
        "refresh_token": refresh,
    }).encode("utf-8")
    req = urllib.request.Request(
        BASE + "/public/oauth/token",
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    result = get_json(req, "OAuth refresh")
    access = result.get("access_token", "") if isinstance(result, dict) else ""
    if not isinstance(access, str) or not access:
        raise ConnectionErrorSafe("Etsy did not return a usable access token.")
    print("PASS: Etsy refresh token accepted by Etsy.")
    shop_id = get_shop_id(key, shared, access)
    print("PASS: A shop was found for the authorized account.")
    print("PASS: No listing was created or changed.")
    # For later steps in the *same job* only. Do not print IDs or persist credentials.
    github_env = os.environ.get("GITHUB_ENV")
    if github_env:
        with open(github_env, "a", encoding="utf-8") as handle:
            handle.write("ETSY_RESOLVED_SHOP_ID=" + shop_id + "\n")
    return shop_id


if __name__ == "__main__":
    try:
        verify()
    except ConnectionErrorSafe as exc:
        print("FAIL: " + str(exc), file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print("FAIL: Unexpected error in the Etsy connection check (" + type(exc).__name__ + ").", file=sys.stderr)
        sys.exit(1)
