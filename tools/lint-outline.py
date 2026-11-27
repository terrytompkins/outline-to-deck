#!/usr/bin/env python3
"""lint-outline: check OUTLINE.md against TAGS.md, LAYOUTS.md and BRIEF.md.

Usage:
    python3 lint-outline.py OUTLINE.md [--knowledge DIR] [--brief BRIEF.md] [--json] [--no-info]

Errors (E) are meaning problems: Phase 2 stops on that slide. Warnings (W) are
fit or balance problems: Phase 2 falls back and records it. Notes (I) are
information, such as label splits. Exit code: 0 clean, 1 warnings or notes
only, 2 errors.

Standard library only. Run `--codes` to list every check.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from outline_parser import (Block, CALLOUT_RE, FENCE_RE, LIST_RE, _cells,  # noqa: E402
                            bracket_tags, load_registry, parse_outline,
                            plain_words, split_label)

CODES = {
    "E001": "Unknown tag in square brackets",
    "E002": "Unknown callout type",
    "E004": "Slide type is missing a required field",
    "E005": "Unknown, reserved or misplaced slide-type tag",
    "E006": "Unknown layout name",
    "E007": "Layout: line not followed by a bullet list",
    "E008": "Diagram: line and Mermaid block don't pair up",
    "E009": "Chart block is invalid",
    "E010": "Image: without Alt:",
    "E011": "Embed: URL isn't https",
    "E012": "Heading numbering or depth problem",
    "E013": "Slide type is missing its source link or As of date",
    "E014": "Time plan doesn't match the top-level sections",
    "W101": "More callouts on a slide than allowed",
    "W102": "Slide-type slide carries a callout or layout",
    "W103": "Tag used more often than its limit",
    "W104": "WATCHOUT on consecutive slides",
    "W105": "Too few vertical slides without a callout",
    "W106": "Layout content won't fit as written (fallback predicted)",
    "W107": "More layouts or diagrams on a slide than fit",
    "W108": "Too many slides with layouts in one section",
    "W109": "Top-level slide main points missing or outside 3-5",
    "W110": "Bullet longer than about 25 words",
    "W112": "Speaker notes inside a layout list",
    "W113": "Live time exceeds the session length",
    "W114": "Status comment missing or incomplete",
    "W115": "Diagram is larger than recommended",
    "W116": "Unnumbered section that isn't a known outline part",
    "W117": "Missing outline part",
    "W118": "Slide-type field outside its limits",
    "W119": "More than one emphasized item in a layout",
    "W120": "Tag that the active style renders more simply (a degrade)",
    "I201": "Layout label/detail splits",
    "I202": "Unknown layout option (ignored)",
    "I203": "Content bullets without an origin tag",
    "I204": "Audience tags not checked (BRIEF.md not found or not filled in)",
}

STATUS_FIELDS = ["version", "phase", "approved", "reviewed", "deck"]
LINK_RE = re.compile(r"\[[^\]\n]+\]\(https?://[^)\s]+\)")
ASOF_RE = re.compile(r"\bAs of [A-Z][a-z]+ \d{1,2}, \d{4}")
MERMAID_KEYWORDS = {"flowchart", "graph", "LR", "TD", "TB", "RL", "BT", "class", "classDef",
                    "subgraph", "end", "style", "linkStyle", "click", "direction"}


class Linter:
    def __init__(self, outline, reg):
        self.o, self.reg = outline, reg
        self.issues = []
        self.stats = {"slides": 0, "horizontal": 0, "vertical": 0, "tbd": [], "unverified": [],
                      "callouts": {}, "slide_types": {}, "layouts": {}, "diagrams": 0, "charts": 0,
                      "live_minutes": None, "unknown_audience": []}

    def add(self, code, line, msg, sec=None):
        sev = {"E": "error", "W": "warning", "I": "note"}[code[0]]
        self.issues.append({"code": code, "severity": sev, "line": line,
                            "section": sec.number if sec is not None else None, "message": msg})

    # ------------------------------------------------------------ helpers
    def canonical_callout(self, t):
        return self.reg.aliases.get(t, t)

    def slide_text(self, sec):
        return "\n".join(t for _, t in sec.body)

    def iter_items(self, items):
        for it in items:
            yield it
            yield from self.iter_items(it.children)

    # ------------------------------------------------------------ checks
    def run(self):
        self.check_parts()
        self.check_headings()
        self.check_inline_tags()
        for sec in self.o.slides:
            self.check_slide(sec)
        self.check_sections_and_deck()
        self.check_timeplan()
        self.check_status()
        return self.issues, self.stats

    def check_parts(self):
        kinds = {s.kind for s in self.o.sections}
        for kind, name in [("central", "Central message"), ("timeplan", "Time plan"),
                           ("front", "Front matter"), ("gaps", "Coverage gaps")]:
            if kind not in kinds:
                self.add("W117", 1, f"No '{name}' section.")

    def check_headings(self):
        seen = {}
        for s in self.o.sections:
            if s.level >= 4:
                self.add("E012", s.line, f"Heading '{s.raw}' is deeper than ####. Split the material or use a layout.", s)
                continue
            if s.kind == "other" and not s.outline_only and s.level >= 1:
                self.add("W116", s.line, f"Section '{s.title}' has no number and isn't a known outline part, so it won't appear in the deck.", s)
            if s.kind != "topic" or not s.number:
                continue
            depth = len(s.number.split("."))
            if depth != s.level:
                self.add("E012", s.line, f"Section {s.number} uses {'#' * (s.level + 1)}; a number with {depth} part(s) needs {'#' * (depth + 1)}.", s)
            if s.number in seen:
                self.add("E012", s.line, f"Section number {s.number} is used twice (also line {seen[s.number]}).", s)
            seen[s.number] = s.line
            if s.level > 1 and (s.parent is None or not s.number.startswith(s.parent.number + ".")):
                self.add("E012", s.line, f"Section {s.number} isn't under its parent section.", s)
            if s.slide_type is not None:
                if s.slide_type == "Demo":
                    self.add("E005", s.line, "[Demo] is reserved for v2.1.", s)
                elif s.slide_type not in self.reg.slide_types:
                    self.add("E005", s.line, f"Unknown slide type [{s.slide_type}].", s)
                if re.match(r"\[[^\]]+\]", s.title):
                    self.add("E005", s.line, "More than one slide-type tag in the heading.", s)
            for tag in s.tags:
                self.check_tag(tag, s.line, s, in_heading=True)

    def check_tag(self, tag, line, sec, in_heading=False):
        t = tag.strip()
        if t.startswith("!") or t in (" ", "x", "X"):
            return
        on_slide = sec.kind in ("topic", "front") and not sec.outline_only   # working aids don't count
        if t.startswith("TBD:"):
            if on_slide:
                self.stats["tbd"].append(sec.number or sec.title)
            return
        if t == "TBD" or t.startswith("TBD "):
            self.add("E001", line, "Write placeholders as [TBD: description].", sec)
            return
        if t == "UNVERIFIED" or t.startswith("UNVERIFIED:"):
            if on_slide:
                self.stats["unverified"].append(sec.number or sec.title)
            return
        if t in self.reg.working_aids:
            return
        if self.reg.audience_known and t in self.reg.audience:
            return
        if not self.reg.audience_known and in_heading:
            if t not in self.stats["unknown_audience"]:
                self.stats["unknown_audience"].append(t)
            return
        if t in self.reg.slide_types:
            self.add("E001", line, f"[{t}] is a slide type; put it right after the section number in a heading, or write it in backticks.", sec)
            return
        self.add("E001", line, f"Unknown tag [{t}].", sec)

    def check_inline_tags(self):
        for s in self.o.sections:
            in_fence, fence = False, ""
            for ln, text in s.body:
                fm = FENCE_RE.match(text)
                if fm and (not in_fence or text.startswith(fence[:3])):
                    in_fence, fence = (not in_fence), fm.group(1)
                    continue
                if in_fence or "<!--" in text:
                    continue
                if CALLOUT_RE.match(text):
                    text = CALLOUT_RE.sub(r"\2", text)
                for tag in bracket_tags(text):
                    self.check_tag(tag, ln, s)

    def check_slide(self, sec):
        st = self.stats
        st["slides"] += 1
        st["horizontal" if sec.level == 1 else "vertical"] += 1
        blocks = sec.blocks
        text = self.slide_text(sec)
        callouts = [b for b in blocks if b.kind == "callout"]
        layouts = [b for b in blocks if b.kind == "layout"]
        sec._callouts = [self.canonical_callout(b.key) for b in callouts]
        sec._layouts = layouts

        for b in callouts:
            if b.key not in self.reg.callouts and b.key not in self.reg.aliases:
                self.add("E002", b.line, f"Unknown callout type [!{b.key}].", sec)
            else:
                k = self.canonical_callout(b.key)
                st["callouts"][k] = st["callouts"].get(k, 0) + 1
        if len(callouts) > self.reg.limits.get("callouts-per-slide", 1):
            self.add("W101", callouts[1].line, f"{len(callouts)} callouts on this slide; the limit is {int(self.reg.limits.get('callouts-per-slide', 1))}.", sec)

        # slide types
        if sec.slide_type in self.reg.degrades:
            self.add("W120", sec.line, f"The active style renders [{sec.slide_type}] as: {self.reg.degrades[sec.slide_type]}.", sec)
        for b in blocks:
            if b.kind == "key" and b.key in self.reg.degrades:
                self.add("W120", b.line, f"The active style renders {b.key}: as: {self.reg.degrades[b.key]}.", sec)
        if sec.slide_type in self.reg.slide_types:
            st["slide_types"][sec.slide_type] = st["slide_types"].get(sec.slide_type, 0) + 1
            self.check_slide_type(sec, text)
            if callouts or layouts:
                self.add("W102", sec.line, f"[{sec.slide_type}] slides carry no callouts or layouts.", sec)

        # main points on top-level slides
        if sec.level == 1:
            mp = next((i for i, b in enumerate(blocks) if b.kind == "key" and b.key == "Main points"), None)
            if mp is None:
                self.add("W109", sec.line, "Top-level slide has no 'Main points:' list.", sec)
            else:
                items = blocks[mp].items
                if not items and mp + 1 < len(blocks) and blocks[mp + 1].kind == "layout":
                    items = blocks[mp + 1].items
                if not 3 <= len(items) <= 5:
                    self.add("W109", blocks[mp].line, f"Main points has {len(items)} bullet(s); use 3-5.", sec)

        # layouts
        for b in layouts:
            self.check_layout(sec, b)
        lim = int(self.reg.limits.get("layouts-per-slide", 2))
        if len(layouts) > lim:
            self.add("W107", layouts[lim].line, f"{len(layouts)} layouts on one slide; beyond {lim} they move to a continued slide.", sec)

        # diagrams and fences
        diagrams = 0
        for i, b in enumerate(blocks):
            if b.kind == "key" and b.key == "Diagram":
                nxt = blocks[i + 1] if i + 1 < len(blocks) else None
                if not (nxt and nxt.kind == "fence" and nxt.key == "mermaid"):
                    self.add("E008", b.line, "Diagram: needs Claude's Mermaid block directly below it.", sec)
            if b.kind == "fence" and b.key == "mermaid":
                diagrams += 1
                prev = blocks[i - 1] if i > 0 else None
                if not (prev and prev.kind == "key" and prev.key == "Diagram"):
                    self.add("E008", b.line, "Mermaid block without a 'Diagram:' line describing it in plain language.", sec)
                self.check_mermaid(sec, b, two=False)
            if b.kind == "fence" and b.key == "chart":
                st["charts"] += 1
                self.check_chart(sec, b)
            if b.kind == "key" and b.key == "Image":
                rest = blocks[i + 1:i + 4]
                if not any(r.kind == "key" and r.key == "Alt" and r.text for r in rest):
                    self.add("E010", b.line, "Image: needs an 'Alt:' line describing the picture.", sec)
            if b.kind == "key" and b.key == "Embed" and not b.text.startswith("https://"):
                self.add("E011", b.line, "Embed: takes an https:// URL.", sec)
        st["diagrams"] += diagrams
        lim = int(self.reg.limits.get("diagrams-per-slide", 2))
        if diagrams > lim:
            self.add("W107", sec.line, f"{diagrams} diagrams on one slide; beyond {lim} they move to a continued slide.", sec)
        if diagrams == 2:
            for b in blocks:
                if b.kind == "fence" and b.key == "mermaid":
                    self.check_mermaid(sec, b, two=True, report_only_two=True)

        # bullet length and origin tags
        heading_origin = any(t in ("Seed", "Research") for t in sec.tags)
        sec._no_origin = 0
        for b in blocks:
            items = []
            if b.kind == "list" or (b.kind == "key" and b.key == "Main points"):
                items = list(self.iter_items(b.items))
            for it in items:
                if plain_words(it.text) > 25:
                    self.add("W110", it.line, f"Bullet has {plain_words(it.text)} words; keep to about 25 and move detail to speaker notes.", sec)
                if not heading_origin and not re.search(r"\[(Seed|Research)\]", it.text):
                    sec._no_origin += 1

    def check_slide_type(self, sec, text):
        spec = self.reg.slide_types[sec.slide_type]
        keys = [b for b in sec.blocks if b.kind == "key"]
        present = {b.key for b in keys}
        for req in spec["required"]:
            if req not in present:
                self.add("E004", sec.line, f"[{sec.slide_type}] needs a '{req}:' line.", sec)
        for b in keys:
            if b.key in ("Steps", "Options", "Points") and not b.items and not b.text:
                self.add("E004", b.line, f"'{b.key}:' needs a list directly below it.", sec)
        if sec.slide_type == "Myth vs fact":
            myths = sum(1 for b in keys if b.key == "Myth")
            facts = sum(1 for b in keys if b.key == "Fact")
            if myths != facts:
                self.add("E004", sec.line, f"{myths} Myth: line(s) but {facts} Fact: line(s); they come in pairs.", sec)
            elif not 1 <= myths <= 3:
                self.add("W118", sec.line, f"{myths} myth/fact pairs; use 1-3.", sec)
        for b in keys:
            if b.key == "Points" and b.items and not 3 <= len(b.items) <= 4:
                self.add("W118", b.line, f"Points has {len(b.items)} bullets; use 3-4.", sec)
            if b.key == "Options" and b.items and not 2 <= len(b.items) <= 4:
                self.add("W118", b.line, f"Options has {len(b.items)} bullets; use 2-4.", sec)
            if b.key == "Quote" and plain_words(b.text) > 40:
                self.add("W118", b.line, f"Quote has {plain_words(b.text)} words; keep to 40.", sec)
            if b.key == "Label" and sec.slide_type == "Key figure" and plain_words(b.text) > 8:
                self.add("W118", b.line, f"Label has {plain_words(b.text)} words; keep to 8.", sec)
        if spec["needs_source"] and not LINK_RE.search(text):
            self.add("E013", sec.line, f"[{sec.slide_type}] needs a source link.", sec)
        if spec["needs_asof"] and not ASOF_RE.search(text):
            self.add("E013", sec.line, f"[{sec.slide_type}] needs an 'As of Month D, YYYY' date.", sec)

    def check_layout(self, sec, b):
        reg = self.reg
        name = b.key
        if name not in reg.layouts:
            self.add("E006", b.line, f"Unknown layout '{name}'. Known: {', '.join(reg.layouts)}.", sec)
            return
        spec = reg.layouts[name]
        self.stats["layouts"][name] = self.stats["layouts"].get(name, 0) + 1
        if not b.items:
            self.add("E007", b.line, "Layout: must sit directly above the bullet list it renders.", sec)
            return
        for opt in b.options:
            if opt not in spec["variants"] and opt not in ("build", "numbered"):
                self.add("I202", b.line, f"Option '{opt}' isn't known for '{name}' and will be ignored.", sec)
        for f in b.fields:
            if f not in spec["fields"]:
                self.add("I202", b.line, f"'{f}:' doesn't apply to '{name}' and will be ignored.", sec)
        top = b.items
        shape = spec["shape"]
        fb = spec["fallback"]
        fb_txt = "a continued slide" if fb == "split" else f"'{fb}'"

        def fit(msg):
            self.add("W106", b.line, f"{name}: {msg} Phase 2 will fall back to {fb_txt}.", sec)

        all_items = list(self.iter_items(top))
        if shape in ("tree", "radial"):
            if len(top) != 1:
                fit(f"needs exactly one top-level bullet (the {'root' if shape == 'tree' else 'center'}); found {len(top)}.")
                return
            if shape == "radial":
                count = len(top[0].children)
                if any(c.children for c in top[0].children):
                    fit("spokes can't have their own sub-bullets.")
            else:
                count = len(all_items)
                def depth(it, d=0):
                    return max([d] + [depth(c, d + 1) for c in it.children])
                if depth(top[0]) > 3:
                    fit("nests more than three levels below the root.")
        elif shape == "columns":
            count = len(top)
            for col in top:
                if not 1 <= len(col.children) <= 5:
                    fit(f"column '{split_label(col.text)[0]}' has {len(col.children)} sub-bullets; use 1-5.")
        else:
            count = len(top)
            if shape != "list" and any(it.children for it in top):
                fit("items in this layout can't have sub-bullets.")
        if not spec["min"] <= count <= spec["max"]:
            what = {"columns": "columns", "tree": "nodes", "radial": "spokes"}.get(shape, "items")
            fit(f"{count} {what}; it takes {spec['min']}-{spec['max']}.")
        splits, keys = [], 0
        for it in all_items:
            if re.search(r"\bSpeaker notes:", it.text):
                self.add("W112", it.line, "Move 'Speaker notes:' below the layout list.", sec)
            label, detail, is_key = split_label(it.text)
            keys += is_key
            if detail:
                splits.append(label)
            if plain_words(label) > spec["label_words"]:
                fit(f"label '{label}' has {plain_words(label)} words; keep to {spec['label_words']}.")
            if detail and spec["detail_words"] == 0:
                fit(f"'{label}' has a detail; this layout shows labels only (details move to speaker notes).")
            elif detail and plain_words(detail) > spec["detail_words"]:
                fit(f"detail for '{label}' has {plain_words(detail)} words; keep to {spec['detail_words']}.")
        if keys > 1:
            self.add("W119", b.line, f"{keys} bold items; only one item can be emphasized.", sec)
        if splits:
            self.add("I201", b.line, f"{name}: split into label and detail at the colon for: {', '.join(splits)}.", sec)

    def check_mermaid(self, sec, b, two=False, report_only_two=False):
        src = "\n".join(b.lines)
        first = next((l.strip() for l in b.lines if l.strip()), "")
        if not re.match(r"(flowchart|graph)\b", first):
            return
        nodes = set()
        for m in re.finditer(r"(?<![\w\"])([A-Za-z_][\w]*)\s*(?=[\[\(\{>]|-->|---|-\.->|==>|--\s|&)", src):
            nodes.add(m.group(1))
        for m in re.finditer(r"(?:-->|---|==>|-\.->)\s*(?:\|[^|]*\|\s*)?([A-Za-z_][\w]*)", src):
            nodes.add(m.group(1))
        nodes -= MERMAID_KEYWORDS
        limit = 5 if two else 9
        if report_only_two and len(nodes) <= limit:
            return
        if len(nodes) > limit:
            self.add("W115", b.line, f"Diagram has about {len(nodes)} nodes; keep to about {limit}{' when two share a slide' if two else ''}.", sec)
        if report_only_two:
            return
        for lab in re.findall(r"[\[\(\{]\"?([^\]\)\}\"]+)\"?[\]\)\}]", src):
            if len(lab.split()) > 6:
                self.add("W115", b.line, f"Diagram label '{lab.strip()}' has {len(lab.split())} words; keep to 6.", sec)

    def check_chart(self, sec, b):
        kv, table = {}, []
        for l in b.lines:
            if l.strip().startswith("|"):
                table.append(l)
            elif ":" in l and not table:
                k, v = l.split(":", 1)
                kv[k.strip().lower()] = v.strip()
        if kv.get("type") not in ("bar", "column", "line"):
            self.add("E009", b.line, "chart needs 'type: bar', 'type: column' or 'type: line'.", sec)
        if not kv.get("title"):
            self.add("E009", b.line, "chart needs a 'title:' line.", sec)
        rows = [_cells(r) for r in table if not re.fullmatch(r"\|?[\s|:-]+\|?", r.strip())]
        if len(rows) < 2:
            self.add("E009", b.line, "chart needs a table: a header row and at least one data row.", sec)
            return
        header, data = rows[0], rows[1:]
        if len(header) < 2:
            self.add("E009", b.line, "chart table needs a category column and at least one series column.", sec)
        if len(header) - 1 > 5:
            self.add("E009", b.line, f"chart has {len(header) - 1} series; the limit is 5.", sec)
        if len(data) > 12:
            self.add("E009", b.line, f"chart has {len(data)} categories; the limit is 12.", sec)
        for r in data:
            for c in r[1:]:
                if not re.fullmatch(r"-?[\d,]*\.?\d+%?", c.replace(" ", "")):
                    self.add("E009", b.line, f"chart cell '{c}' isn't a number (no placeholders inside charts).", sec)
                    return

    def check_sections_and_deck(self):
        slides = self.o.slides
        by_top = {}
        for s in slides:
            by_top.setdefault(s.top_number, []).append(s)
        reg = self.reg
        for top, group in by_top.items():
            # per-section limits for callouts and slide types
            for t, spec in reg.callouts.items():
                n = sum(s._callouts.count(t) for s in group)
                for lim, scope in spec["limits"]:
                    if scope == "section" and n > lim:
                        self.add("W103", group[0].line, f"Section {top} has {n} {t} callouts; the limit is {lim} per section.", group[0])
            for name, spec in reg.slide_types.items():
                n = sum(1 for s in group if s.slide_type == name)
                for lim, scope in spec["limits"]:
                    if scope == "section" and n > lim:
                        self.add("W103", group[0].line, f"Section {top} has {n} [{name}] slides; the limit is {lim} per section.", group[0])
            with_layout = sum(1 for s in group if s._layouts)
            share = reg.limits.get("section-layout-share", 0.5)
            if with_layout > max(1, math.floor(share * len(group))):
                self.add("W108", group[0].line, f"Section {top}: {with_layout} of {len(group)} slides carry a layout; aim for at most {int(share * 100)}%.", group[0])
        for name, spec in reg.slide_types.items():
            n = sum(1 for s in slides if s.slide_type == name)
            for lim, scope in spec["limits"]:
                if scope == "deck" and n > lim:
                    self.add("W103", 1, f"{n} [{name}] slides in the deck; the limit is {lim}.")
        vertical = [s for s in slides if s.level > 1]
        if vertical:
            bare = sum(1 for s in vertical if not s._callouts)
            need = reg.limits.get("deck-no-callout-share", 0.5)
            if bare / len(vertical) < need:
                self.add("W105", 1, f"Only {bare} of {len(vertical)} vertical slides have no callout; aim for at least {int(need * 100)}%.")
        if str(reg.limits.get("watchout-consecutive", "no")).strip("`") == "no":
            for a, b in zip(slides, slides[1:]):
                if "WATCHOUT" in a._callouts and "WATCHOUT" in b._callouts:
                    self.add("W104", b.line, f"WATCHOUT on consecutive slides {a.number} and {b.number}.", b)
        no_origin = sum(getattr(s, "_no_origin", 0) for s in slides)
        if no_origin:
            self.add("I203", 1, f"{no_origin} content bullet(s) have no [Seed] or [Research] tag and no origin tag on their heading.")
        if self.stats["unknown_audience"]:
            self.add("I204", 1, "BRIEF.md has no audience tags filled in, so these heading tags were accepted as audience tags without checking: "
                     + ", ".join("[" + t + "]" for t in self.stats["unknown_audience"]) + ".")

    def check_timeplan(self):
        tp_sec = next((s for s in self.o.sections if s.kind == "timeplan"), None)
        if tp_sec is None:
            return
        table = next((b for b in tp_sec.blocks if b.kind == "table"), None)
        if table is None:
            self.add("E014", tp_sec.line, "Time plan has no table.", tp_sec)
            return
        header = [h.lower() for h in _cells(table.lines[0])]
        live_col = next((i for i, h in enumerate(header) if h.startswith("live")), None)
        prio_col = next((i for i, h in enumerate(header) if h.startswith("priority")), None)
        tops = {s.number: s for s in self.o.slides if s.level == 1}
        listed, total = {}, 0.0
        for row in self.o.timeplan:
            cells = row["cells"]
            label = " ".join(cells).lower()
            if "total" in label:
                continue
            if live_col is not None and live_col < len(cells):
                m = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*", cells[live_col])
                if m:
                    total += float(m.group(1))
            n = row["number"]
            if n is None:
                continue
            if n in listed:
                self.add("E014", row["line"], f"Section {n} appears twice in the time plan.")
            listed[n] = row
            if n not in tops:
                self.add("E014", row["line"], f"Time plan lists section {n}, which doesn't exist.")
            if prio_col is not None and prio_col < len(cells) and cells[prio_col] not in ("Core", "Brief", "Self-guided", ""):
                self.add("E014", row["line"], f"Priority '{cells[prio_col]}' should be Core, Brief or Self-guided.")
        for n, s in tops.items():
            if n not in listed:
                self.add("E014", s.line, f"Section {n} isn't in the time plan.", s)
        self.stats["live_minutes"] = total
        session = self.reg.brief.get("session_minutes")
        if session and total > session:
            self.add("W113", table.line, f"Live time totals {total:g} minutes; the session is {session}.")

    def check_status(self):
        if not self.o.status:
            self.add("W114", 1, "No '<!-- status: ... -->' comment at the top of the outline.")
            return
        missing = [f for f in STATUS_FIELDS if f not in self.o.status]
        if missing:
            self.add("W114", 1, f"Status comment is missing: {', '.join(missing)}.")


def format_report(issues, stats, show_info=True):
    out = []
    order = {"error": 0, "warning": 1, "note": 2}
    shown = [i for i in issues if show_info or i["severity"] != "note"]
    for i in sorted(shown, key=lambda i: (order[i["severity"]], i["line"])):
        sec = f" §{i['section']}" if i["section"] else ""
        out.append(f"{i['severity'].upper():7} {i['code']} line {i['line']}{sec}: {i['message']}")
    n = {s: sum(1 for i in issues if i["severity"] == s) for s in order}
    out.append("")
    out.append(f"{n['error']} error(s), {n['warning']} warning(s), {n['note']} note(s).")
    out.append(f"Slides: {stats['slides']} ({stats['horizontal']} horizontal, {stats['vertical']} vertical). "
               f"Live time: {stats['live_minutes'] if stats['live_minutes'] is not None else '?'} min.")
    out.append(f"[TBD]: {len(stats['tbd'])}" + (f" ({', '.join(stats['tbd'])})" if stats["tbd"] else "")
               + f". [UNVERIFIED]: {len(stats['unverified'])}" + (f" ({', '.join(stats['unverified'])})" if stats["unverified"] else "") + ".")
    def fmt(d):
        return ", ".join(f"{k} {v}" for k, v in sorted(d.items())) or "none"
    out.append(f"Callouts: {fmt(stats['callouts'])}. Slide types: {fmt(stats['slide_types'])}.")
    out.append(f"Layouts: {fmt(stats['layouts'])}. Diagrams: {stats['diagrams']}. Charts: {stats['charts']}.")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check OUTLINE.md against the tag registry.")
    ap.add_argument("outline", nargs="?")
    ap.add_argument("--knowledge", help="folder with TAGS.md and LAYOUTS.md (default: next to the outline, else ../knowledge)")
    ap.add_argument("--brief", help="BRIEF.md (default: in the knowledge folder or next to the outline)")
    ap.add_argument("--json", action="store_true", help="print issues and counts as JSON")
    ap.add_argument("--no-info", action="store_true", help="hide notes (I codes) in the text report")
    ap.add_argument("--codes", action="store_true", help="list every check and exit")
    a = ap.parse_args(argv)
    if a.codes:
        for c, d in CODES.items():
            print(f"{c}  {d}")
        return 0
    if not a.outline:
        ap.error("give the path to OUTLINE.md")
    here = os.path.dirname(os.path.abspath(a.outline))
    kdir = a.knowledge or (here if os.path.exists(os.path.join(here, "TAGS.md"))
                           else os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "knowledge"))
    brief = a.brief or next((p for p in (os.path.join(here, "BRIEF.md"), os.path.join(kdir, "BRIEF.md")) if os.path.exists(p)), None)
    reg = load_registry(kdir, brief_path=brief or os.path.join(kdir, "BRIEF.md"))
    with open(a.outline, encoding="utf-8") as f:
        outline = parse_outline(f.read(), reg)
    issues, stats = Linter(outline, reg).run()
    if a.json:
        print(json.dumps({"issues": issues, "stats": stats}, indent=2))
    else:
        print(format_report(issues, stats, show_info=not a.no_info))
    if any(i["severity"] == "error" for i in issues):
        return 2
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
