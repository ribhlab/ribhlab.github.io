"""Offline tests for RivoScan's strictly non-production-publishing track setup."""
import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location("rivo_stage", ROOT / "rivoscan_stage_closed_and_production.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def example(version=74, track="internal"):
    return ({"bundles": [{"versionCode": version}]}, [{
        "track": track, "releases": [{"versionCodes": [str(version)],
                                      "status": "completed"}]
    }])

class RivoStageTests(unittest.TestCase):
    def test_select_only_saved_internal_bundle(self):
        inventory, tracks = example(74)
        self.assertEqual(module.select_internal_bundle(inventory, tracks), 74)
        self.assertIsNone(module.select_internal_bundle({"bundles": []}, tracks))
        self.assertIsNone(module.select_internal_bundle(inventory, []))

    def test_custom_or_open_track_does_not_qualify_for_promotion(self):
        inventory, tracks = example(74, "beta")
        self.assertIsNone(module.select_internal_bundle(inventory, tracks))
        inventory, tracks = example(74, "production")
        self.assertIsNone(module.select_internal_bundle(inventory, tracks))

    def test_new_unsaved_bundle_is_not_selected_over_saved_internal(self):
        inventory, tracks = example(74)
        inventory["bundles"].append({"versionCode": 99})
        self.assertEqual(module.select_internal_bundle(inventory, tracks), 74)
        self.assertRaises(ValueError, module.release_request, 73, "completed")
        self.assertRaises(ValueError, module.release_request, 74, "inProgress")

    def test_real_internal_74_release_notes_and_name(self):
        a = module.release_request(74, "completed")
        self.assertEqual(a.name, "RivoScan Android 74")
        self.assertEqual(a.track, "alpha")
        self.assertEqual(a.status, "completed")

    def test_production_must_stay_draft(self):
        edits = MagicMock()
        with self.assertRaisesRegex(ValueError, "NEVER"):
            module.stage_track(edits, 99, module.PRODUCTION, "completed")
        edits.insert.assert_not_called()

    def test_beta_open_testing_is_forbidden(self):
        edits = MagicMock()
        with self.assertRaisesRegex(ValueError, "approved closed"):
            module.stage_track(edits, 99, "beta", "completed")
        edits.insert.assert_not_called()

    def test_missing_bundle_does_not_change_track(self):
        edits = MagicMock()
        edits.insert.return_value.execute.return_value = {"id": "edit1"}
        edits.bundles.return_value.list.return_value.execute.return_value = {"bundles": []}
        result = module.stage_track(edits, 99, module.CLOSED, "completed")
        self.assertEqual(result["result"], "BLOCKED_NOT_IN_BUNDLE_INVENTORY")
        edits.tracks.return_value.update.assert_not_called()
        edits.commit.assert_not_called()
        edits.delete.return_value.execute.assert_called_once()

    def test_closed_test_publishes_only_closed_track(self):
        edits = MagicMock()
        edits.insert.return_value.execute.return_value = {"id": "edit1"}
        edits.bundles.return_value.list.return_value.execute.return_value = {
            "bundles": [{"versionCode": 99}]}
        with patch.object(module, "get_target_track", return_value=("alpha", [])):
            result = module.stage_track(edits, 99, module.CLOSED, "completed")
        self.assertEqual(result["result"], "TRACK_EDIT_COMMITTED")
        details = edits.tracks.return_value.update.call_args.kwargs
        self.assertEqual(details["track"], "alpha")
        self.assertEqual(details["body"]["releases"][0]["status"], "completed")
        edits.commit.return_value.execute.assert_called_once()

    def test_existing_same_version_closed_draft_activates_as_requested(self):
        edits = MagicMock()
        edits.insert.return_value.execute.return_value = {"id": "edit1"}
        edits.bundles.return_value.list.return_value.execute.return_value = {
            "bundles": [{"versionCode": 99}]}
        with patch.object(module, "get_target_track", return_value=(
            "alpha", [{"versionCodes": ["99"], "status": "draft"}])):
            result = module.stage_track(edits, 99, module.CLOSED, "completed")
        self.assertEqual(result["result"], "TRACK_EDIT_COMMITTED")
        self.assertEqual(edits.tracks.return_value.update.call_args.kwargs[
            "body"]["releases"][0]["status"], "completed")

    def test_closed_unrelated_draft_is_not_overwritten(self):
        edits = MagicMock()
        edits.insert.return_value.execute.return_value = {"id": "edit1"}
        edits.bundles.return_value.list.return_value.execute.return_value = {
            "bundles": [{"versionCode": 99}]}
        with patch.object(module, "get_target_track", return_value=(
            "alpha", [{"versionCodes": ["98"], "status": "draft"}])):
            with self.assertRaisesRegex(ValueError, "draft"):
                module.stage_track(edits, 99, module.CLOSED, "completed")
        edits.commit.assert_not_called()

    def test_same_version_completed_closed_track_is_idempotent(self):
        edits = MagicMock()
        edits.insert.return_value.execute.return_value = {"id": "edit1"}
        edits.bundles.return_value.list.return_value.execute.return_value = {
            "bundles": [{"versionCode": 99}]}
        with patch.object(module, "get_target_track", return_value=(
            "alpha", [{"versionCodes": ["99"], "status": "completed"}])):
            result = module.stage_track(edits, 99, module.CLOSED, "completed")
        self.assertEqual(result["result"], "ALREADY_ON_TRACK")
        edits.commit.assert_not_called()

    def test_empty_production_placeholder_can_be_filled_as_draft(self):
        edits = MagicMock()
        edits.insert.return_value.execute.return_value = {"id": "edit1"}
        edits.bundles.return_value.list.return_value.execute.return_value = {
            "bundles": [{"versionCode": 99}]}
        with patch.object(module, "get_target_track", return_value=(
            "production", [{"versionCodes": [], "status": "draft"}])):
            result = module.stage_track(edits, 99, module.PRODUCTION, "draft")
        self.assertEqual(result["result"], "TRACK_EDIT_COMMITTED")
        self.assertEqual(edits.tracks.return_value.update.call_args.kwargs[
            "body"]["releases"][0]["status"], "draft")

    def test_closed_failure_attempts_nonpublic_production_draft(self):
        def fake_stage(_edits, code, track, status):
            return {"track": track, "status": status, "result": "BLOCKED" if track == "alpha" else "TRACK_EDIT_COMMITTED"}
        with patch.object(module, "get_credentials", return_value=None), \
             patch.dict(sys.modules, {"googleapiclient": MagicMock(),
                                     "googleapiclient.discovery": MagicMock()}), \
             patch.object(module, "stage_track", side_effect=fake_stage) as fake:
            result = module.deploy(74)
        self.assertEqual(fake.call_count, 3)
        self.assertEqual([x["status"] for x in result["tracks"]], ["completed", "draft", "draft"])
        self.assertEqual(result["tracks"][-1]["track"], "production")
        self.assertFalse(result["productionPublicationAttempted"])

    def test_api_error_message_is_redacted(self):
        class TestError(Exception):
            content = b'{"error":{"message":"App setup missing for user@example.com https://example.org","status":"FAILED_PRECONDITION"}}'
            resp = type("Response", (), {"status":400})()
        safe = module.safe_api_error(TestError("sensitive"))
        self.assertEqual(safe["httpStatus"], 400)
        self.assertNotIn("user@example.com", safe["googleReason"])
        self.assertNotIn("https://", safe["googleReason"])
        self.assertEqual(safe["googleStatus"], "FAILED_PRECONDITION")

    def test_production_draft_stays_non_public(self):
        edits = MagicMock()
        edits.insert.return_value.execute.return_value = {"id": "e"}
        edits.bundles.return_value.list.return_value.execute.return_value = {
            "bundles": [{"versionCode": 99}]}
        with patch.object(module, "get_target_track", return_value=("production", [])):
            result = module.stage_track(edits, 99, "production", "draft")
        self.assertEqual(result["status"], "draft")
        self.assertEqual(edits.tracks.return_value.update.call_args.kwargs["body"]["releases"][0]["status"], "draft")

if __name__ == "__main__":
    unittest.main()
