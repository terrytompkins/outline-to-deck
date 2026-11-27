"""Tests for write-notes.py."""
import contextlib, importlib.util, io, json, os, tempfile, unittest
HERE = os.path.dirname(os.path.abspath(__file__)); TOOLS = os.path.dirname(HERE)
spec = importlib.util.spec_from_file_location("write_notes", os.path.join(TOOLS, "write-notes.py"))
wn = importlib.util.module_from_spec(spec); spec.loader.exec_module(wn)
OUTLINE = os.path.join(HERE, "fixtures", "good", "OUTLINE.md")


class NotesTests(unittest.TestCase):
    def run_notes(self, tmp, *args):
        out = os.path.join(tmp, "notes.md")
        with contextlib.redirect_stdout(io.StringIO()):
            code = wn.main(["--outline", OUTLINE, "--deck", "d.html", "--style", "base", "--out", out, *args])
        self.assertEqual(code, 0)
        return open(out, encoding="utf-8").read()

    def test_partial_rebuild_keeps_other_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            check = os.path.join(tmp, "c.json")
            json.dump({"slides": 3, "overflow": 0, "collisions": 0, "diagrams": 0, "diagrams_rendered": 0, "layouts": 1,
                       "console_errors": 0, "fragment_clicks": None, "autofit": [{"page": 2, "number": "1.1", "fit": 0.8, "compact": ""}],
                       "problems": []}, open(check, "w"))
            first = self.run_notes(tmp, "--check", check, "--fallback", "1.2|a|b|c|d", "--fallback", "3.1|e|f|g|h")
            self.assertIn("outline v1.0", first)
            self.assertIn("text reduced to 0.80em", first)
            os.rename(os.path.join(tmp, "notes.md"), os.path.join(tmp, "prev.md"))
            second = self.run_notes(tmp, "--previous", os.path.join(tmp, "prev.md"), "--rebuilt", "3", "--fallback", "3.2|x|y|z|w")
            self.assertIn("| 1.2 | a |", second)
            self.assertNotIn("| 3.1 |", second)
            self.assertIn("| 3.2 | x |", second)



class ReferenceTests(unittest.TestCase):
    def test_reference_in_sync(self):
        import subprocess, sys
        r = subprocess.run([sys.executable, os.path.join(TOOLS, "sync-reference.py"), "--check"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)


if __name__ == "__main__":
    unittest.main()
