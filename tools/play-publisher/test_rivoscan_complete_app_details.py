import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock
ROOT=Path(__file__).parent
sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location("rivo_details",ROOT/"rivoscan_complete_app_details.py")
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class RivoDetailsTests(unittest.TestCase):
    def test_specific_package_and_verified_contacts(self):
        self.assertEqual(m.PACKAGE,"com.ribhlab.rivoscan")
        self.assertEqual(m.DESIRED["defaultLanguage"],"en-US")
        self.assertEqual(m.DESIRED["contactWebsite"],"https://ribhlab.github.io/rivoscan/")

    def test_preserves_existing_phone(self):
        edits=MagicMock()
        edits.insert.return_value.execute.return_value={"id":"ed1"}
        edits.details.return_value.get.return_value.execute.return_value={
            "defaultLanguage":"fr-FR","contactWebsite":"", "contactEmail":"",
            "contactPhone":"+212000000000"
        }
        res=m.update_details(edits)
        self.assertEqual(res["result"],"STORE_DETAILS_COMMITTED")
        body=edits.details.return_value.patch.call_args.kwargs["body"]
        self.assertEqual(body,m.DESIRED)
        self.assertNotIn("contactPhone",body)
        edits.commit.return_value.execute.assert_called_once()

    def test_idempotence_no_commit_if_already_correct(self):
        edits=MagicMock()
        edits.insert.return_value.execute.return_value={"id":"ed1"}
        edits.details.return_value.get.return_value.execute.return_value={
            **m.DESIRED,"contactPhone":"+212000000000"
        }
        res=m.update_details(edits)
        self.assertEqual(res["result"],"ALREADY_CORRECT")
        edits.details.return_value.patch.assert_not_called()
        edits.commit.assert_not_called()
        edits.delete.return_value.execute.assert_called_once()
if __name__=="__main__":
    unittest.main()
