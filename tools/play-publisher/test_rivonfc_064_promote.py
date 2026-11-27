#!/usr/bin/env python3
"""Offline regressions for RivoNFC exact code11 release and Google Play guard."""
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0,str(Path(__file__).resolve().parent))
import rivonfc_064_promote as app

class Code11Guards(unittest.TestCase):
    def test_staged_latest_code11_is_accepted(self):
        self.assertTrue(app.latest_bundle_guard(["9","10","11"]))
        self.assertTrue(app.latest_bundle_guard(["11"]))

    def test_old_code10_is_not_accepted(self):
        with self.assertRaisesRegex(RuntimeError,"missing"):
            app.latest_bundle_guard(["9","10"])

    def test_new_code12_blocks_publishing_stale_code11(self):
        with self.assertRaisesRegex(RuntimeError,"Newer"):
            app.latest_bundle_guard(["9","10","11","12"])

    def test_exact_production_and_internal_checks(self):
        def mock_editor(prod,internal):
            editor=MagicMock()
            editor.tracks().list().execute.return_value={"tracks":[
                {"track":"production","releases":[{"versionCodes":[prod],"status":"completed"}]},
                {"track":"internal","releases":[{"versionCodes":[internal],"status":"completed"}]},
            ]}
            return editor
        self.assertEqual(
            set(app.verify_exact_tracks(mock_editor("9","9"),{}, "9","9").keys()),
            {"production","internal"})
        self.assertEqual(
            set(app.verify_exact_tracks(mock_editor("11","9"),{}, "11","9").keys()),
            {"production","internal"})
        with self.assertRaisesRegex(RuntimeError,"Unexpected production"):
            app.verify_exact_tracks(mock_editor("12","9"),{}, "9","9")
        with self.assertRaisesRegex(RuntimeError,"Unexpected internal"):
            app.verify_exact_tracks(mock_editor("9","10"),{}, "9","9")

    def test_publication_never_cancels_existing_review(self):
        source=Path(app.__file__).read_text()
        self.assertIn('changesInReviewBehavior="ERROR_IF_IN_REVIEW"',source)
        self.assertNotIn('changesInReviewBehavior="CANCEL_IN_REVIEW"',source)
        self.assertIn('RIVONFC_064_COMPLIANCE_APPROVAL',source)
        self.assertIn('RIVONFC_064_PLAY_ADS_DATASAFETY_VERIFIED',source)

    def test_safety_overrides_never_change_other_application(self):
        self.assertEqual(app.PKG,"com.ribhlab.rivonfc")
        self.assertEqual(app.OLD,"9")
        self.assertEqual(app.NEW,"11")

if __name__=="__main__":
    unittest.main(verbosity=2)
