"""Offline guardrails for 2026-11-19 free Play localization rollout."""
from __future__ import annotations

import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("free_play_locales", ROOT / "organic_localizations.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class FakeCall:
    def __init__(self, value=None):
        self.value = value or {}
    def execute(self):
        return self.value


class FakeListings:
    def __init__(self, current=None):
        self.current = current or []
        self.updated = []
    def list(self, **kw):
        return FakeCall({"listings": self.current})
    def update(self, **kw):
        self.updated.append(kw)
        return FakeCall()


class FakeEdits:
    def __init__(self, existing=None):
        self.listing = FakeListings(existing)
        self.validated = False
        self.committed = False
        self.deleted = False
    def insert(self, **kw):
        return FakeCall({"id": "temp"})
    def listings(self):
        return self.listing
    def validate(self, **kw):
        self.validated = True
        return FakeCall()
    def commit(self, **kw):
        self.committed = True
        return FakeCall()
    def delete(self, **kw):
        self.deleted = True
        return FakeCall()


class FakeApi:
    def __init__(self, existing=None):
        self.e = FakeEdits(existing)
    def edits(self):
        return self.e


class Tests(unittest.TestCase):
    def test_every_locale_and_description_within_play_limits(self):
        apps = mod.load_and_validate()
        self.assertEqual(set(apps), mod.ALLOW_APPS)
        for app, locales in apps.items():
            self.assertEqual(set(locales), mod.ALLOW_LOCALES)
            for lang, data in locales.items():
                self.assertIn("TradingFiew" if "tradingfiew" in app else "NovaGrid",
                              data["title"])
                for field, limit in mod.FIELDS:
                    self.assertTrue(0 < len(data[field]) <= limit, (app, lang, field))
                self.assertNotIn("100%", data["fullDescription"])

    def test_existing_locale_is_not_replaced(self):
        api = FakeApi([{"language": "de-DE"}])
        result = mod.apply_to_package(
            "com.novagrid.cosmicpuzzle", {
                "de-DE": {"title": "New", "shortDescription": "X", "fullDescription": "Y"},
                "es-ES": {"title": "New", "shortDescription": "X", "fullDescription": "Y"}
            }, api
        )
        self.assertEqual([v["language"] for v in api.e.listing.updated], ["es-ES"])
        self.assertTrue(api.e.validated)
        self.assertTrue(api.e.committed)
        self.assertFalse(api.e.deleted)
        self.assertTrue(result["reviewMayStillBePending"])

    def test_all_existing_means_no_changes_and_temp_edit_is_cleaned(self):
        api = FakeApi([{"language": "it-IT"}])
        result = mod.apply_to_package(
            "com.ribhlab.tradingfiew",
            {"it-IT": {"title": "Ignored", "shortDescription": "X", "fullDescription": "Y"}},
            api
        )
        self.assertEqual(result["result"], "NO_CHANGE")
        self.assertEqual(api.e.listing.updated, [])
        self.assertFalse(api.e.committed)
        self.assertTrue(api.e.deleted)


if __name__ == "__main__":
    unittest.main()
