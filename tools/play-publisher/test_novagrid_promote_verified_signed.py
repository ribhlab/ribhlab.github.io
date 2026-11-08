"""NovaGrid production update must never publish an unverified or older bundle."""
import importlib.util
import io
import sys
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location("novagrid_prod", ROOT / "novagrid_promote_verified_signed.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def signed(code: int) -> dict:
    return {"versionCode": code, "sha256": m.EXPECTED_SIGNED_AAB_SHA256.upper()}


def prod(code: int, status="completed") -> list[dict]:
    return [{"versionCodes": [str(code)], "status": status}]


class NovaGridProductionSafety(unittest.TestCase):
    def test_package_hash_from_user_report(self):
        self.assertEqual(m.PACKAGE, "com.novagrid.cosmicpuzzle")
        self.assertEqual(len(m.EXPECTED_SIGNED_AAB_SHA256), 64)
        self.assertEqual(len(m.RELEASE_NOTES), 236)

    def test_absent_signed_aab_must_not_replace_old(self):
        self.assertEqual(m.choose_release([{"versionCode": 3, "sha256": "0" * 64}],
                                          prod(2))["result"], "SIGNED_FILE_NOT_SAVED_IN_PLAY")

    def test_exact_signed_newer_aab_would_publish(self):
        data = m.choose_release([signed(3)], prod(2))
        self.assertEqual(data["result"], "READY_FOR_PRODUCTION")
        self.assertEqual(data["candidateVersionCode"], 3)
        self.assertEqual(data["oldVersionCode"], 2)

    def test_do_not_roll_back_even_with_matching_signed_digest(self):
        self.assertEqual(m.choose_release([signed(2)], prod(3))["result"],
                         "CANDIDATE_NOT_NEWER")

    def test_do_not_override_staged_or_draft_release(self):
        for state in ("draft", "inProgress", "halted"):
            with self.subTest(state=state):
                self.assertEqual(m.choose_release([signed(4)], prod(3, state))["result"],
                                 "PRODUCTION_HAS_PENDING_OR_HALTED_RELEASE")

    def test_idempotent_exact_version_already_served(self):
        self.assertEqual(m.choose_release([signed(3)], prod(3))["result"],
                         "ALREADY_IN_PRODUCTION")

    def test_multi_bundle_release_requires_manual_audit(self):
        self.assertEqual(m.choose_release([signed(4)], [
            {"status": "completed", "versionCodes": ["2", "3"]}
        ])["result"], "PRODUCTION_HAS_MULTI_BUNDLE_RELEASE")

    def test_default_never_contacts_google(self):
        with patch.object(m, "production_update") as api, redirect_stdout(io.StringIO()):
            self.assertEqual(m.main([]), 0)
            api.assert_not_called()

    def test_publishing_needs_hardcoded_owner_confirmation(self):
        with patch.object(m, "production_update") as api, redirect_stderr(io.StringIO()):
            self.assertEqual(m.main(["--apply"]), 2)
            api.assert_not_called()

    def test_blocked_result_is_not_success(self):
        with patch.object(m, "production_update",
                          return_value={"result": "SIGNED_FILE_NOT_SAVED_IN_PLAY"}), \
             redirect_stdout(io.StringIO()):
            self.assertEqual(m.main(["--apply", "--confirm", m.CONFIRM]), 2)


if __name__ == "__main__":
    unittest.main()
