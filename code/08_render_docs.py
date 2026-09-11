#!/usr/bin/env python3
"""
08_render_docs.py — render README.md and docs/LIMITATIONS.md from templates.

Defect A3: the change-event count was stated by hand in several documents and
they disagreed — docs/LIMITATIONS.md said both "six change events" and "five
change events" in the same file, because the catalog changes in two different
ways and the prose conflated them.

The fix is not to correct the numbers but to stop typing them. README.md and
docs/LIMITATIONS.md are now rendered from `.template` files in which every
figure is a placeholder resolved against report/stats.json and metadata.json,
the same rule the report already followed. Editing the rendered file is
pointless: the next run overwrites it, and code/03_qa.py checks that rendering
is a no-op.

Placeholder syntax:  {{ stats.events.total_schema_evolution_events }}
                     {{ meta.title }}
Numbers are thousands-separated automatically; add `:raw` to suppress that.

Usage:
    python code/08_render_docs.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import release_state

ROOT = Path(__file__).resolve().parents[1]
TARGETS = [
    (ROOT / "templates" / "README.md.template", ROOT / "README.md"),
    (ROOT / "templates" / "LIMITATIONS.md.template", ROOT / "docs" / "LIMITATIONS.md"),
]
PLACEHOLDER = re.compile(r"\{\{\s*([a-zA-Z0-9_.]+)\s*(:raw)?\s*\}\}")


def resolve(dotted: str, ctx: dict):
    cur = ctx
    for part in dotted.split("."):
        if isinstance(cur, list):
            cur = cur[int(part)]
        else:
            if part not in cur:
                raise KeyError(f"unknown placeholder path: {dotted}")
            cur = cur[part]
    return cur


def render(text: str, ctx: dict) -> str:
    def sub(m):
        val = resolve(m.group(1), ctx)
        if m.group(2) == ":raw":
            return str(val)
        if isinstance(val, int):
            return f"{val:,}"
        if isinstance(val, float):
            return f"{val:g}"
        return str(val)
    return PLACEHOLDER.sub(sub, text)


def main() -> int:
    stats = json.loads((ROOT / "report" / "stats.json").read_text())
    try:
        state = release_state.load()
    except release_state.ReleaseStateError as exc:
        print(f"[render] {exc}", file=sys.stderr)
        return 2
    ctx = {
        "stats": stats,
        "meta": json.loads((ROOT / "metadata.json").read_text()),
        "authors": json.loads((ROOT / "AUTHORS.json").read_text())["authors"],
        # The README STATUS banner is generated, in both modes. It used to be
        # literal text in the template carrying a hand-typed version string,
        # which is the one place the project's own "never type a figure" rule
        # was not applied.
        "release": dict(state,
                        banner=release_state.readme_banner(state, stats)
                        .rstrip("\n")),
    }
    print(f"[render] {release_state.describe(state)}")
    for src, dst in TARGETS:
        if not src.exists():
            print(f"[render] SKIP (no template): {src.relative_to(ROOT)}")
            continue
        out = render(src.read_text(), ctx)
        header = ("<!-- GENERATED from templates/" + src.name +
                  " by code/08_render_docs.py. Edit the template, not this "
                  "file. -->\n")
        dst.write_text(header + out, encoding="utf-8")
        print(f"[render] {dst.relative_to(ROOT)} <- {src.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
