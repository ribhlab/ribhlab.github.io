"""Unit tests for the non-publishing Google Play credential check."""
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location("play_conn_check", ROOT / "check_connection.py")
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)


class CheckConnectionTests(unittest.TestCase):
    def test_package_can_be_omitted(self):
        self.assertEqual(check.validate_package(""), "")

    def test_valid_package(self):
        self.assertEqual(check.validate_package("com.ribhlab.rivoscan"), "com.ribhlab.rivoscan")

    def test_invalid_package_is_rejected(self):
        with self.assertRaises(ValueError):
            check.validate_package("../secret")

    def test_package_check_requires_explicit_confirmation(self):
        with patch.object(check, "run_check") as action:
            self.assertEqual(check.main(["--package", "com.ribhlab.rivoscan"]), 1)
            action.assert_not_called()

    def test_package_check_with_confirmation(self):
        with patch.object(check, "run_check") as action:
            self.assertEqual(check.main(["--package", "com.ribhlab.rivoscan", "--confirm-temp-edit"]), 0)
            action.assert_called_once_with("com.ribhlab.rivoscan")

    def test_invalid_package_fails_before_network(self):
        with patch.object(check, "run_check") as action:
            self.assertEqual(check.main(["--package", "bad!value"]), 1)
            action.assert_not_called()


if __name__ == "__main__":
    unittest.main()
