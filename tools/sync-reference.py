#!/usr/bin/env python3
"""sync-reference: regenerate the catalog tables in docs/REFERENCE.md from the registries.

Each block between <!-- generated: NAME --> and <!-- /generated --> is replaced with the
registry table of that name from knowledge/TAGS.md or knowledge/LAYOUTS.md, so the reference
can't drift from the rules Claude follows.

    python3 tools/sync-reference.py           # rewrite docs/REFERENCE.md
    python3 tools/sync-reference.py --check   # exit 1 if it is out of date
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REF = os.path.join(ROOT, "docs", "REFERENCE.md")
SOURCES = [os.path.join(ROOT, "knowledge", "TAGS.md"), os.path.join(ROOT, "knowledge", "LAYOUTS.md")]
TABLE_RE = re.compile(r"<!-- registry: ([\w-]+) -->\n((?:\|.*\|[ \t]*\n?)+)")
BLOCK_RE = re.compile(r"(<!-- generated: ([\w-]+) -->\n)(.*?)(<!-- /generated -->)", re.S)


def tables():
    out = {}
    for path in SOURCES:
        with open(path, encoding="utf-8") as f:
            for m in TABLE_RE.finditer(f.read()):
                out[m.group(1)] = m.group(2).rstrip("\n") + "\n"
    return out


def render(text, found):
    missing = []

    def repl(m):
        name = m.group(2)
        if name not in found:
            missing.append(name)
            return m.group(0)
        source = "TAGS.md" if name != "layouts" and name != "layout-proposals" else "LAYOUTS.md"
        return f"{m.group(1)}_Generated from `knowledge/{source}`; edit it there._\n\n{found[name]}{m.group(4)}"
    return BLOCK_RE.sub(repl, text), missing


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    with open(REF, encoding="utf-8") as f:
        old = f.read()
    new, missing = render(old, tables())
    if missing:
        print("error: no registry table named " + ", ".join(missing), file=sys.stderr)
        return 1
    if a.check:
        if new != old:
            print("docs/REFERENCE.md is out of date: run python3 tools/sync-reference.py", file=sys.stderr)
            return 1
        print("docs/REFERENCE.md is up to date.")
        return 0
    with open(REF, "w", encoding="utf-8") as f:
        f.write(new)
    print("Updated docs/REFERENCE.md." if new != old else "docs/REFERENCE.md was already up to date.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
