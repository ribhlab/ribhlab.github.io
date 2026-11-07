"""Offline tests for Google Play store listing payloads."""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location("rivoscan_listing", ROOT / "publish_listing.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class ListingTests(unittest.TestCase):
    def setUp(self):
        self.path = ROOT / "store-listings/rivoscan.json"

    def test_three_locales_and_char_limits(self):
        data = mod.load(self.path)
        self.assertEqual(set(data["locales"]), {"en-US", "fr-FR", "ar", "es-ES", "de-DE", "pt-BR", "it-IT"})
        self.assertEqual(data["appId"], mod.PACKAGE)

    def test_real_icon_dimensions(self):
        icon = ROOT / "store-listings/assets/rivoscan-icon.png"
        self.assertEqual(mod.verify_icon(icon), icon)

    def test_owner_green_icon_and_feature_match_uploaded_package(self):
        icon = ROOT / "store-listings/assets/rivoscan-icon.png"
        graphic = ROOT / "store-listings/assets/rivoscan-owner-feature-1024x500.jpg"
        self.assertEqual(mod.verify_icon(icon), icon)
        self.assertEqual(mod.verify_feature(graphic), graphic)
        listing = mod.load(self.path)
        self.assertEqual(listing["locales"]["en-US"]["title"], "RivoScan")
        self.assertIn("Smart document scanning", listing["locales"]["en-US"]["shortDescription"])

    def test_too_long_title_rejected(self):
        data = mod.load(self.path)
        data["locales"]["en-US"]["title"] = "x" * 31
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "listing.json"
            f.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(ValueError):
                mod.load(f)

    def test_untrusted_package_rejected(self):
        data = mod.load(self.path)
        data["appId"] = "com.other.application"
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / "listing.json"
            f.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(ValueError):
                mod.load(f)

    def test_default_does_not_call_google(self):
        with patch.object(mod, "apply_listings") as call:
            self.assertEqual(mod.main(["--file", str(self.path)]), 0)
            call.assert_not_called()

    def test_apply_needs_confirmation(self):
        with patch.object(mod, "apply_listings") as call:
            self.assertEqual(mod.main(["--file", str(self.path), "--apply"]), 1)
            call.assert_not_called()


if __name__ == "__main__":
    unittest.main()
