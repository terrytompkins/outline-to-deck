#!/usr/bin/env python3
"""Fill in or verify the SRI hashes in tools/pins.json.

For every pinned file, downloads the cdnjs URL and the jsDelivr fallback URL,
computes a sha384 Subresource Integrity hash for each, and writes it to
pins.json. A URL that can't be downloaded gets "sri": null and a warning, so
the assembler knows not to use it.

Run it on a machine that can reach both CDNs (Claude's sandbox usually can't):

    python3 tools/update-pins.py            # fill in or refresh every hash
    python3 tools/update-pins.py --check    # verify the stored hashes, change nothing

Also reports whether each CDN file is byte-identical to the npm copy in
node_modules/ (after `npm install`), which tells you whether check-deck.py's
local copies test exactly what the deck will load.

Standard library only. Exit code: 0 all good, 1 a download failed or a hash differs.
"""
import argparse
import base64
import hashlib
import json
import pathlib
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
PINS = ROOT / "tools" / "pins.json"
CDNS = ("cdnjs", "jsdelivr")


def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": "outline-to-deck update-pins"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def sri(data):
    return "sha384-" + base64.b64encode(hashlib.sha384(data).digest()).decode()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="verify stored hashes; don't write")
    a = ap.parse_args()

    pins = json.loads(PINS.read_text())
    problems = 0
    for lib, spec in pins["libraries"].items():
        print(f"\n{lib} {spec['version']}")
        for name, f in spec["files"].items():
            local = ROOT / f["local"]
            local_hash = sri(local.read_bytes()) if local.is_file() else None
            for cdn in CDNS:
                entry = f[cdn]
                try:
                    data = fetch(entry["url"])
                except Exception as e:  # report every failure, keep going
                    print(f"  FAIL  {name:9} {cdn:8} {type(e).__name__}: {e}")
                    if not a.check:
                        entry["sri"] = None
                    problems += 1
                    continue
                h = sri(data)
                same_as_npm = "same as npm" if h == local_hash else (
                    "differs from npm" if local_hash else "npm copy not installed")
                if a.check:
                    status = "ok" if entry["sri"] == h else "MISMATCH"
                    problems += status != "ok"
                else:
                    status = "updated" if entry["sri"] != h else "unchanged"
                    entry["sri"] = h
                print(f"  {status:9} {name:9} {cdn:8} {len(data):>9,} bytes  {same_as_npm}")

    if not a.check:
        PINS.write_text(json.dumps(pins, indent=2) + "\n")
        print(f"\nWrote {PINS.relative_to(ROOT)}")
    print("All good." if not problems else f"{problems} problem(s).")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
