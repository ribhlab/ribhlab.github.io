"""Offline regression tests: Data Safety can never silently change app or data types."""
import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location("rivoscan_data_safety",ROOT/"rivoscan_data_safety.py")
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
RAW=m.CSV_FILE.read_text(encoding="utf-8")

class GooglePlayRivoDataSafetyTests(unittest.TestCase):
    def test_exact_v74_sdk_ai_data_types_and_choices(self):
        info=m.validate(RAW)
        self.assertEqual(info["package"],"com.ribhlab.rivoscan")
        self.assertEqual(info["rows"],782)
        self.assertEqual(set(info["dataTypes"]),m.EXPECTED_TYPES)
        self.assertGreater(info["answeredRows"],30)

    def test_unexpected_deletion_or_encryption_claim_rejected(self):
        wrong=RAW.replace("PSL_DATA_COLLECTION_ENCRYPTED_IN_TRANSIT,,FALSE",
                          "PSL_DATA_COLLECTION_ENCRYPTED_IN_TRANSIT,,TRUE",1)
        with self.assertRaises(ValueError):
            m.validate(wrong)
        wrong=RAW.replace("PSL_SUPPORT_DATA_DELETION_BY_USER,DATA_DELETION_NO,TRUE",
                          "PSL_SUPPORT_DATA_DELETION_BY_USER,DATA_DELETION_NO,FALSE",1)
        with self.assertRaises(ValueError):
            m.validate(wrong)

    def test_unverified_extra_user_data_type_rejected(self):
        wrong=RAW.replace("PSL_DATA_TYPES_PERSONAL,PSL_NAME,,",
                          "PSL_DATA_TYPES_PERSONAL,PSL_NAME,TRUE,",1)
        with self.assertRaises(ValueError):
            m.validate(wrong)

    def test_default_preflight_never_contacts_google(self):
        with patch.object(m,"apply") as api:
            self.assertEqual(m.main([]),0)
            api.assert_not_called()

    def test_real_apply_requires_exact_confirmation(self):
        with patch.object(m,"apply") as api:
            self.assertEqual(m.main(["--apply"]),2)
            api.assert_not_called()

if __name__=="__main__":
    unittest.main()
