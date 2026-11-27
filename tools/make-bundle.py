#!/usr/bin/env python3
"""make-bundle: build deck-tools.zip, the tools bundle attached to a Claude Project chat (D24).

Project knowledge never appears on Claude's sandbox disk, so everything the tools need travels
in one zip: the tools, the runtime, the style CSS, pins, and the two registry files they read
(TAGS.md, LAYOUTS.md). A MANIFEST.json records the version and a SHA-256 for every file.

    python3 tools/make-bundle.py                # writes dist/deck-tools.zip
    python3 tools/make-bundle.py --out my.zip

Standard library only.
"""
import argparse
import datetime
import hashlib
import json
import os
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

FILES = [
    "tools/outline_parser.py", "tools/lint-outline.py", "tools/assemble-deck.py", "tools/check-deck.py",
    "tools/write-notes.py", "tools/render_blocks.py",
    "tools/pins.json", "runtime/deck.js", "runtime/base.css", "runtime/layouts.js", "runtime/layouts.css", "runtime/charts.js",
    "knowledge/TAGS.md", "knowledge/LAYOUTS.md", "package.json",
]

README = """# deck-tools bundle

Tools for building and checking outline-to-deck decks inside Claude's sandbox.
Unzip, then work from the unzipped folder:

    unzip -o deck-tools.zip -d /tmp/o2d && cd /tmp/o2d
    npm install --no-audit --no-fund          # local Reveal.js and Mermaid copies for the checker
    pip install playwright && playwright install chromium   # if not already installed

Put the presentation's OUTLINE.md and BRIEF.md in this folder (read them with project_read and
copy them here exactly), then:

    python3 tools/lint-outline.py OUTLINE.md --knowledge knowledge
    python3 tools/assemble-deck.py build --fragments frags --style STYLE --outline OUTLINE.md --out deck.html
    python3 tools/check-deck.py deck.html --outline OUTLINE.md --shots shots --json > check.json
    python3 tools/write-notes.py --outline OUTLINE.md --lint lint.json --check check.json --deck deck.html --style STYLE

STYLE is base, field-guide, toons, or the path to a style CSS file.
"""


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build deck-tools.zip.")
    ap.add_argument("--out", default=os.path.join(ROOT, "dist", "deck-tools.zip"))
    a = ap.parse_args(argv)
    files = list(FILES)
    styles = os.path.join(ROOT, "knowledge", "styles")
    files += sorted(f"knowledge/styles/{f}" for f in os.listdir(styles) if f.endswith(".css"))
    missing = [f for f in files if not os.path.exists(os.path.join(ROOT, f))]
    if missing:
        print("error: missing " + ", ".join(missing), file=sys.stderr)
        return 1
    try:
        commit = subprocess.run(["git", "-C", ROOT, "rev-parse", "--short", "HEAD"],
                                capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        commit = "unknown"
    manifest = {
        "bundle": "deck-tools",
        "built": datetime.date.today().isoformat(),
        "commit": commit,
        "files": {f: sha256(os.path.join(ROOT, f)) for f in files},
    }
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with zipfile.ZipFile(a.out, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(os.path.join(ROOT, f), f)
        z.writestr("MANIFEST.json", json.dumps(manifest, indent=2) + "\n")
        z.writestr("README-BUNDLE.md", README)
    print(f"Wrote {a.out}: {len(files)} files, commit {commit}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
