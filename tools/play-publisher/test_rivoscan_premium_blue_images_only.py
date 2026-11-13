"""Regression guards for the RivoScan store-graphics-only deployment."""
from __future__ import annotations

import importlib.util
import io
import sys
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location("blue_store", ROOT / "rivoscan_premium_blue_images_only.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class StoreOnlyTests(unittest.TestCase):
    def test_fixed_package_and_ten_assets(self):
        self.assertEqual(m.PACKAGE, "com.ribhlab.rivoscan")
        self.assertEqual(m.LANGUAGE, "en-US")
        self.assertEqual(len(m.ASSET_SHA256), 10)
        self.assertEqual(len(m.SLOTS["phoneScreenshots"]), 8)
        self.assertEqual(m.SLOTS["icon"], ("App_Icon_512x512.png",))
        self.assertEqual(m.SLOTS["featureGraphic"], ("Feature_Graphic_1024x500.png",))
        self.assertEqual(len(m.EXPECTED_ARCHIVE_SHA256), 64)

    def test_each_image_used_exactly_once(self):
        selected = [item for group in m.SLOTS.values() for item in group]
        self.assertEqual(len(selected), 10)
        self.assertEqual(set(selected), set(m.ASSET_SHA256))

    def test_archive_wrong_bytes_rejected(self):
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            m.inspect_archive(b"not user approved asset data")

    def test_default_cannot_write_to_google(self):
        with patch.object(m, "download_from_private_drive") as drive, \
             patch.object(m, "apply_images") as publisher, \
             redirect_stdout(io.StringIO()):
            self.assertEqual(m.main([]), 0)
            drive.assert_not_called()
            publisher.assert_not_called()

    def test_confirmation_required_before_any_external_access(self):
        with patch.object(m, "download_from_private_drive") as drive, \
             patch.object(m, "apply_images") as publisher, \
             redirect_stderr(io.StringIO()):
            self.assertEqual(m.main(["--apply"]), 2)
            drive.assert_not_called()
            publisher.assert_not_called()

    def test_disallows_tampered_archive_without_google_edit(self):
        with patch.object(m, "download_from_private_drive", return_value=b"tampered zip"), \
             patch.object(m, "apply_images") as publisher, \
             redirect_stderr(io.StringIO()):
            self.assertEqual(m.main(["--apply", "--confirm", m.CONFIRM]), 1)
            publisher.assert_not_called()


if __name__ == "__main__":
    unittest.main()
