"""Safety tests for owner green icon ONLY (never change release tracks)."""
import importlib.util
import io
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location("green_icon_only", ROOT / "rivoscan_green_icon_only.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class RivoIconTests(unittest.TestCase):
    def test_owner_source_is_exact_512_green_icon(self):
        verified = m.verify_icon()
        self.assertEqual(verified["package"], "com.ribhlab.rivoscan")
        self.assertEqual(verified["dimensions"], "512x512")
        self.assertEqual(verified["sha256"], m.EXPECTED_HASH)

    def test_dry_run_never_calls_play_api(self):
        with patch.object(m, "apply_icon") as call, redirect_stdout(io.StringIO()):
            self.assertEqual(m.main([]), 0)
            call.assert_not_called()

    def test_apply_requires_exact_confirmation(self):
        with patch.object(m, "apply_icon") as call, \
             redirect_stderr(io.StringIO()):
            self.assertEqual(m.main(["--apply"]), 1)
            self.assertEqual(m.main(["--apply", "--confirm", "PUBLISH"]), 1)
            call.assert_not_called()

    def test_apply_only_with_explicit_owner_confirmation(self):
        with patch.object(m, "apply_icon", return_value={"result":"GREEN_ICON_COMMITTED"}) as call, \
             redirect_stdout(io.StringIO()):
            self.assertEqual(m.main([
                "--apply", "--confirm", "REPLACE_RIVOSCAN_BLUE_ICON_WITH_OWNER_GREEN"
            ]), 0)
            call.assert_called_once_with()

if __name__ == "__main__":
    unittest.main()
