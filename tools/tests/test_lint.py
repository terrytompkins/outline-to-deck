"""Tests for outline_parser and lint-outline. Run: python3 -m unittest discover tools/tests"""
import importlib.util
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)

from outline_parser import load_registry, parse_outline, split_label, bracket_tags, plain_words  # noqa: E402

spec = importlib.util.spec_from_file_location("lint_outline", os.path.join(TOOLS, "lint-outline.py"))
lint = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lint)

KNOWLEDGE = os.path.join(ROOT, "knowledge")
GOOD = os.path.join(HERE, "fixtures", "good")
REG = load_registry(KNOWLEDGE, brief_path=os.path.join(GOOD, "BRIEF.md"))

HEAD = """# OUTLINE — Test
<!-- status: version 0.2 | phase 1 | last written 2026-11-27 | approved: no | reviewed: no | deck: none -->

## Central message
Test.

## Time plan (outline-only working aid)
| # | Section | Live (min) | Priority |
|---|---|---|---|
{rows}

## Front matter: Title and agenda [All]
- Title: Test

"""
TAIL = "\n## Coverage gaps (outline-only working aid)\n- none\n"
MAIN = "Main points:\n- One [Seed]\n- Two [Seed]\n- Three [Seed]\n"


def run(body, tops=("1",), live=5):
    rows = "\n".join(f"| {n} | Section {n} | {live} | Core |" for n in tops)
    text = HEAD.format(rows=rows) + body + TAIL
    issues, stats = lint.Linter(parse_outline(text, REG), REG).run()
    return issues, stats


def codes(body, **kw):
    return sorted({i["code"] for i in run(body, **kw)[0]})


class ParserTests(unittest.TestCase):
    def test_registry_loaded(self):
        self.assertEqual(set(REG.callouts), {"NOTE", "TIP", "REMEMBER", "WATCHOUT", "UNDERTHEHOOD", "FIELDNOTE"})
        self.assertEqual(REG.aliases["WARNING"], "WATCHOUT")
        self.assertIn("Key figure", REG.slide_types)
        self.assertTrue(REG.slide_types["Key figure"]["needs_asof"])
        self.assertEqual(REG.layouts["matrix"]["min"], 4)
        self.assertEqual(REG.audience, {"All", "Technical"})

    def test_split_label(self):
        self.assertEqual(split_label("Pilot: two teams"), ("Pilot", "two teams", False))
        self.assertEqual(split_label("**Review: it** [Seed]"), ("Review", "it [Seed]", True))
        self.assertEqual(split_label("One two three four five six: x")[1], "")
        self.assertEqual(split_label(r"Time\: no split"), ("Time: no split", "", False))

    def test_bracket_tags_skip_links_and_code(self):
        self.assertEqual(bracket_tags("See [docs](https://x) and `[Foo]` but [Seed]"), ["Seed"])

    def test_plain_words(self):
        self.assertEqual(plain_words("**Bold** [Seed] [link text](https://x)"), 3)


class LintTests(unittest.TestCase):
    def test_good_fixture_is_clean(self):
        reg = load_registry(KNOWLEDGE, brief_path=os.path.join(GOOD, "BRIEF.md"))
        with open(os.path.join(GOOD, "OUTLINE.md"), encoding="utf-8") as f:
            o = parse_outline(f.read(), reg)
        issues, stats = lint.Linter(o, reg).run()
        bad = [i for i in issues if i["severity"] != "note"]
        self.assertEqual(bad, [], bad)
        self.assertEqual(stats["slides"], 20)
        self.assertEqual(stats["layouts"], {"process": 1, "matrix": 1, "columns": 1})

    def test_unknown_tag(self):
        self.assertIn("E001", codes(f"## 1. A [All]\n{MAIN}- Something [Foo]\n"))

    def test_tbd_without_colon(self):
        self.assertIn("E001", codes(f"## 1. A [All]\n{MAIN}- Value [TBD]\n"))

    def test_unknown_audience_tag(self):
        self.assertIn("E001", codes(f"## 1. A [Executives]\n{MAIN}"))

    def test_unknown_callout(self):
        self.assertIn("E002", codes(f"## 1. A [All]\n{MAIN}\n> [!HINT]\n> x\n"))

    def test_alias_callout_ok(self):
        self.assertNotIn("E002", codes(f"## 1. A [All]\n{MAIN}\n> [!WARNING]\n> x\n"))

    def test_missing_required_field(self):
        c = codes(f"## 1. A [All]\n{MAIN}\n### 1.1 [Quick check] Q [All]\nQuestion: Why?\n")
        self.assertIn("E004", c)

    def test_myth_fact_pairs(self):
        self.assertIn("E004", codes(f"## 1. A [All]\n{MAIN}\n### 1.1 [Myth vs fact] M [All]\nMyth: a\nFact: b\nMyth: c\n"))

    def test_reserved_demo(self):
        self.assertIn("E005", codes(f"## 1. A [All]\n{MAIN}\n### 1.1 [Demo] D [All]\n- x\n"))

    def test_unknown_layout(self):
        self.assertIn("E006", codes(f"## 1. A [All]\n{MAIN}\n### 1.1 B [All]\nLayout: spiral\n- a\n- b\n- c\n"))

    def test_layout_without_list(self):
        self.assertIn("E007", codes(f"## 1. A [All]\n{MAIN}\n### 1.1 B [All]\nLayout: process\n\nJust a paragraph.\n"))

    def test_mermaid_without_diagram_line(self):
        self.assertIn("E008", codes(f"## 1. A [All]\n{MAIN}\n### 1.1 B [All]\n```mermaid\nflowchart LR\n  A --> B\n```\n"))

    def test_diagram_without_mermaid(self):
        self.assertIn("E008", codes(f"## 1. A [All]\n{MAIN}\n### 1.1 B [All]\nDiagram: a flow\n"))

    def test_bad_chart(self):
        body = f"## 1. A [All]\n{MAIN}\n### 1.1 B [All]\n```chart\ntype: pie\ntitle: x\n| a | b |\n| c | [TBD: n] |\n```\n"
        self.assertIn("E009", codes(body))

    def test_image_needs_alt(self):
        self.assertIn("E010", codes(f"## 1. A [All]\n{MAIN}\n### 1.1 B [All]\nImage: photo.png\n"))

    def test_embed_https(self):
        self.assertIn("E011", codes(f"## 1. A [All]\n{MAIN}\n### 1.1 B [All]\nEmbed: http://example.com\n"))

    def test_numbering(self):
        self.assertIn("E012", codes(f"## 1. A [All]\n{MAIN}\n#### 1.1 B [All]\n- x\n"))
        self.assertIn("E012", codes(f"## 1. A [All]\n{MAIN}\n### 2.1 B [All]\n- x\n"))
        self.assertIn("E012", codes(f"## 1. A [All]\n{MAIN}\n### 1.1 B [All]\n- x\n### 1.1 C [All]\n- y\n"))
        self.assertIn("E012", codes(f"## 1. A [All]\n{MAIN}\n##### 1.1.1.1 B [All]\n- x\n"))

    def test_key_figure_needs_source_and_date(self):
        c = codes(f"## 1. A [All]\n{MAIN}\n### 1.1 [Key figure] K [All]\nFigure: 30 hours\nLabel: Wait\n")
        self.assertIn("E013", c)

    def test_timeplan_mismatch(self):
        self.assertIn("E014", codes(f"## 1. A [All]\n{MAIN}\n## 2. B [All]\n{MAIN}", tops=("1",)))
        self.assertIn("E014", codes(f"## 1. A [All]\n{MAIN}", tops=("1", "7")))

    def test_two_callouts(self):
        self.assertIn("W101", codes(f"## 1. A [All]\n{MAIN}\n> [!TIP]\n> a\n\n> [!NOTE]\n> b\n"))

    def test_slide_type_with_callout(self):
        body = f"## 1. A [All]\n{MAIN}\n### 1.1 [Recap] R [All]\nPoints:\n- a\n- b\n- c\n\n> [!TIP]\n> x\n"
        self.assertIn("W102", codes(body))

    def test_section_limit(self):
        body = f"## 1. A [All]\n{MAIN}\n### 1.1 [Quick check] Q [All]\nQuestion: a\nAnswer: b\n### 1.2 [Quick check] R [All]\nQuestion: a\nAnswer: b\n"
        self.assertIn("W103", codes(body))

    def test_watchout_consecutive(self):
        body = f"## 1. A [All]\n{MAIN}\n### 1.1 B [All]\n- x\n\n> [!WATCHOUT]\n> a\n### 1.2 C [All]\n- y\n\n> [!CAUTION]\n> b\n"
        self.assertIn("W104", codes(body))

    def test_layout_fit(self):
        items = "".join(f"- Step {i}\n" for i in range(9))
        self.assertIn("W106", codes(f"## 1. A [All]\n{MAIN}\n### 1.1 B [All]\nLayout: process\n{items}"))
        self.assertIn("W106", codes(f"## 1. A [All]\n{MAIN}\n### 1.1 B [All]\nLayout: matrix\n- a\n- b\n- c\n"))
        self.assertIn("W106", codes(f"## 1. A [All]\n{MAIN}\n### 1.1 B [All]\nLayout: hierarchy\n- a\n- b\n"))

    def test_three_layouts(self):
        lay = "Layout: list\n- a\n- b\n\n"
        self.assertIn("W107", codes(f"## 1. A [All]\n{MAIN}\n### 1.1 B [All]\n{lay}{lay}{lay}"))

    def test_main_points(self):
        self.assertIn("W109", codes("## 1. A [All]\n- just a bullet [Seed]\n"))
        self.assertIn("W109", codes("## 1. A [All]\nMain points:\n- one [Seed]\n"))

    def test_main_points_as_layout(self):
        body = "## 1. A [All]\nMain points:\nLayout: process\n- a [Seed]\n- b [Seed]\n- c [Seed]\n"
        self.assertNotIn("W109", codes(body))

    def test_long_bullet(self):
        long = " ".join(["word"] * 30)
        self.assertIn("W110", codes(f"## 1. A [All]\n{MAIN}- {long} [Seed]\n"))

    def test_live_time_over_session(self):
        self.assertIn("W113", codes(f"## 1. A [All]\n{MAIN}", live=45))

    def test_status_comment(self):
        text = HEAD.replace(" | reviewed: no | deck: none", "").format(rows="| 1 | A | 5 | Core |") + f"## 1. A [All]\n{MAIN}" + TAIL
        issues, _ = lint.Linter(parse_outline(text, REG), REG).run()
        self.assertIn("W114", {i["code"] for i in issues})

    def test_big_diagram(self):
        nodes = "\n".join(f"  N{i} --> N{i + 1}" for i in range(12))
        body = f"## 1. A [All]\n{MAIN}\n### 1.1 B [All]\nDiagram: a long chain\n```mermaid\nflowchart LR\n{nodes}\n```\n"
        self.assertIn("W115", codes(body))

    def test_two_bold_items(self):
        self.assertIn("W119", codes(f"## 1. A [All]\n{MAIN}\n### 1.1 B [All]\nLayout: list\n- **a**\n- **b**\n"))

    def test_counts(self):
        _, stats = run(f"## 1. A [All]\n{MAIN}- x [TBD: one]\n- y [UNVERIFIED]\n")
        self.assertEqual(len(stats["tbd"]), 1)
        self.assertEqual(len(stats["unverified"]), 1)

    def test_code_block_tags_ignored(self):
        self.assertNotIn("E001", codes(f"## 1. A [All]\n{MAIN}\n### 1.1 B [All]\n```python\nx = [Foo]\n```\n"))


if __name__ == "__main__":
    unittest.main()
