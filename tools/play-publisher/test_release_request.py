"""Release request guardrails (no Google credentials or network required)."""
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location("request_validator", ROOT / "validate_release_request.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class RequestValidationTests(unittest.TestCase):
    def parse(self, obj):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "request.json"
            p.write_text(json.dumps(obj), encoding="utf-8")
            return module.parse_request(p)

    def example(self):
        return {
            "enabled": True,
            "package": "com.ribhlab.rivoscan",
            "versionCode": 81,
            "track": "internal",
            "status": "draft",
            "notes": "Initial release.",
            "commitConfirmation": "COMMIT",
            "productionConfirmation": "",
        }

    def test_disabled_request_is_noop(self):
        self.assertEqual(self.parse({"enabled": False, "package": "com.ribhlab.rivoscan"}), {"enabled": "false"})

    def test_enabled_internal_request(self):
        self.assertEqual(self.parse(self.example())["version_code"], "81")

    def test_wrong_app_rejected(self):
        request = self.example()
        request["package"] = "com.example.other"
        with self.assertRaises(ValueError):
            self.parse(request)

    def test_production_requires_production_confirmation(self):
        request = self.example()
        request.update(track="production", status="completed")
        with self.assertRaises(ValueError):
            self.parse(request)
        request["productionConfirmation"] = "PUBLISH"
        self.assertEqual(self.parse(request)["status"], "completed")

    def test_disabled_bad_bool_rejected(self):
        with self.assertRaises(ValueError):
            self.parse({"enabled": "false", "package": "com.ribhlab.rivoscan"})

    def test_confirmation_required(self):
        request = self.example()
        request["commitConfirmation"] = ""
        with self.assertRaises(ValueError):
            self.parse(request)

    def test_newlines_in_notes_blocked(self):
        request = self.example()
        request["notes"] = "one\nvalue"
        with self.assertRaises(ValueError):
            self.parse(request)


if __name__ == "__main__":
    unittest.main()
