"""Offline tests for safe read-only release detection and owner image gating."""
import importlib.util
import json
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location("play_watch",ROOT/"rivoscan_play_watch.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class WatchTests(unittest.TestCase):
 def request(self):
  return {"enabled":True,"appId":mod.PACKAGE,"applied":False,
     "iconSha256":mod.EXPECTED_LOGO,"featureSha256":mod.EXPECTED_FEATURE}
 def test_locked_owner_configuration(self):
  self.assertTrue(mod.validate_request(self.request())["enabled"])
 def test_reject_wrong_package_and_hash(self):
  req=self.request();req["appId"]="org.someone.else"
  with self.assertRaises(ValueError):mod.validate_request(req)
 def test_draft_without_version_not_ready(self):
  data={"package":mod.PACKAGE,"tracks":{"qa":{"result":"OK","releases":[{"versionCodes":[]}]}}}
  self.assertEqual(mod.visible_versions(data),[])
 def test_saved_valid_version_enables_one_time_sync(self):
  data={"package":mod.PACKAGE,"tracks":{"qa":{"result":"OK","releases":[{"versionCodes":[101]}]}}}
  self.assertEqual(mod.visible_versions(data),[{"track":"qa","versionCode":101}])
 def test_other_package_never_enables(self):
  data={"package":"com.other.app","tracks":{"qa":{"result":"OK","releases":[{"versionCodes":[101]}]}}}
  self.assertEqual(mod.visible_versions(data),[])
 def test_metadata_uses_correct_owner_assets(self):
  listing=json.loads((ROOT/"store-listings/rivoscan.json").read_text(encoding="utf-8"))
  self.assertEqual(listing["locales"]["en-US"]["title"],"RivoScan")
  self.assertIn("rivoscan-owner-feature-1024x500.jpg",listing["images"]["featureGraphic"])
  self.assertEqual(mod.validate_request(self.request())["iconSha256"],mod.EXPECTED_LOGO)

if __name__=="__main__":unittest.main()
