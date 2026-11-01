import json
from pathlib import Path

import pytest

from scripts.create_listing import build_manifest
from etsy_publisher.core import ValidationError


def test_build_manifest(tmp_path):
    root = tmp_path / 'wall-art-test'
    (root / 'images').mkdir(parents=True)
    (root / 'files').mkdir()
    (root / 'images' / 'preview.png').write_bytes(b'preview')
    (root / 'files' / 'wall-art.pdf').write_bytes(b'%PDF-1.7\nexample')
    p = build_manifest(root, title='Modern geometric printable wall art',
                       description='Printable artwork. Digital download, no physical item shipped.',
                       price='5.00', taxonomy_id=1234, images=['images/preview.png'],
                       files=['files/wall-art.pdf'], tags=['wall art', 'printable art'])
    assert json.loads(p.read_text())['type'] == 'download'
    with pytest.raises(ValidationError):
        build_manifest(root, title='duplicate', description='no', price='5.00', taxonomy_id=1,
                       images=['images/preview.png'], files=['files/wall-art.pdf'], tags=[])


def test_invalid_manifest_not_left(tmp_path):
    root=tmp_path/'bad-art'
    root.mkdir()
    with pytest.raises(ValidationError):
        build_manifest(root, title='Wall art', description='Digital art', price='0', taxonomy_id=1,
                       images=['missing.png'], files=['missing.pdf'], tags=[])
    assert not (root / 'listing.json').exists()
