"""Create a product listing.json from known product metadata and local assets.

No AI content is invented: buyer-facing title, description, and keywords must
be supplied by the seller (or a separate verified editorial process).
"""
import argparse
import json
from pathlib import Path

from etsy_publisher.core import ValidationError, validate_product


def build_manifest(folder: Path, *, title: str, description: str, price: str,
                   taxonomy_id: int, images: list[str], files: list[str],
                   tags: list[str], publish: bool = False) -> Path:
    manifest = folder / 'listing.json'
    if manifest.exists():
        raise ValidationError('listing.json already exists; refusing to overwrite.')
    listing = {
        'title': title, 'description': description, 'price': str(price),
        'taxonomy_id': taxonomy_id, 'quantity': 999,
        'type': 'download', 'who_made': 'i_did', 'when_made': '2020_2026',
        'tags': tags, 'images': images, 'digital_files': files,
        'auto_publish': bool(publish),
    }
    folder.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(listing, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    try:
        validate_product(folder)
    except Exception:
        manifest.unlink(missing_ok=True)
        raise
    return manifest


def main():
    ap = argparse.ArgumentParser(description='Create a validated Etsy digital listing manifest')
    ap.add_argument('--folder', type=Path, required=True)
    ap.add_argument('--title', required=True)
    ap.add_argument('--description', required=True)
    ap.add_argument('--price', required=True, help='Amount in your Etsy shop currency')
    ap.add_argument('--taxonomy-id', type=int, required=True, help='Real Etsy seller taxonomy node ID')
    ap.add_argument('--image', action='append', required=True, help='Relative file path in product folder')
    ap.add_argument('--file', action='append', required=True, help='Relative printable/download file path')
    ap.add_argument('--tag', action='append', default=[])
    ap.add_argument('--publish', action='store_true', help='Only marks intent; does not publish by itself')
    args = ap.parse_args()
    try:
        path = build_manifest(args.folder, title=args.title, description=args.description,
                              price=args.price, taxonomy_id=args.taxonomy_id,
                              images=args.image, files=args.file, tags=args.tag, publish=args.publish)
    except (ValidationError, OSError) as exc:
        ap.error(str(exc))
    print('Validated listing created:', path)


if __name__ == '__main__':
    main()
