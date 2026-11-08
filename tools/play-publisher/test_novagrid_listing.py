"""Offline checks for NovaGrid Play listing upload: owner art, correct app, safe scope."""
import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location("novagrid_listing", HERE / "novagrid_listing.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class NovaGridPlayTests(unittest.TestCase):
    def test_owner_art_and_localizations(self):
        info = m.load_metadata()
        self.assertEqual(info["appId"], "com.novagrid.cosmicpuzzle")
        self.assertEqual(set(info["locales"]), {"en-US", "fr-FR", "ar"})
        assets = m.verified_artwork()
        self.assertEqual(len(assets), 9)
        self.assertEqual(len(assets["icon"]), 267648)

    def test_dry_run_not_connected_to_google(self):
        self.assertEqual(m.main([]), 0)

    def test_no_release_track_or_aab_write(self):
        from inspect import getsource
        body = getsource(m.apply_listing)
        self.assertNotIn("bundles().upload(", body)
        self.assertNotIn("tracks().update(", body)
        self.assertNotIn("edits.rollouts(", body)

    def test_invalid_owner_confirmation_cannot_publish(self):
        self.assertEqual(m.main(["--apply", "--confirm", "PUBLISH"]), 1)


if __name__ == "__main__":
    unittest.main()
