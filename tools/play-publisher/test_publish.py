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


if __name__ == "__main__":
    unittest.main()
