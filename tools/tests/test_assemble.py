"""Tests for assemble-deck.py. Run: python3 -m unittest discover tools/tests"""
import contextlib
import importlib.util
import io
import os
import shutil
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
GOOD = os.path.join(HERE, "fixtures", "good")

spec = importlib.util.spec_from_file_location("assemble_deck", os.path.join(TOOLS, "assemble-deck.py"))
asm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(asm)


def quiet(fn, *args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = fn(*args)
    return code, out.getvalue() + err.getvalue()


class AssembleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.frags = os.path.join(self.tmp, "frags")
        shutil.copytree(os.path.join(GOOD, "fragments"), self.frags)
        self.deck = os.path.join(self.tmp, "deck.html")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def build(self, *extra):
        return quiet(asm.main, ["build", "--fragments", self.frags, "--style", "field-guide",
                                "--outline", os.path.join(GOOD, "OUTLINE.md"), "--out", self.deck, *extra])

    def test_build(self):
        code, out = self.build()
        self.assertEqual(code, 0, out)
        doc = open(self.deck, encoding="utf-8").read()
        self.assertIn("<!-- TOPIC 3: Tags and layouts -->", doc)
        self.assertIn('integrity="sha384-', doc)
        self.assertIn("cdn.jsdelivr.net/npm/reveal.js@6.0.2", doc)       # Reveal: jsDelivr first (D23)
        self.assertIn("cdnjs.cloudflare.com/ajax/libs/mermaid/12.3.0", doc)
        self.assertIn("window.RevealNotes||document.write", doc)         # CDN fallback
        self.assertIn("--label-recap:\"Trail recap\"", doc)              # style CSS inlined
        self.assertLess(doc.index("TOPIC 1:"), doc.index("TOPIC 4:"))

    def test_no_mermaid_when_no_diagrams(self):
        path = os.path.join(self.frags, "topic-2.html")
        html = open(path, encoding="utf-8").read()
        start, end = html.index('<figure class="diagram">'), html.index("</figure>") + len("</figure>")
        open(path, "w", encoding="utf-8").write(html[:start] + html[end:])
        code, out = self.build()
        self.assertEqual(code, 0, out)
        self.assertNotIn("mermaid@12.3.0", open(self.deck, encoding="utf-8").read())

    def test_script_in_fragment_is_refused(self):
        with open(os.path.join(self.frags, "topic-4.html"), "a", encoding="utf-8") as f:
            f.write("<script>alert(1)</script>")
        code, out = self.build()
        self.assertEqual(code, 1)
        self.assertIn("may not contain <script>", out)
        self.assertFalse(os.path.exists(self.deck))

    def test_missing_topic(self):
        os.remove(os.path.join(self.frags, "topic-2.html"))
        code, out = self.build()
        self.assertEqual(code, 1)
        self.assertIn("no fragment for section(s) 2", out)

    def test_image_inlined(self):
        png = bytes.fromhex("89504e470d0a1a0a0000000d4948445200000001000000010806000000"
                            "1f15c4890000000d49444154789c6360000002000154a24f5d0000000049454e44ae426082")
        open(os.path.join(self.frags, "dot.png"), "wb").write(png)
        with open(os.path.join(self.frags, "topic-4.html"), "r+", encoding="utf-8") as f:
            html = f.read().replace("</section>\n</section>", '<figure class="image"><img src="dot.png" alt="A dot"></figure></section>\n</section>', 1)
            f.seek(0); f.write(html); f.truncate()
        code, out = self.build()
        self.assertEqual(code, 0, out)
        self.assertIn('src="data:image/png;base64,', open(self.deck, encoding="utf-8").read())

    def test_replace_topic_and_edit(self):
        self.build()
        new = os.path.join(self.tmp, "t4.html")
        open(new, "w", encoding="utf-8").write(
            '<section id="s4"><section class="topic" data-number="4"><h2>Phase 2: the deck</h2><ul><li>Rebuilt</li></ul></section></section>')
        code, out = quiet(asm.main, ["replace-topic", self.deck, "4", new])
        self.assertEqual(code, 0, out)
        doc = open(self.deck, encoding="utf-8").read()
        self.assertIn("<li>Rebuilt</li>", doc)
        self.assertNotIn("Verify every slide", doc)
        self.assertIn("<!-- APPENDIX -->", doc)
        code, out = quiet(asm.main, ["edit", self.deck, "--find", "<li>Rebuilt</li>", "--replace", "<li>Rebuilt again</li>"])
        self.assertEqual(code, 0, out)
        code, out = quiet(asm.main, ["edit", self.deck, "--find", "<section", "--replace", "x"])
        self.assertEqual(code, 1)                       # matches many times: refused
        self.assertIn("must be exactly 1", out)


if __name__ == "__main__":
    unittest.main()
