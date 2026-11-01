"""Etsy Open API v3 digital listing publisher.

The publisher deliberately creates a draft, uploads assets, then optionally
activates the listing. A durable local registry helps avoid duplicate drafts.
"""
from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import re
import time
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import requests

BASE = 'https://api.etsy.com/v3'
MAX_FILE = 20 * 1024 * 1024  # Etsy digital file maximum
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif'}
SLUG_RE = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9_-]{0,79}$')


class EtsyError(Exception):
    pass


class ValidationError(Exception):
    pass


def save_json(path: Path, value: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    os.replace(tmp, path)


def safe_asset(folder: Path, raw: str) -> Path:
    if not isinstance(raw, str) or raw.startswith(('/', '\\')):
        raise ValidationError(f'Invalid asset path: {raw!r}')
    root = folder.resolve()
    p = (root / raw).resolve()
    if not p.is_relative_to(root) or not p.is_file() or p.is_symlink():
        raise ValidationError(f'Asset missing or outside product directory: {raw}')
    return p


def validate_product(folder: Path) -> dict:
    folder = Path(folder)
    if not SLUG_RE.fullmatch(folder.name):
        raise ValidationError('Product directory must be a safe ASCII slug (letters, digits, _ or -).')
    p = folder / 'listing.json'
    if not p.is_file():
        raise ValidationError(f'Missing {p}')
    try:
        obj = json.loads(p.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise ValidationError(f'Invalid JSON: {exc}') from exc
    if not isinstance(obj, dict):
        raise ValidationError('listing.json must be a JSON object')
    title = obj.get('title', '')
    if not isinstance(title, str) or not (3 <= len(title) <= 140):
        raise ValidationError('title must be 3-140 characters')
    desc = obj.get('description')
    if not isinstance(desc, str) or not desc.strip():
        raise ValidationError('description is required')
    try:
        price = Decimal(str(obj.get('price', '')))
    except InvalidOperation as exc:
        raise ValidationError('price must be a number in the shop currency') from exc
    if not price.is_finite() or price <= 0:
        raise ValidationError('price must be > 0')
    try:
        taxonomy = int(obj.get('taxonomy_id', 0))
        qty = int(obj.get('quantity', 999))
    except (ValueError, TypeError) as exc:
        raise ValidationError('taxonomy_id and quantity must be integers') from exc
    if taxonomy < 1 or qty < 1:
        raise ValidationError('taxonomy_id and quantity must be positive')
    tags = obj.get('tags', [])
    if not isinstance(tags, list) or len(tags) > 13 or any(not isinstance(x, str) or not (1 <= len(x) <= 20) or ',' in x for x in tags):
        raise ValidationError('tags must contain no more than 13 strings, each 1-20 chars without commas')
    # Only a few other characters are legal in Etsy tags; reject typical invalid separators.
    if any(re.search(r'[^\w\s\-\'™©®]', x, re.UNICODE) for x in tags):
        raise ValidationError('tags contain characters Etsy does not accept')
    if any('_' in x or '\n' in x or '\r' in x for x in tags):
        raise ValidationError('Underscore or newlines are not allowed in Etsy tags')
    if len(set(x.strip().casefold() for x in tags)) != len(tags):
        raise ValidationError('Duplicate tags are not allowed')
    if obj.get('type', 'download') != 'download':
        raise ValidationError('This version supports instant digital downloads only')
    if 'auto_publish' in obj and not isinstance(obj['auto_publish'], bool):
        raise ValidationError('auto_publish must be true or false')
    images = obj.get('images', [])
    digital = obj.get('digital_files', [])
    if not isinstance(images, list) or not (1 <= len(images) <= 20):
        raise ValidationError('1-20 listing images are required')
    if not isinstance(digital, list) or not (1 <= len(digital) <= 5):
        raise ValidationError('1-5 digital files are required')
    if any(not isinstance(x, str) for x in images + digital):
        raise ValidationError('Asset paths must be strings')
    if len(set(images + digital)) != len(images + digital):
        raise ValidationError('Do not reuse the same file path within a listing')
    for relative in images:
        path = safe_asset(folder, relative)
        if path.suffix.lower() not in IMAGE_EXTENSIONS:
            raise ValidationError(f'Unsupported image extension: {path.name}')
        if path.stat().st_size == 0 or path.stat().st_size > MAX_FILE:
            raise ValidationError(f'Image is empty or over 20 MiB: {path.name}')
    for relative in digital:
        path = safe_asset(folder, relative)
        if path.suffix.lower() not in {'.pdf', '.zip', '.png', '.jpg', '.jpeg', '.svg', '.eps', '.txt', '.doc', '.docx', '.gif', '.psd', '.ai', '.stl', '.csv', '.mp3', '.mp4'}:
            raise ValidationError(f'Unsupported digital file extension: {path.name}')
        if path.stat().st_size == 0 or path.stat().st_size > MAX_FILE:
            raise ValidationError(f'Digital file empty or over 20 MiB: {path.name}')
    who_made = obj.get('who_made', 'i_did')
    when_made = obj.get('when_made', '2020_2026')
    if who_made not in ('i_did', 'someone_else', 'collective'):
        raise ValidationError('Invalid who_made')
    if when_made not in ('2020_2026', '2010_2019', '2007_2009', 'before_2007', 'made_to_order'):
        raise ValidationError('Set a valid when_made period')
    return obj


def asset_digest(folder: Path, relative: str) -> str:
    h = hashlib.sha256()
    with safe_asset(folder, relative).open('rb') as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


@dataclass
class EtsyConfig:
    keystring: str
    shared_secret: str
    shop_id: str
    refresh_token: str

    @classmethod
    def from_env(cls) -> 'EtsyConfig':
        from dotenv import load_dotenv
        load_dotenv()
        vals = {k: os.environ.get(k, '').strip() for k in
                ('ETSY_KEYSTRING', 'ETSY_SHARED_SECRET', 'ETSY_SHOP_ID', 'ETSY_REFRESH_TOKEN')}
        missing = [k for k, v in vals.items() if not v]
        if missing:
            raise EtsyError('Missing environment settings: ' + ', '.join(missing))
        if not vals['ETSY_SHOP_ID'].isdigit():
            raise EtsyError('ETSY_SHOP_ID must be numeric')
        return cls(vals['ETSY_KEYSTRING'], vals['ETSY_SHARED_SECRET'], vals['ETSY_SHOP_ID'], vals['ETSY_REFRESH_TOKEN'])


class EtsyClient:
    def __init__(self, config: EtsyConfig, session: requests.Session | None = None):
        self.config = config
        self.session = session or requests.Session()
        self.access_token = ''
        self.expiry = 0.0

    def headers(self) -> dict:
        if not self.access_token or time.time() > self.expiry - 60:
            self.refresh()
        return {'x-api-key': f'{self.config.keystring}:{self.config.shared_secret}',
                'Authorization': f'Bearer {self.access_token}'}

    @staticmethod
    def check(response: requests.Response) -> dict:
        if response.status_code >= 400:
            try:
                detail = response.json()
                message = detail.get('error') or detail.get('message') or detail
            except (ValueError, AttributeError):
                message = response.text[:400]
            raise EtsyError(f'Etsy HTTP {response.status_code}: {str(message)[:450]}')
        try:
            return response.json()
        except ValueError as exc:
            raise EtsyError('Etsy returned invalid JSON') from exc

    def refresh(self):
        r = self.session.post(f'{BASE}/public/oauth/token', data={
            'grant_type': 'refresh_token', 'client_id': self.config.keystring,
            'refresh_token': self.config.refresh_token}, timeout=30)
        d = self.check(r)
        self.access_token = d['access_token']
        self.expiry = time.time() + int(d.get('expires_in', 3600))
        # In case Etsy rotates refresh tokens, persist when running in a local env.
        # On GitHub Actions, a changed refresh token requires updating the secret.
        if d.get('refresh_token') and d['refresh_token'] != self.config.refresh_token:
            self.config.refresh_token = d['refresh_token']
            path = Path('.state/oauth_tokens.json')
            if path.is_file():
                try:
                    tokens = json.loads(path.read_text(encoding='utf-8'))
                    tokens['refresh_token'] = d['refresh_token']
                    save_json(path, tokens)
                    os.chmod(path, 0o600)
                except (ValueError, OSError):
                    pass
            else:
                print('NOTICE: Etsy may have rotated the refresh token. Reauthorize if the GitHub secret expires.')

    def request(self, method: str, path: str, *, data=None, files=None) -> dict:
        r = self.session.request(method, BASE + path, headers=self.headers(),
                                 data=data, files=files, timeout=90)
        return self.check(r)

    def draft(self, product: dict) -> dict:
        form = {
            'quantity': str(product.get('quantity', 999)),
            'title': product['title'],
            'description': product['description'],
            'price': str(product['price']),
            'who_made': product.get('who_made', 'i_did'),
            'when_made': product.get('when_made', '2020_2026'),
            'taxonomy_id': str(product['taxonomy_id']),
            'is_supply': 'false', 'type': 'download',
            'should_auto_renew': 'false',
        }
        if product.get('tags'):
            form['tags'] = ','.join(product['tags'])
        if product.get('shop_section_id'):
            form['shop_section_id'] = str(product['shop_section_id'])
        return self.request('POST', f'/application/shops/{self.config.shop_id}/listings', data=form)

    def upload_image(self, listing_id: int, path: Path, rank: int):
        with path.open('rb') as fh:
            return self.request('POST', f'/application/shops/{self.config.shop_id}/listings/{listing_id}/images',
                data={'rank': str(rank)}, files={'image': (path.name, fh, mimetypes.guess_type(path.name)[0] or 'application/octet-stream')})

    def upload_file(self, listing_id: int, path: Path):
        with path.open('rb') as fh:
            return self.request('POST', f'/application/shops/{self.config.shop_id}/listings/{listing_id}/files',
                data={'name': path.name}, files={'file': (path.name, fh, mimetypes.guess_type(path.name)[0] or 'application/octet-stream')})

    def update(self, listing_id: int, **fields):
        return self.request('PATCH', f'/application/shops/{self.config.shop_id}/listings/{listing_id}', data=fields)


def publish(folder: Path, client: EtsyClient, registry_path: Path, activate: bool = False) -> dict:
    folder = Path(folder)
    product = validate_product(folder)
    if registry_path.is_file():
        registry = json.loads(registry_path.read_text(encoding='utf-8'))
    else:
        registry = {}
    sku = folder.name
    entry = registry.get(sku)
    if entry:
        # Prevent reuse of an existing SKU for a totally different product.
        if entry.get('title') != product['title']:
            raise ValidationError('Existing SKU has a different title. Use a new product directory.')
    else:
        result = client.draft(product)
        if 'listing_id' not in result:
            raise EtsyError('Draft response omitted listing_id')
        entry = {'listing_id': int(result['listing_id']), 'title': product['title'],
                 'status': 'draft', 'assets': {}, 'type_set': False}
        registry[sku] = entry
        save_json(registry_path, registry)   # Save before first upload.
    if entry['status'] == 'published':
        return {'sku': sku, 'status': 'already_published', 'listing_id': entry['listing_id'],
                'url': f'https://www.etsy.com/listing/{entry["listing_id"]}'}
    lid = entry['listing_id']
    for idx, relative in enumerate(product['images'], start=1):
        sha = asset_digest(folder, relative)
        previous = entry['assets'].get(relative)
        if previous and previous != sha:
            raise ValidationError(f'File changed after first upload: {relative}; use a new SKU')
        if not previous:
            client.upload_image(lid, safe_asset(folder, relative), idx)
            entry['assets'][relative] = sha
            save_json(registry_path, registry)
    for relative in product['digital_files']:
        sha = asset_digest(folder, relative)
        previous = entry['assets'].get(relative)
        if previous and previous != sha:
            raise ValidationError(f'File changed after first upload: {relative}; use a new SKU')
        if not previous:
            client.upload_file(lid, safe_asset(folder, relative))
            entry['assets'][relative] = sha
            save_json(registry_path, registry)
    if not entry['type_set']:
        client.update(lid, type='download')
        entry['type_set'] = True
        save_json(registry_path, registry)
    if activate:
        response = client.update(lid, state='active')
        if response.get('state') and response['state'] != 'active':
            raise EtsyError(f'Etsy did not activate listing {lid}: {response["state"]}')
        entry['status'] = 'published'
        save_json(registry_path, registry)
    return {'sku': sku, 'status': entry['status'], 'listing_id': lid,
            'url': f'https://www.etsy.com/listing/{lid}'}
