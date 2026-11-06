"""Run with python -m unittest discover tools/play-publisher -p 'test_*.py'."""
import importlib.util
import tempfile
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location("google_play_publisher", Path(__file__).with_name("publish.py"))
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.aab = Path(self.temp.name) / "app.aab"
        self.aab.write_bytes(b"fake-bundle-for-validation-only")

    def tearDown(self):
        self.temp.cleanup()

    def args(self, *extra):
        return publisher.build_parser().parse_args(
            ["--aab", str(self.aab), "--package", "com.ribhlab.demo", *extra]
        )

    def test_default_draft_internal(self):
        args = self.args()
        self.assertEqual((args.track, args.status), ("internal", "draft"))
        self.assertEqual(publisher.validate(args), self.aab.resolve())

    def test_production_requires_confirmation(self):
        with self.assertRaisesRegex(ValueError, "requires"):
            publisher.validate(self.args("--track", "production", "--status", "completed"))
        publisher.validate(self.args("--track", "production", "--status", "completed", "--confirm-production", "PUBLISH"))

    def test_invalid_package(self):
        with self.assertRaisesRegex(ValueError, "package"):
            publisher.validate(self.args("--package", "invalid"))

    def test_empty_aab(self):
        self.aab.write_bytes(b"")
        with self.assertRaisesRegex(ValueError, "empty"):
            publisher.validate(self.args())

    def test_notes_limit(self):
        with self.assertRaisesRegex(ValueError, "500"):
            publisher.validate(self.args("--notes", "a" * 501))

    def test_dry_run_needs_no_credentials(self):
        self.assertEqual(publisher.main(["--aab", str(self.aab), "--package", "com.ribhlab.demo", "--dry-run"]), 0)



    def test_draft_keeps_live_release(self):
        args = self.args()
        live = {"status": "completed", "versionCodes": ["20"]}
        versions = publisher.build_releases(args, "21", [live])
        self.assertEqual(versions, [live, {"status": "draft", "versionCodes": ["21"]}])

    def test_existing_draft_is_blocked(self):
        with self.assertRaisesRegex(ValueError, "existing draft"):
            publisher.build_releases(self.args(), "21", [{"status": "draft", "versionCodes": ["20"]}])

    def test_staged_rollout_not_overridden(self):
        args = self.args("--status", "completed")
        with self.assertRaisesRegex(ValueError, "staged"):
            publisher.build_releases(args, "21", [{"status": "inProgress", "userFraction": 0.5, "versionCodes": ["20"]}])

    def test_completed_single_aab_replaces_completed(self):
        args = self.args("--status", "completed")
        self.assertEqual(
            publisher.build_releases(args, "21", [{"status": "completed", "versionCodes": ["20"]}]),
            [{"status": "completed", "versionCodes": ["21"]}]
        )

    def test_multi_apk_needs_manual_review(self):
        args = self.args("--status", "completed")
        with self.assertRaisesRegex(ValueError, "multi-APK"):
            publisher.build_releases(args, "21", [{"status": "completed", "versionCodes": ["19", "20"]}])

    def test_internal_track_alias(self):
        class Request:
            def execute(self):
                return {"tracks": [{"track": "qa", "releases": [{"status": "completed", "versionCodes": ["3"]}]}]}
        class Tracks:
            def list(self, **kwargs):
                return Request()
        class Edits:
            def tracks(self):
                return Tracks()
        self.assertEqual(
            publisher.get_target_track(Edits(), "com.ribhlab.demo", "test-edit", "internal"),
            ("qa", [{"status": "completed", "versionCodes": ["3"]}])
        )

if __name__ == "__main__":
    unittest.main()
