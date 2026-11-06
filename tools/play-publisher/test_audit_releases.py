import importlib.util
import sys
import unittest
from pathlib import Path

root = Path(__file__).resolve().parent
sys.path.insert(0, str(root))
spec = importlib.util.spec_from_file_location("audit_releases", root / "audit_releases.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class AuditReleaseTests(unittest.TestCase):
    def test_package_valid(self):
        self.assertEqual(module.validate_package("com.ribhlab.rivoscan"), "com.ribhlab.rivoscan")

    def test_package_invalid(self):
        with self.assertRaises(ValueError):
            module.validate_package("com.bad/../../")

    def test_error_does_not_repeat_body(self):
        self.assertEqual(module.summarize_response(403, {"message": "SECRET"}), {"result": "ACCESS_DENIED", "httpStatus": 403})

    def test_release_state(self):
        data = {
            "releases": [{
                "releaseName": "Version 42",
                "releaseLifecycleState": "RELEASE_LIFECYCLE_STATE_IN_REVIEW",
                "activeArtifacts": [{"versionCode": 42}]
            }]
        }
        expected = module.summarize_response(200, data)
        self.assertEqual(expected["releases"][0]["versionCodes"], [42])
        self.assertEqual(expected["releases"][0]["lifecycle"], "RELEASE_LIFECYCLE_STATE_IN_REVIEW")

    def test_empty_track(self):
        self.assertEqual(module.summarize_response(200, {})["releaseCount"], 0)


if __name__ == "__main__":
    unittest.main()
