#!/usr/bin/env python3
"""Organic localization: add only missing accurate RivoScan listings; no media, pricing, or release edits."""
import json
from pathlib import Path
from organic_localizations import apply_to_package
from publish import get_credentials
from googleapiclient.discovery import build
source=json.loads(Path(__file__).with_name('store-listings').joinpath('rivoscan.json').read_text(encoding='utf-8'))
assert source['appId']=='com.ribhlab.rivoscan'
locales=source['locales']
assert set(locales)=={'en-US','fr-FR','ar','es-ES','de-DE','pt-BR','it-IT'}
for lang,data in locales.items():
    for field,limit in [('title',30),('shortDescription',80),('fullDescription',4000)]:
        assert 0<len(data[field])<=limit,(lang,field)
api=build('androidpublisher','v3',credentials=get_credentials(),cache_discovery=False)
print('RIVO_ORGANIC_ASO='+json.dumps(apply_to_package(source['appId'],locales,api),ensure_ascii=False),flush=True)
