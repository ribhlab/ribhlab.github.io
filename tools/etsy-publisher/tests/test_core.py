import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from etsy_publisher.core import ValidationError, publish, validate_product, save_json, EtsyClient, EtsyConfig


def product(tmp_path, tags=None):
    root = tmp_path / 'first-planner'
    (root / 'images').mkdir(parents=True)
    (root / 'files').mkdir()
    (root / 'images' / 'cover.jpg').write_bytes(b'fake image')
    (root / 'files' / 'planner.pdf').write_bytes(b'fake pdf')
    (root / 'listing.json').write_text(json.dumps({
        'title': 'Example Weekly Planner', 'description': 'A sample.', 'price': '4.99',
        'taxonomy_id': 100, 'tags': tags or ['digital planner'],
        'type': 'download', 'images': ['images/cover.jpg'],
        'digital_files': ['files/planner.pdf']
    }))
    return root


def test_valid(tmp_path):
    root = product(tmp_path)
    assert validate_product(root)['title'] == 'Example Weekly Planner'


def test_no_path_traversal(tmp_path):
    root = product(tmp_path)
    p = root / 'listing.json'
    d = json.loads(p.read_text())
    d['images'] = ['../../secret.png']
    p.write_text(json.dumps(d))
    with pytest.raises(ValidationError):
        validate_product(root)


def test_validation_tags(tmp_path):
    root = product(tmp_path, tags=['long tag that exceeds 20 characters'])
    with pytest.raises(ValidationError):
        validate_product(root)


def test_publish_idempotent(tmp_path):
    root = product(tmp_path)
    reg = tmp_path / 'registry.json'
    client = MagicMock()
    client.draft.return_value = {'listing_id': 12345}
    client.update.return_value = {'state': 'active'}
    result = publish(root, client, reg, activate=False)
    assert result['status'] == 'draft'
    assert client.draft.call_count == 1
    assert client.upload_image.call_count == 1
    assert client.upload_file.call_count == 1
    result = publish(root, client, reg, activate=True)
    assert result['status'] == 'published'
    assert client.draft.call_count == 1
    assert client.upload_image.call_count == 1
    assert client.upload_file.call_count == 1
    assert client.update.call_args.kwargs == {'state': 'active'}
    assert publish(root, client, reg, activate=True)['status'] == 'already_published'
    assert client.draft.call_count == 1


def test_failure_and_resume(tmp_path):
    root = product(tmp_path)
    reg = tmp_path / 'registry.json'
    client = MagicMock()
    client.draft.return_value = {'listing_id': 88}
    client.update.return_value = {'state': 'active'}
    client.upload_file.side_effect = RuntimeError('simulated connection failure')
    with pytest.raises(RuntimeError):
        publish(root, client, reg, activate=True)
    assert json.loads(reg.read_text())['first-planner']['listing_id'] == 88
    client.upload_file.side_effect = None
    publish(root, client, reg, activate=True)
    assert client.draft.call_count == 1
    assert client.upload_image.call_count == 1
    assert client.upload_file.call_count == 2


def test_form_fields_tags():
    sess = MagicMock()
    sess.request.return_value.status_code = 200
    sess.request.return_value.json.return_value = {'listing_id': 1}
    client = EtsyClient(EtsyConfig('key', 'secret', '321', 'refresh'), sess)
    client.access_token = 'token'
    client.expiry = 10**12
    client.draft({'quantity': 1, 'title': 'Title', 'description': 'Description',
                  'price': '5.00', 'taxonomy_id': 100, 'tags': ['first tag', 'second']})
    assert sess.request.call_args.kwargs['data']['tags'] == 'first tag,second'
    assert sess.request.call_args.kwargs['data']['type'] == 'download'


def test_unsupported_image_extension(tmp_path):
    root = product(tmp_path)
    (root / 'images' / 'cover.webp').write_bytes(b'sample')
    manifest = root / 'listing.json'
    info = json.loads(manifest.read_text())
    info['images'] = ['images/cover.webp']
    manifest.write_text(json.dumps(info))
    with pytest.raises(ValidationError, match='Unsupported image'):
        validate_product(root)


def test_callback_state_and_shop_results(tmp_path, monkeypatch):
    import time
    from etsy_publisher.__main__ import oauth_finish

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('ETSY_KEYSTRING', 'test-client-key')
    monkeypatch.setenv('ETSY_SHARED_SECRET', 'test-shared-secret')
    redirect = 'https://ribhlab.github.io/ar/etsy-oauth-callback.html'
    monkeypatch.setenv('ETSY_REDIRECT_URI', redirect)
    pending = {'state': 'expected-state', 'verifier': 'secret-verifier', 'created_at': int(time.time()), 'redirect': redirect}
    save_json(tmp_path / '.state' / 'oauth_pending.json', pending)

    def make_response(data):
        reply = MagicMock()
        reply.status_code = 200
        reply.ok = True
        reply.json.return_value = data
        return reply

    import etsy_publisher.__main__ as cli
    monkeypatch.setattr(cli.requests, 'post', lambda *args, **kw: make_response({'access_token': '123456.access', 'refresh_token': 'a-refresh-token'}))
    monkeypatch.setattr(cli.requests, 'get', lambda *args, **kw: make_response({'results': [{'shop_id': 987654}]}))
    with pytest.raises(ValidationError, match='Invalid OAuth state'):
        oauth_finish(redirect + '?code=aaa&state=wrong')
    assert (tmp_path / '.state' / 'oauth_pending.json').exists()
    oauth_finish(redirect + '?code=aaa&state=expected-state')
    stored = json.loads((tmp_path / '.state' / 'oauth_tokens.json').read_text())
    assert stored['shop_id'] == '987654'
    assert stored['refresh_token'] == 'a-refresh-token'
    assert not (tmp_path / '.state' / 'oauth_pending.json').exists()
