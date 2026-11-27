"""Offline tests: never call Google Play or create a real edit."""
import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "ribhmeasure_submit_pending_alpha", ROOT / "ribhmeasure_submit_pending_alpha.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def release(name, state, version=13):
    return {"releases": [{
        "releaseName": name, "releaseLifecycleState": state,
        "activeArtifacts": [{"versionCode": version}]
    }]}


def production():
    return release("RivoMeasure 1.3.9", module.PUBLISHED)


def alpha(state=module.NOT_SENT):
    return release("RivoMeasure 1.3.9 – Closed Alpha", state)


class RivoMeasureSubmissionTests(unittest.TestCase):
    def test_strict_expected_release_pair(self):
        self.assertEqual(module.safe_release_states(production(), alpha()), "PENDING_ALPHA_13")

    def test_alpha_already_reviewing_is_idempotent(self):
        self.assertEqual(module.safe_release_states(
            production(), alpha("RELEASE_LIFECYCLE_STATE_IN_REVIEW")),
            "ALREADY_IN_REVIEW")

    def test_alpha_already_published_is_idempotent(self):
        self.assertEqual(module.safe_release_states(
            production(), alpha(module.PUBLISHED)),
            "ALREADY_PUBLISHED")

    def test_wrong_production_or_version_never_submits(self):
        with self.assertRaisesRegex(ValueError, "Production"):
            module.safe_release_states(
                release("RivoMeasure 1.3.9", module.NOT_SENT), alpha())
        with self.assertRaisesRegex(ValueError, "Alpha"):
            module.safe_release_states(
                production(), release("RivoMeasure 1.3.9 – Closed Alpha", module.NOT_SENT, 14))

    def test_unexpected_extra_release_never_submits(self):
        p = alpha()
        p["releases"].append({"releaseName": "Unknown", "activeArtifacts": []})
        with self.assertRaises(ValueError):
            module.safe_release_states(production(), p)

    def test_commit_explicitly_refuses_to_restart_review_and_touches_no_track(self):
        edits = MagicMock()
        edits.insert.return_value.execute.return_value = {"id": "test-alpha-edit"}
        service = MagicMock()
        service.edits.return_value = edits
        mod = types.ModuleType("googleapiclient")
        discovery = types.ModuleType("googleapiclient.discovery")
        discovery.build = lambda *args, **kwargs: service
        with patch.object(module, "status", side_effect=[
            "PENDING_ALPHA_13", "ALREADY_IN_REVIEW"
        ]), patch.dict(sys.modules, {
            "googleapiclient": mod, "googleapiclient.discovery": discovery
        }):
            result = module.submit_pending_alpha(object(), object())
        self.assertEqual(result["result"], "REVIEW_SUBMITTED")
        edits.commit.assert_called_once_with(
            packageName="com.ribhlab.ribhmeasure",
            editId="test-alpha-edit",
            changesInReviewBehavior="ERROR_IF_IN_REVIEW",
            changesNotSentForReview=False,
        )
        edits.tracks.assert_not_called()
        edits.bundles.assert_not_called()
        edits.delete.assert_not_called()

    def test_postcommit_production_403_still_confirms_alpha_in_review(self):
        with patch.object(module, "status", side_effect=RuntimeError("Production GET HTTP 403")), \
             patch.object(module, "fetch_track", return_value=alpha(
                 "RELEASE_LIFECYCLE_STATE_IN_REVIEW")) as fetch:
            result = module.verify_postcommit_alpha(object())
        self.assertEqual(result, "ALREADY_IN_REVIEW")
        fetch.assert_called_once()
        self.assertEqual(fetch.call_args.args[1], "alpha")

    def test_rejected_commit_cleans_up_edit(self):
        edits = MagicMock()
        edits.insert.return_value.execute.return_value = {"id": "blocked-edit"}
        edits.commit.return_value.execute.side_effect = RuntimeError("review already active")
        service = MagicMock()
        service.edits.return_value = edits
        mod = types.ModuleType("googleapiclient")
        discovery = types.ModuleType("googleapiclient.discovery")
        discovery.build = lambda *args, **kwargs: service
        with patch.object(module, "status", return_value="PENDING_ALPHA_13"), \
             patch.dict(sys.modules, {"googleapiclient": mod,
                                      "googleapiclient.discovery": discovery}):
            with self.assertRaises(RuntimeError):
                module.submit_pending_alpha(object(), object())
        edits.delete.assert_called_once_with(
            packageName="com.ribhlab.ribhmeasure", editId="blocked-edit")


if __name__ == "__main__":
    unittest.main()
