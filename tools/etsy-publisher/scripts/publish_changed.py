"""Publish changed product folders on GitHub push (one job per product)."""
import json
import os
import subprocess
import sys
from pathlib import Path

from etsy_publisher.core import EtsyClient, EtsyConfig, EtsyError, ValidationError, publish, validate_product


def changed_products() -> list[Path]:
    try:
        raw = subprocess.check_output(['git', 'diff', '--name-only', 'HEAD^', 'HEAD'], text=True, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        raw = subprocess.check_output(['git', 'ls-files', 'products'], text=True)
    result = set()
    for line in raw.splitlines():
        p = Path(line)
        if len(p.parts) >= 3 and p.parts[0] == 'products' and (Path('products') / p.parts[1] / 'listing.json').is_file():
            result.add(Path('products') / p.parts[1])
    return sorted(result)


def main():
    failures = []
    for folder in changed_products():
        try:
            obj = validate_product(folder)
            activate = obj.get('auto_publish', False) is True
            result = publish(folder, EtsyClient(EtsyConfig.from_env()),
                             Path('publication_registry.json'), activate=activate)
            print(json.dumps(result))
        except (EtsyError, ValidationError, OSError, ValueError) as err:
            print(f'FAILED {folder}: {err}', file=sys.stderr)
            failures.append(str(folder))
    if failures:
        sys.exit(1)


if __name__ == '__main__':
    main()
