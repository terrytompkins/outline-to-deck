"""Tests for draft-fragments.py. Run: python3 -m unittest discover tools/tests"""
import contextlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
ROOT = os.path.dirname(TOOLS)
KNOW = os.path.join(ROOT, "knowledge")
SHOW = os.path.join(ROOT, "examples", "showcase")
sys.path.insert(0, TOOLS)

spec = importlib.util.spec_from_file_location("draft_fragments", os.path.join(TOOLS, "draft-fragments.py"))
df = importlib.util.module_from_spec(spec)
spec.loader.exec_module(df)
from outline_parser import load_registry  # noqa: E402

HAVE_PW = importlib.util.find_spec("playwright") is not None
HAVE_LIBS = os.path.exists(os.path.join(ROOT, "node_modules", "reveal.js", "dist", "reveal.js"))

MINI = """# OUTLINE — Mini
<!-- status: version 1.0 | phase 2 | last written 2026-11-27 | approved: yes | reviewed: yes | deck: none -->

## Time plan [Working aid]
| # | Section | Full (min) | Live (min) | Priority |
|---|---|---|---|---|
| 2 | Second | 5 | 5 | Core |
| 1 | First | 5 | 5 | Self-guided |

## Front matter: Title and agenda [All]
- Series: Mini series
- Title: Mini deck
- Framing line: A small outline.
- Speaker notes: Welcome.

## 1. First [All]
Main points:
- One
- Two (As of November 27, 2026)
- Three

([Example source](https://example.com/a))

### 1.1 Media
Image: chart.png
Alt: A bar chart
Caption: Last quarter
Embed: https://example.com/live
Caption: The live page

| Name | Value |
|---|---|
| A | `1` |

> [!TIP] Shortcut
> Use the tool.
> - first step
> - second step

### 1.2 Two diagrams
Diagram: before and after.
```mermaid
flowchart LR
  A["Before"] --> B["After"]
```
```mermaid
flowchart LR
  C["x < y"] --> D["Done"]
```
Speaker notes: Compare them.

### 1.3 Picture
Suggested visual: a simple sketch of a pipeline.

## 2. Second [All]
Main points:
- Alpha [TBD: confirm]
- Beta [UNVERIFIED: not re-checked]
- Gamma
"""

BRIEF = """- **Presenter:** Pat Example
- **Show the presenter's name on the title slide:** yes
- **Sources slide:** yes
"""


class DraftTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = load_registry(KNOW)
        cls.files, cls.todos = df.draft(MINI, cls.reg, df.brief_fields(BRIEF))

    def test_title_and_agenda(self):
        t = self.files["title.html"]
        self.assertIn('<p class="presenter">Pat Example</p>', t)
        self.assertIn('<aside class="notes">Welcome.</aside>', t)
        a = self.files["agenda.html"]
        self.assertLess(a.index('data-number="2"'), a.index('data-number="1"'), "agenda follows the time plan")
        self.assertIn('<li data-number="1" class="self-guided">', a)
        self.assertIn("sources.html", self.files)

    def test_footer_and_markers(self):
        t1 = self.files["topic-1.html"]
        self.assertIn('<footer><span class="asof">As of November 27, 2026</span><a href="https://example.com/a">Example source</a></footer>', t1)
        self.assertNotIn("(As of", t1)
        t2 = self.files["topic-2.html"]
        self.assertIn('<span class="tbd">TBD: confirm</span>', t2)
        self.assertIn('<span class="unverified">Unverified</span>', t2)
        self.assertIn("Unverified: not re-checked.", t2)

    def test_media_table_callout(self):
        t = self.files["topic-1.html"]
        self.assertIn('<figure class="image"><img src="chart.png" alt="A bar chart"><figcaption>Last quarter</figcaption></figure>', t)
        self.assertIn('<iframe src="https://example.com/live" loading="lazy" title="The live page">', t)
        self.assertIn("<th>Name</th>", t)
        self.assertIn("<td><code>1</code></td>", t)
        self.assertIn('<div class="callout" data-type="tip" data-title="Shortcut"><p>Use the tool.</p><ul><li>first step</li>', t)
        self.assertNotIn("Alt:", t)

    def test_diagram_pair(self):
        t = self.files["topic-1.html"]
        self.assertIn('<div class="diagram-pair"><figure class="diagram">', t)
        self.assertIn('C["x &lt; y"] --> D["Done"]', t)
        self.assertIn('<aside class="notes">Compare them.</aside>', t)

    def test_visual_draft(self):
        self.assertIn('data-draft="visual"', self.files["topic-1.html"])
        self.assertEqual([(t["slide"], t["what"]) for t in self.todos], [("1.3", "visual")])

    def test_pass_and_topics(self):
        files, _ = df.draft(MINI, self.reg, {}, pass_=1)
        self.assertEqual(files["topic-1.html"].count("data-number="), 1)
        self.assertNotIn("sources.html", files)
        files, _ = df.draft(MINI, self.reg, {}, topics={"2"})
        self.assertEqual(sorted(files), ["topic-2.html"])

    def test_showcase_matches_committed_fragments(self):
        """The showcase fragments are this tool's output plus one finished visual."""
        reg = load_registry(KNOW, os.path.join(SHOW, "BRIEF.md"))
        files, todos = df.draft(open(os.path.join(SHOW, "OUTLINE.md")).read(), reg,
                                df.brief_fields(open(os.path.join(SHOW, "BRIEF.md")).read()))
        self.assertEqual(sorted(files), sorted(os.listdir(os.path.join(SHOW, "fragments"))))
        self.assertEqual(len(todos), 1)
        fig = re.compile(r'<figure class="visual".*?</figure>', re.S)
        for name, html in files.items():
            committed = open(os.path.join(SHOW, "fragments", name)).read()
            self.assertEqual(fig.sub("FIG", html), fig.sub("FIG", committed), name)


class CommandTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.outline = os.path.join(self.tmp, "OUTLINE.md")
        open(self.outline, "w").write(MINI)
        self.out = os.path.join(self.tmp, "frags")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def run_tool(self, *extra):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = df.main([self.outline, "--knowledge", KNOW, "--out", self.out, "--json", *extra])
        return code, json.loads(buf.getvalue())

    def test_merge_keeps_edits(self):
        self.run_tool("--pass", "1")
        p = os.path.join(self.out, "topic-1.html")
        text = open(p).read().replace("<h2>First</h2>", "<h2>First, edited</h2>")
        open(p, "w").write(text)
        code, res = self.run_tool()
        self.assertEqual(code, 0)
        self.assertEqual(res["merged"]["topic-1.html"]["added"], ["1.1", "1.2", "1.3"])
        self.assertIn("title.html", res["kept"])
        text = open(p).read()
        self.assertIn("First, edited", text)
        self.assertEqual(text.count("data-number="), 4)
        self.assertEqual([t["slide"] for t in res["drafts"]], ["1.3"])

    def test_finished_draft_not_reported(self):
        self.run_tool()
        p = os.path.join(self.out, "topic-1.html")
        text = re.sub(r'<figure class="visual".*?</figure>', '<figure class="visual"><svg></svg></figure>',
                      open(p).read(), flags=re.S)
        open(p, "w").write(text)
        _, res = self.run_tool()
        self.assertEqual(res["drafts"], [])

    def test_force_overwrites(self):
        self.run_tool()
        p = os.path.join(self.out, "title.html")
        open(p, "w").write("edited")
        _, res = self.run_tool("--force")
        self.assertIn("title.html", res["written"])
        self.assertNotEqual(open(p).read(), "edited")


@unittest.skipUnless(HAVE_PW and HAVE_LIBS, "needs playwright and `npm install`")
class DraftDeckTests(unittest.TestCase):
    def test_checker_fails_unfinished_draft(self):
        with tempfile.TemporaryDirectory() as tmp:
            frags, deck = os.path.join(tmp, "frags"), os.path.join(tmp, "deck.html")
            subprocess.run([sys.executable, os.path.join(TOOLS, "draft-fragments.py"), os.path.join(SHOW, "OUTLINE.md"),
                            "--brief", os.path.join(SHOW, "BRIEF.md"), "--out", frags], check=True, capture_output=True)
            subprocess.run([sys.executable, os.path.join(TOOLS, "assemble-deck.py"), "build", "--fragments", frags,
                            "--style", "base", "--out", deck], check=True, capture_output=True)
            r = subprocess.run([sys.executable, os.path.join(TOOLS, "check-deck.py"), deck, "--json"],
                               capture_output=True, text=True)
            problems = json.loads(r.stdout)["problems"]
            self.assertEqual(len(problems), 1, problems)
            self.assertIn("draft placeholder", problems[0])


if __name__ == "__main__":
    unittest.main()
