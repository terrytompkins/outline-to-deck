"""Integration test: build both fixture decks in every style and run check-deck on them.
Skipped when Playwright or the local libraries (npm install) aren't available."""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
ROOT = os.path.dirname(TOOLS)
HAVE_PW = importlib.util.find_spec("playwright") is not None
HAVE_LIBS = os.path.exists(os.path.join(ROOT, "node_modules", "reveal.js", "dist", "reveal.js"))


@unittest.skipUnless(HAVE_PW and HAVE_LIBS, "needs playwright and `npm install`")
class DeckTests(unittest.TestCase):
    def check(self, fixture, style):
        fx = os.path.join(HERE, "fixtures", fixture)
        with tempfile.TemporaryDirectory() as tmp:
            deck = os.path.join(tmp, "deck.html")
            subprocess.run([sys.executable, os.path.join(TOOLS, "assemble-deck.py"), "build", "--fragments",
                            os.path.join(fx, "fragments"), "--style", style, "--outline", os.path.join(fx, "OUTLINE.md"),
                            "--out", deck], check=True, capture_output=True)
            r = subprocess.run([sys.executable, os.path.join(TOOLS, "check-deck.py"), deck, "--outline",
                                os.path.join(fx, "OUTLINE.md"), "--json"], capture_output=True, text=True)
            result = json.loads(r.stdout)
            self.assertEqual(result["problems"], [], f"{fixture}/{style}")
            return result

    def test_good(self):
        for style in ("base", "field-guide", "toons"):
            res = self.check("good", style)
            self.assertEqual(res["slides"], 24)

    def test_layouts(self):
        for style in ("base", "field-guide", "toons"):
            res = self.check("layouts", style)
            self.assertEqual(res["layouts"], 22)
            compacted = [a for a in res["autofit"] if a["compact"]]
            self.assertTrue(any(a["number"] == "11.1" for a in compacted), "the 7-step process should compact")


if __name__ == "__main__":
    unittest.main()
