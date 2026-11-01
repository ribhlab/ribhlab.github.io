"""Command-line entry point for local publishing and GitHub Actions."""
import argparse
import base64
import hashlib
import json
import os
import secrets
import sys
import time
from pathlib import Path
from urllib.parse import urlencode, urlparse, parse_qs

import requests
from dotenv import load_dotenv
from .core import EtsyClient, EtsyConfig, EtsyError, ValidationError, publish, validate_product, save_json


def oauth_start():
    load_dotenv()
    key = os.getenv('ETSY_KEYSTRING', '').strip()
    redirect = os.getenv('ETSY_REDIRECT_URI', '').strip()
    if not key or not redirect.startswith('https://'):
        raise ValidationError('Set ETSY_KEYSTRING and an HTTPS ETSY_REDIRECT_URI in .env')
    verifier = secrets.token_urlsafe(48)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()
    state = secrets.token_urlsafe(24)
    save_json(Path('.state/oauth_pending.json'), {'state': state, 'verifier': verifier,
               'created_at': int(time.time()), 'redirect': redirect})
    q = urlencode({'response_type': 'code', 'client_id': key, 'redirect_uri': redirect,
                   'scope': 'listings_r listings_w shops_r', 'state': state,
                   'code_challenge': challenge, 'code_challenge_method': 'S256'})
    print('Open this URL in your browser, approve Etsy permissions, then copy the final URL:')
    print('https://www.etsy.com/oauth/connect?' + q)
    print('\nRun: python -m etsy_publisher auth-finish --url "PASTE_FULL_CALLBACK_URL"')


def oauth_finish(redirected_url: str):
    load_dotenv()
    p = Path('.state/oauth_pending.json')
    if not p.is_file():
        raise ValidationError('No pending OAuth request. Run auth-start first.')
    pending = json.loads(p.read_text())
    if time.time() - pending['created_at'] > 600:
        raise ValidationError('OAuth request expired. Run auth-start again.')
    # Do not accept callback from another domain/path; query is allowed.
    got = urlparse(redirected_url)
    expected = urlparse(pending['redirect'])
    if (got.scheme, got.netloc, got.path) != (expected.scheme, expected.netloc, expected.path):
        raise ValidationError('Callback URL does not match ETSY_REDIRECT_URI')
    q = parse_qs(got.query)
    if q.get('state', [''])[0] != pending['state']:
        raise ValidationError('Invalid OAuth state')
    if 'error' in q:
        raise EtsyError('Etsy authorization declined: ' + q['error'][0])
    code = q.get('code', [''])[0]
    if not code:
        raise ValidationError('Callback URL did not include code')
    r = requests.post('https://api.etsy.com/v3/public/oauth/token', data={
        'grant_type': 'authorization_code', 'client_id': os.environ['ETSY_KEYSTRING'],
        'redirect_uri': pending['redirect'], 'code': code,
        'code_verifier': pending['verifier']}, timeout=30)
    data = EtsyClient.check(r)
    if 'refresh_token' not in data:
        raise EtsyError('No refresh_token in Etsy response')
    output = Path('.state/oauth_tokens.json')
    stored = {'refresh_token': data['refresh_token'], 'connected_at': int(time.time())}
    user_id = data.get('access_token', '').split('.')[0]
    if user_id.isdigit():
        response = requests.get(f'https://api.etsy.com/v3/application/users/{user_id}/shops',
                                headers={'x-api-key': os.environ['ETSY_KEYSTRING'] + ':' + os.environ['ETSY_SHARED_SECRET'],
                                         'Authorization': 'Bearer ' + data['access_token']}, timeout=30)
        if response.ok:
            shop = response.json()
            # getUserShops commonly returns a {results: [...]} envelope,
            # not a top-level shop_id.
            candidates = shop.get('results', []) if isinstance(shop, dict) else []
            if not candidates and isinstance(shop, dict) and shop.get('shop_id'):
                candidates = [shop]
            if candidates and isinstance(candidates[0], dict) and candidates[0].get('shop_id'):
                stored['shop_id'] = str(candidates[0]['shop_id'])
                print('Your Etsy shop ID:', candidates[0]['shop_id'])
        else:
            print('Shop ID lookup was unavailable. Find your numeric shop ID in Etsy API or shop settings.')
    save_json(output, stored)
    try:
        os.chmod(output, 0o600)
    except OSError:
        pass
    p.unlink()
    print('Etsy linked successfully. Refresh token saved privately to .state/oauth_tokens.json')
    print('Set ETSY_REFRESH_TOKEN locally or in GitHub Actions Secrets. Never upload tokens to a repository or chat.')
    print('If Etsy returned your shop ID, configure ETSY_SHOP_ID with that numeric value.')


def main():
    parser = argparse.ArgumentParser(description='Digital Etsy publisher; no Vela subscription')
    subs = parser.add_subparsers(dest='command', required=True)
    subs.add_parser('auth-start')
    finish = subs.add_parser('auth-finish')
    finish.add_argument('--url', required=False, help='Full redirected URL; omit to paste privately')
    check = subs.add_parser('validate')
    check.add_argument('--product', required=True)
    run = subs.add_parser('publish')
    run.add_argument('--product', required=True)
    run.add_argument('--activate', action='store_true', help='Make listing public (Etsy may charge a listing fee)')
    run.add_argument('--registry', default='.state/registry.json')
    args = parser.parse_args()
    try:
        if args.command == 'auth-start':
            oauth_start()
        elif args.command == 'auth-finish':
            if args.url:
                oauth_finish(args.url)
            else:
                from getpass import getpass
                oauth_finish(getpass('Paste the full HTTPS callback URL here: '))
        elif args.command == 'validate':
            obj = validate_product(Path(args.product))
            print('VALID:', obj['title'])
        else:
            load_dotenv()
            if not os.getenv('ETSY_REFRESH_TOKEN'):
                token_path = Path('.state/oauth_tokens.json')
                if token_path.is_file():
                    os.environ['ETSY_REFRESH_TOKEN'] = json.loads(token_path.read_text())['refresh_token']
            result = publish(Path(args.product), EtsyClient(EtsyConfig.from_env()),
                             Path(args.registry), activate=args.activate)
            print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValidationError, EtsyError, requests.RequestException, OSError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
