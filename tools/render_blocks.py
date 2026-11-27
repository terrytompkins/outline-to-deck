"""render_blocks: turn parsed outline blocks into deck markup (DECK-BUILD-SPEC.md section 4).

Covers the structured tags whose markup is fully determined by the outline: layouts, charts,
callouts, inline Markdown and markers. Claude still writes slide content and visuals.

    from outline_parser import load_registry, parse_outline
    from render_blocks import layout_html, inline
"""
from __future__ import annotations

import html
import re

from outline_parser import split_label

ORDERED_SHAPES = {"ordered", "dated", "tree", "radial"}


def inline(text: str) -> str:
    """Inline Markdown and markers to HTML. Origin and audience tags are stripped."""
    codes = []

    def keep_code(m):
        codes.append(html.escape(m.group(1)))
        return f"\x00{len(codes) - 1}\x00"
    t = re.sub(r"`([^`]+)`", keep_code, text)
    links = []

    def keep_link(m):
        links.append((m.group(1), m.group(2)))
        return f"\x01{len(links) - 1}\x01"
    t = re.sub(r"\[([^\]\n]+)\]\((https?://[^)\s]+)\)", keep_link, t)
    t = re.sub(r"\(\s*\x01(\d+)\x01\s*\)", lambda m: "", t)          # source links in parentheses go to the footer
    t = re.sub(r"\s*\[(Seed|Research|Core|Brief|Self-guided)\]", "", t)
    t = html.escape(t, quote=False)
    t = re.sub(r"\[TBD:\s*([^\]]+)\]", lambda m: f'<span class="tbd">TBD: {m.group(1).strip()}</span>', t)
    t = re.sub(r"\[UNVERIFIED(?::[^\]]*)?\]", '<span class="unverified">Unverified</span>', t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", t)
    t = re.sub(r"\x01(\d+)\x01", lambda m: f'<a href="{links[int(m.group(1))][1]}">{html.escape(links[int(m.group(1))][0])}</a>', t)
    t = re.sub(r"\x00(\d+)\x00", lambda m: f"<code>{codes[int(m.group(1))]}</code>", t)
    t = t.replace("\\:", ":")
    return t.strip()


def source_links(text: str) -> list[tuple[str, str]]:
    return re.findall(r"\(\s*\[([^\]\n]+)\]\((https?://[^)\s]+)\)\s*\)", text)


def _item(it, shape, depth=0) -> str:
    label, detail, key = split_label(it.text)
    cls = "layout__item" + (" is-key" if key else "")
    if depth > 0 and shape not in ("tree", "radial"):
        return f"<li>{inline(it.text)}</li>"
    parts = [f'<span class="layout__label">{inline(label)}</span>']
    if detail:
        parts.append(f'<span class="layout__detail">{inline(detail)}</span>')
    if it.children:
        tag = "ul"
        kids = "".join(_item(c, shape, depth + 1) for c in it.children)
        parts.append(f"<{tag}>{kids}</{tag}>")
    if depth > 0:      # nested tree and radial nodes carry the item class too
        return f'<li class="{cls}">' + "".join(parts) + "</li>"
    return f'<li class="{cls}">' + "".join(parts) + "</li>"


def layout_count(block, shape) -> int:
    top = block.items
    if shape == "tree":
        def n(it):
            return 1 + sum(n(c) for c in it.children)
        return sum(n(it) for it in top)
    if shape == "radial":
        return len(top[0].children) if top else 0
    return len(top)


def layout_html(block, reg) -> str:
    spec = reg.layouts[block.key]
    shape = spec["shape"]
    variants = [o for o in block.options if o in spec["variants"]]
    variant = variants[0] if variants else (spec["variants"][0] if spec["variants"] else "")
    attrs = [f'class="layout layout--{block.key}"', f'data-layout="{block.key}"']
    if variant:
        attrs.append(f'data-variant="{variant}"')
    attrs.append(f'data-count="{layout_count(block, shape)}"')
    if "build" in block.options:
        attrs.append("data-build")
    if "numbered" in block.options:
        attrs.append("data-numbered")
    for k, v in block.fields.items():
        attrs.append(f'data-{k.lower().replace(" ", "-")}="{html.escape(v)}"')
    tag = "ol" if shape in ORDERED_SHAPES else "ul"
    body = "".join(_item(it, shape) for it in block.items)
    return f'<div {" ".join(attrs)}>\n  <{tag} class="layout__items">{body}</{tag}>\n</div>'
