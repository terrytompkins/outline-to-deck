"""outline_parser: read the tag registry and parse OUTLINE.md.

Shared by lint-outline.py, assemble-deck.py and check-deck.py. Standard
library only, so it runs in any sandbox without installs.

    from outline_parser import load_registry, parse_outline
    reg = load_registry("knowledge")          # TAGS.md + LAYOUTS.md
    outline = parse_outline(open("OUTLINE.md").read(), reg)

The registry comes from the tables marked <!-- registry: NAME --> in
TAGS.md and LAYOUTS.md. Nothing about tags is hard-coded here except the
syntax of the five forms.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

# ---------------------------------------------------------------- registry

REG_RE = re.compile(r"<!-- registry: ([\w-]+) -->\n((?:\|.*\|[ \t]*\n?)+)")
BACKTICK_KEY_RE = re.compile(r"`([A-Z][A-Za-z ]*):`")
BRACKET_RE = re.compile(r"`?\[([^\]\n]+)\]`?")


def _cells(row: str) -> list[str]:
    return [c.strip() for c in row.strip().strip("|").split("|")]


def read_registry_tables(text: str) -> dict[str, list[dict[str, str]]]:
    """Return {table_name: [ {header: cell} ]} for every marked table."""
    tables = {}
    for m in REG_RE.finditer(text):
        rows = [r for r in m.group(2).strip().split("\n") if r.strip()]
        header = _cells(rows[0])
        body = [_cells(r) for r in rows[2:]]
        tables[m.group(1)] = [dict(zip(header, r)) for r in body if len(r) == len(header)]
    return tables


def _strip_ticks(s: str) -> str:
    return s.strip().strip("`").strip()


def _parse_limit(text: str) -> list[tuple[int, str]]:
    """'1 per slide; ≤ 2 per section' -> [(1,'slide'), (2,'section')]."""
    return [(int(n), scope) for n, scope in re.findall(r"(\d+)\s+per\s+(slide|section|deck)", text)]


@dataclass
class Registry:
    callouts: dict = field(default_factory=dict)        # TYPE -> {label, limits}
    aliases: dict = field(default_factory=dict)         # ALIAS -> TYPE
    slide_types: dict = field(default_factory=dict)     # name -> {required, optional, needs_source, needs_asof, limits}
    directives: dict = field(default_factory=dict)      # key -> {companions}
    blocks: list = field(default_factory=list)          # fence languages with special meaning
    limits: dict = field(default_factory=dict)          # id -> value
    working_aids: set = field(default_factory=set)      # bracket tags that are stripped
    layouts: dict = field(default_factory=dict)         # name -> {...}
    layout_fields: set = field(default_factory=set)
    audience: set = field(default_factory=set)          # from BRIEF.md, may be empty
    audience_known: bool = False
    brief: dict = field(default_factory=dict)           # parsed BRIEF.md fields
    degrades: dict = field(default_factory=dict)        # tag -> how the active style renders it instead

    @property
    def field_keys(self) -> set:
        keys = set()
        for st in self.slide_types.values():
            keys |= set(st["required"]) | set(st["optional"])
        return keys


def load_registry(knowledge_dir: str, brief_path: str | None = None) -> Registry:
    reg = Registry()
    with open(os.path.join(knowledge_dir, "TAGS.md"), encoding="utf-8") as f:
        t = read_registry_tables(f.read())

    for row in t.get("callouts", []):
        reg.callouts[_strip_ticks(row["Type"])] = {
            "label": row["Default label"], "limits": _parse_limit(row["Limit"])}
    for row in t.get("callout-aliases", []):
        reg.aliases[_strip_ticks(row["Alias"])] = _strip_ticks(row["Renders as"])

    for row in t.get("slide-types", []):
        name = _strip_ticks(row["Tag"]).strip("[]")
        req = row["Required fields"]
        reg.slide_types[name] = {
            "required": BACKTICK_KEY_RE.findall(req),
            "optional": BACKTICK_KEY_RE.findall(row["Optional fields"]),
            "needs_source": "source link" in req,
            "needs_asof": "`As of`" in req,
            "limits": _parse_limit(row["Limit"]),
        }
    for row in t.get("directives", []):
        key = BACKTICK_KEY_RE.findall(row["Key"])
        if key:
            reg.directives[key[0]] = {"companions": BACKTICK_KEY_RE.findall(row["Companions"])}
    for row in t.get("blocks", []):
        lang = _strip_ticks(row["Block"])
        if re.fullmatch(r"[a-z]+", lang):
            reg.blocks.append(lang)
    for row in t.get("limits", []):
        v = row["Value"]
        reg.limits[_strip_ticks(row["ID"])] = float(v) if re.fullmatch(r"[\d.]+", v) else v
    for row in t.get("working-aids", []):
        for tag in re.findall(r"`\[([^\]]+)\]`", row["Tag"]):
            reg.working_aids.add(tag)

    lay_path = os.path.join(knowledge_dir, "LAYOUTS.md")
    if os.path.exists(lay_path):
        with open(lay_path, encoding="utf-8") as f:
            lt = read_registry_tables(f.read())
        for row in lt.get("layouts", []):
            lo, hi = (int(x) for x in re.findall(r"\d+", row["Items"])[:2])
            variants = [] if row["Variants"] in ("—", "") else [v.strip() for v in row["Variants"].split(",")]
            fields = [] if row["Fields"] in ("—", "") else [v.strip() for v in row["Fields"].split(",")]
            reg.layouts[_strip_ticks(row["Name"])] = {
                "shape": row["Shape"], "min": lo, "max": hi,
                "label_words": int(row["Label words"]), "detail_words": int(row["Detail words"]),
                "variants": variants, "fields": fields,
                "fallback": row["Fallback"], "renderer": row["Renderer"]}
            reg.layout_fields |= set(fields)

    brief = brief_path or os.path.join(knowledge_dir, "BRIEF.md")
    if os.path.exists(brief):
        with open(brief, encoding="utf-8") as f:
            reg.brief = parse_brief(f.read())
        if reg.brief.get("audience") is not None:
            reg.audience = set(reg.brief["audience"])
            reg.audience_known = True
    else:
        reg.brief = {}
    style = reg.brief.get("style")
    for cand in ((os.path.join(knowledge_dir, "styles", style), os.path.join(knowledge_dir, style)) if style else ()):
        if os.path.exists(cand):
            with open(cand, encoding="utf-8") as f:
                reg.degrades = parse_degrades(f.read())
            break
    return reg


def parse_degrades(text: str) -> dict:
    """The '## 9. Degrades' table of a style guide: {tag: renders as}."""
    m = re.search(r"^## \d+\. Degrades\s*\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    out = {}
    if not m:
        return out
    for line in m.group(1).split("\n"):
        cells = _cells(line) if line.strip().startswith("|") else []
        if len(cells) >= 2 and "`" in cells[0] and not cells[0].startswith("[e.g."):
            for tag in re.findall(r"`([^`]+)`", cells[0]):
                out[tag.strip("[]").rstrip(":")] = cells[1]
    return out


def parse_brief(text: str) -> dict:
    out = {}
    m = re.search(r"\*\*Audience tags to use in the outline:\*\*\s*(.*)", text)
    if m and "TBD" not in m.group(1):
        val = m.group(1)
        out["audience"] = [] if re.search(r"\bnone\b", val, re.I) else re.findall(r"\[([^\]]+)\]", val)
    m = re.search(r"\*\*Session length:\*\*\s*(\d+)", text)
    if m:
        out["session_minutes"] = int(m.group(1))
    m = re.search(r"\*\*Active style:\*\*\s*`?(STYLE-[\w-]+\.md)", text)
    if m:
        out["style"] = m.group(1)
    m = re.search(r"\*\*Layout use:\*\*\s*(encourage|sparingly|off)", text, re.I)
    if m:
        out["layout_use"] = m.group(1).lower()
    return out

# ---------------------------------------------------------------- outline model

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
NUM_RE = re.compile(r"^(\d+(?:\.\d+)*)(\.?)\s+(.*)$")
LIST_RE = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$")
KEY_RE = re.compile(r"^([A-Z][A-Za-z ]{0,24}):(?:\s+(.*)|\s*)$")
CALLOUT_RE = re.compile(r"^>\s*\[!([A-Za-z]+)\]\s*(.*)$")
FENCE_RE = re.compile(r"^(`{3,}|~{3,})\s*([\w-]*)")
STATUS_RE = re.compile(r"<!--\s*status:\s*(.*?)\s*-->")
OUTLINE_ONLY = "(outline-only working aid)"
ALWAYS_KEYS = {"Speaker notes", "Main points"}
FRONT_KEYS = {"Title", "Series", "Framing line"}


@dataclass
class Item:
    text: str
    line: int
    indent: int
    ordered: bool
    children: list = field(default_factory=list)


@dataclass
class Block:
    kind: str            # para | list | key | callout | fence | table | layout | quote
    line: int
    text: str = ""       # para/quote text, key value, callout title
    key: str = ""        # key name; callout type; fence language; layout name
    items: list = field(default_factory=list)    # list/layout items; key's attached list
    lines: list = field(default_factory=list)    # fence/table/callout body lines
    options: list = field(default_factory=list)  # layout options
    fields: dict = field(default_factory=dict)   # layout fields


@dataclass
class Section:
    level: int           # 1 = '##', 2 = '###', 3 = '####'; 0 = '#'
    raw: str
    line: int
    number: str | None = None
    title: str = ""
    slide_type: str | None = None
    tags: list = field(default_factory=list)
    outline_only: bool = False
    kind: str = "topic"  # topic | front | central | timeplan | changes | reconciliation | gaps | other | title
    body: list = field(default_factory=list)     # (lineno, text)
    blocks: list = field(default_factory=list)
    parent: "Section | None" = None

    @property
    def is_slide(self) -> bool:
        return self.kind == "topic" and self.number is not None and not self.outline_only

    @property
    def top_number(self) -> str | None:
        return self.number.split(".")[0] if self.number else None


@dataclass
class Outline:
    sections: list
    status: dict
    timeplan: list         # [{'number': '3', 'cells': [...], 'line': n}]
    lines: list

    @property
    def slides(self):
        return [s for s in self.sections if s.is_slide]


def strip_inline_code(text: str) -> str:
    return re.sub(r"`[^`]*`", "", text)


def bracket_tags(text: str) -> list[str]:
    """Bracket tags in text, ignoring Markdown links and inline code."""
    t = strip_inline_code(text)
    t = re.sub(r"\[[^\]\n]*\]\([^)]*\)", "", t)   # [text](url)
    return re.findall(r"\[([^\]\n]+)\]", t)


def plain_words(text: str) -> int:
    t = re.sub(r"\[([^\]\n]*)\]\([^)]*\)", r"\1", text)
    t = re.sub(r"\[[^\]\n]*\]", "", t)
    t = re.sub(r"[*_`]", "", t)
    t = re.sub(r"\(\s*\)", "", t)
    return len(t.split())


def split_label(text: str) -> tuple[str, str, bool]:
    """Apply the layout label/detail rule. Returns (label, detail, is_key)."""
    m = re.match(r"^(.*?)((?:\s*\[[^\]\n]+\](?!\())*)\s*$", text.strip())
    t, trailing = m.group(1).strip(), m.group(2).strip()
    is_key = bool(re.fullmatch(r"\*\*[^*].*\*\*", t))
    if is_key:
        t = t[2:-2].strip()
    label, detail = t, ""
    m = re.search(r"(?<!\\): ", t)
    if m:
        before = t[:m.start()]
        if len(before.split()) <= 5 and not re.search(r"[\[\]()`*_<>]", before):
            label, detail = before.strip(), t[m.end():].strip()
    label = label.replace("\\:", ":")
    if trailing:                       # inline tags stay with the item's text
        if detail:
            detail = f"{detail} {trailing}"
        else:
            label = f"{label} {trailing}"
    return label, detail, is_key


def _parse_heading(level_marks: str, raw: str, line: int) -> Section:
    sec = Section(level=len(level_marks) - 1, raw=raw, line=line)
    text = raw
    if OUTLINE_ONLY in text:
        sec.outline_only = True
        text = text.replace(OUTLINE_ONLY, "").strip()
    # trailing tags
    while True:
        m = re.search(r"\s*\[([^\]\n]+)\]\s*$", text)
        if not m or re.match(r"(TBD|UNVERIFIED)\b", m.group(1)):   # placeholders are content, not tags
            break
        sec.tags.insert(0, m.group(1))
        text = text[:m.start()]
    m = NUM_RE.match(text)
    if m:
        sec.number = m.group(1)
        text = m.group(3)
        sec._top_dot = bool(m.group(2))
    m = re.match(r"\[([^\]\n]+)\]\s*(.*)$", text)
    if m and not re.match(r"(TBD|UNVERIFIED)\b", m.group(1)):
        sec.slide_type = m.group(1)
        text = m.group(2)
    sec.title = text.strip()
    low = sec.title.lower()
    if sec.level == 0:
        sec.kind = "title"
    elif sec.number is None:
        if low.startswith("front matter"):
            sec.kind = "front"
        elif low.startswith("central message"):
            sec.kind = "central"
        elif low.startswith("time plan"):
            sec.kind = "timeplan"
        elif low.startswith("changes by version"):
            sec.kind = "changes"
        elif low.startswith("source reconciliation"):
            sec.kind = "reconciliation"
        elif low.startswith("coverage gaps"):
            sec.kind = "gaps"
        else:
            sec.kind = "other"
    return sec


def _gather_list(lines, i):
    """Collect list lines starting at i. Returns (top-level items, next index)."""
    items, stack = [], []
    while i < len(lines):
        ln, text = lines[i]
        m = LIST_RE.match(text)
        if not m:
            if text.strip() and text.startswith("  ") and stack:   # continuation line
                stack[-1].text += " " + text.strip()
                i += 1
                continue
            break
        indent = len(m.group(1).replace("\t", "    "))
        item = Item(text=m.group(3).strip(), line=ln, indent=indent, ordered=m.group(2)[0].isdigit())
        while stack and stack[-1].indent >= indent:
            stack.pop()
        (stack[-1].children if stack else items).append(item)
        stack.append(item)
        i += 1
    return items, i


def parse_body(sec: Section, reg: Registry) -> None:
    """Turn a section's body lines into blocks."""
    lines, blocks, i = sec.body, [], 0
    known = set(reg.directives) | ALWAYS_KEYS | reg.layout_fields | FRONT_KEYS
    if sec.slide_type in reg.slide_types:
        st = reg.slide_types[sec.slide_type]
        known |= set(st["required"]) | set(st["optional"])
    for d in reg.directives.values():
        known |= set(d["companions"])
    pending_layout = None
    while i < len(lines):
        ln, text = lines[i]
        if not text.strip() or text.strip() == "---":
            i += 1
            continue
        fm = FENCE_RE.match(text)
        if fm:
            fence, lang, body = fm.group(1), fm.group(2), []
            j = i + 1
            while j < len(lines) and not lines[j][1].startswith(fence[:3]):
                body.append(lines[j][1])
                j += 1
            blocks.append(Block("fence", ln, key=lang, lines=body))
            i = j + 1
            continue
        cm = CALLOUT_RE.match(text)
        if cm or text.startswith(">"):
            body, j = [], i + 1
            while j < len(lines) and lines[j][1].startswith(">"):
                body.append(lines[j][1].lstrip(">").strip())
                j += 1
            if cm:
                blocks.append(Block("callout", ln, key=cm.group(1).upper(), text=cm.group(2).strip(), lines=body))
            else:
                blocks.append(Block("quote", ln, text=" ".join([text.lstrip(">").strip()] + body)))
            i = j
            continue
        if text.lstrip().startswith("|"):
            body, j = [], i
            while j < len(lines) and lines[j][1].lstrip().startswith("|"):
                body.append(lines[j][1])
                j += 1
            blocks.append(Block("table", ln, lines=body))
            i = j
            continue
        km = KEY_RE.match(text)
        if km and km.group(1) in known:
            key, val = km.group(1), (km.group(2) or "").strip()
            if key == "Layout":
                parts = [p.strip() for p in val.split(";") if p.strip()]
                pending_layout = Block("layout", ln, key=parts[0] if parts else "", options=parts[1:])
                blocks.append(pending_layout)
            elif key in reg.layout_fields and pending_layout is not None and not pending_layout.items:
                pending_layout.fields[key] = val
            else:
                blocks.append(Block("key", ln, key=key, text=val))
            i += 1
            continue
        if LIST_RE.match(text):
            items, i = _gather_list(lines, i)
            if pending_layout is not None and not pending_layout.items:
                pending_layout.items = items
                pending_layout = None
                continue
            pending_layout = None
            # a key with an empty value takes the list below it (Steps:, Options:, Points:)
            if blocks and blocks[-1].kind == "key" and not blocks[-1].text and not blocks[-1].items:
                blocks[-1].items = items
                continue
            # bullets that are key lines (e.g. "- Speaker notes: ...") become key blocks
            plain = []
            for it in items:
                km2 = KEY_RE.match(it.text)
                if km2 and km2.group(1) in known and km2.group(1) != "Layout":
                    if plain:
                        blocks.append(Block("list", plain[0].line, items=plain))
                        plain = []
                    blocks.append(Block("key", it.line, key=km2.group(1), text=(km2.group(2) or "").strip(), items=it.children))
                else:
                    plain.append(it)
            if plain:
                blocks.append(Block("list", plain[0].line, items=plain))
            continue
        pending_layout = None
        blocks.append(Block("para", ln, text=text.strip()))
        i += 1
    sec.blocks = blocks


def parse_outline(text: str, reg: Registry) -> Outline:
    lines = text.split("\n")
    sections, current, in_fence, fence = [], None, False, ""
    status = {}
    sm = STATUS_RE.search(text)
    if sm:
        for part in sm.group(1).split("|"):
            part = part.strip()
            if ":" in part:
                k, v = part.split(":", 1)
                status[k.strip()] = v.strip()
            elif part:
                bits = part.split(None, 1)
                if len(bits) == 2 and bits[0] == "last" and bits[1].startswith("written"):
                    status["last written"] = bits[1][len("written"):].strip()
                elif len(bits) == 2:
                    status[bits[0]] = bits[1]
    for n, raw in enumerate(lines, start=1):
        fm = FENCE_RE.match(raw)
        if fm and (not in_fence or raw.startswith(fence[:3])):
            if not in_fence:
                in_fence, fence = True, fm.group(1)
            else:
                in_fence = False
        hm = None if in_fence or fm else HEADING_RE.match(raw)
        if hm:
            current = _parse_heading(hm.group(1), hm.group(2), n)
            sections.append(current)
            continue
        if current is not None:
            current.body.append((n, raw))
    # parents: the nearest preceding numbered section one level up
    last_by_level = {}
    for s in sections:
        if s.kind == "topic" and s.number:
            s.parent = last_by_level.get(s.level - 1)
            last_by_level[s.level] = s
            for lvl in list(last_by_level):
                if lvl > s.level:
                    del last_by_level[lvl]
        elif s.level == 1:
            last_by_level = {}
    for s in sections:
        parse_body(s, reg)
    timeplan = []
    for s in sections:
        if s.kind == "timeplan":
            for b in s.blocks:
                if b.kind == "table":
                    for row_i, row in enumerate(b.lines[2:], start=2):
                        cells = _cells(row)
                        num = cells[0].strip("*").strip() if cells else ""
                        timeplan.append({"number": num if re.fullmatch(r"\d+", num) else None,
                                         "cells": cells, "line": b.line + row_i})
                    break
    return Outline(sections=sections, status=status, timeplan=timeplan, lines=lines)
