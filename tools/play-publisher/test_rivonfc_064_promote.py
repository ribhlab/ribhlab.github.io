#!/usr/bin/env python3
"""Offline regressions for RivoNFC exact code11 release and Google Play guard."""
import ast
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

# The main publisher's global CI deliberately runs without installed Google API
# dependencies or Play credentials. Extract only pure guard functions via AST.
# Never import the side-effect-capable publishing module in offline CI.
PUBLISHER_SOURCE=Path(__file__).with_name("rivonfc_064_promote.py").read_text()
TREE=ast.parse(PUBLISHER_SOURCE)
NAMES={"latest_bundle_guard","verify_exact_tracks"}
functions=[node for node in TREE.body if
           isinstance(node,ast.FunctionDef) and node.name in NAMES]
assert {f.name for f in functions}==NAMES
scope={}
exec(compile(ast.Module(body=functions,type_ignores=[]),"<nfc-pure-guards>","exec"),scope)
app=SimpleNamespace(**{name:scope[name] for name in NAMES})

class Code11Guards(unittest.TestCase):
    def test_staged_latest_code11_is_accepted(self):
        self.assertTrue(app.latest_bundle_guard(["9","10","11"]))
        self.assertTrue(app.latest_bundle_guard(["11"]))

    def test_old_code10_is_not_accepted(self):
        with self.assertRaisesRegex(RuntimeError,"missing"):
            app.latest_bundle_guard(["9","10"])

    def test_new_code12_blocks_publishing_stale_code11(self):
        with self.assertRaisesRegex(RuntimeError,"Newer"):
            app.latest_bundle_guard(["9","10","11","12"])

    def test_exact_production_and_internal_checks(self):
        def mock_editor(prod,internal):
            editor=MagicMock()
            editor.tracks().list().execute.return_value={"tracks":[
                {"track":"production","releases":[{"versionCodes":[prod],"status":"completed"}]},
                {"track":"internal","releases":[{"versionCodes":[internal],"status":"completed"}]},
            ]}
            return editor
        self.assertEqual(
            set(app.verify_exact_tracks(mock_editor("9","9"),{}, "9","9").keys()),
            {"production","internal"})
        self.assertEqual(
            set(app.verify_exact_tracks(mock_editor("11","9"),{}, "11","9").keys()),
            {"production","internal"})
        with self.assertRaisesRegex(RuntimeError,"Unexpected production"):
            app.verify_exact_tracks(mock_editor("12","9"),{}, "9","9")
        with self.assertRaisesRegex(RuntimeError,"Unexpected internal"):
            app.verify_exact_tracks(mock_editor("9","10"),{}, "9","9")

    def test_publication_never_cancels_existing_review(self):
        source=PUBLISHER_SOURCE
        self.assertIn('changesInReviewBehavior="ERROR_IF_IN_REVIEW"',source)
        self.assertNotIn('changesInReviewBehavior="CANCEL_IN_REVIEW"',source)
        self.assertIn('RIVONFC_064_COMPLIANCE_APPROVAL',source)
        self.assertIn('RIVONFC_064_PLAY_ADS_DATASAFETY_VERIFIED',source)

    def test_safety_overrides_never_change_other_application(self):
        values={n.targets[0].id:ast.literal_eval(n.value)
                for n in TREE.body if isinstance(n,ast.Assign) and
                len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and
                n.targets[0].id in {"PKG","OLD","NEW"}}
        self.assertEqual(values,{"PKG":"com.ribhlab.rivonfc","OLD":"9","NEW":"11"})

if __name__=="__main__":
    unittest.main(verbosity=2)
