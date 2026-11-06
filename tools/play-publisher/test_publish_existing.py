"""Safety tests for existing-bundle release workflow."""
import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location("existing_bundle_publisher", ROOT / "publish_existing.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ExistingBundleTests(unittest.TestCase):
    def args(self, *extra):
        return module.parser().parse_args([
            "--package", "com.ribhlab.rivoscan", "--version-code", "81", *extra
        ])

    def test_default_only_draft_and_internal(self):
        a = self.args("--dry-run")
        module.validate(a)
        self.assertEqual((a.track, a.status), ("internal", "draft"))

    def test_no_commit_without_explicit_confirmation(self):
        with self.assertRaisesRegex(ValueError, "COMMIT"):
            module.validate(self.args())

    def test_production_requires_both_confirmations(self):
        with self.assertRaisesRegex(ValueError, "PUBLISH"):
            module.validate(self.args("--track", "production", "--status", "completed", "--confirm-commit", "COMMIT"))
        module.validate(self.args("--track", "production", "--status", "completed",
                                  "--confirm-commit", "COMMIT", "--confirm-production", "PUBLISH"))

    def test_invalid_version_code(self):
        with self.assertRaises(ValueError):
            module.validate(self.args("--version-code", "0", "--dry-run"))

    def test_inventory_version_codes(self):
        self.assertEqual(module.uploaded_versions({"bundles": [{"versionCode": 81}, {"versionCode": 3}]}), {"81", "3"})

    def test_offline_dry_run_never_calls_api(self):
        with patch.object(module, "perform") as op:
            self.assertEqual(module.main(["--package", "com.ribhlab.rivoscan",
                                          "--version-code", "81", "--dry-run"]), 0)
            op.assert_not_called()

    def test_unsupported_unuploaded_version_rejected_and_edit_deleted(self):
        a = self.args("--confirm-commit", "COMMIT")
        edits = MagicMock()
        edits.insert.return_value.execute.return_value = {"id": "test-edit"}
        edits.bundles.return_value.list.return_value.execute.return_value = {"bundles": []}
        service = MagicMock()
        service.edits.return_value = edits
        with patch.object(module, "get_credentials", return_value=object()), \
             patch("googleapiclient.discovery.build", return_value=service):
            with self.assertRaisesRegex(ValueError, "not visible"):
                module.perform(a)
        edits.tracks.return_value.update.assert_not_called()
        edits.commit.assert_not_called()
        edits.delete.return_value.execute.assert_called_once()


if __name__ == "__main__":
    unittest.main()
