#!/usr/bin/env python3
"""
10_cisa_issue.py — generate docs/CISA_ISSUE.md, the upstream issue text.

The issue body used to live inside docs/PUBLISH_GUIDE.md as a block quote with
its figures typed by hand and its citation written as the literal placeholder
`[Zenodo DOI]`. Two problems with that. The figures could drift from the data
the same way the release notes did (defect A4). And the placeholder was
invisible to the publish gate: its bracketed-placeholder pattern matches
`[DOI]` but not `[Zenodo DOI]`, so the text could have been filed with the
stand-in still in it.

So the issue text is generated: every number from report/stats.json, the DOI
from the canonical release state. In draft mode no DOI exists and none is
invented — the citation line says so plainly, and the file carries a header
making clear it is not ready to file.

Ordering is an author ruling (V5) and is restated in the generated file:
the Zenodo deposit comes first, because filing this issue is the single most
likely thing to prompt CISA to amend the schema, and the observation should be
citable before the thing it observes can change.

Usage:
    python code/10_cisa_issue.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import release_state

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    try:
        state = release_state.load()
    except release_state.ReleaseStateError as exc:
        print(f"[cisa-issue] {exc}", file=sys.stderr)
        return 2

    S = json.loads((ROOT / "report" / "stats.json").read_text())
    META = json.loads((ROOT / "metadata.json").read_text())
    sch, cat = S["schema"], S["catalog"]
    first_seen = sch["forensic_triage_first_seen"]

    if state["final"]:
        header = ""
        citation = (f"Full timeline and method: {state['doi_url']} "
                    f"(DOI {state['doi']})")
        footer = (f"Filed for {META['title']}, {state['version_string']}, "
                  f"released {state['release_date']}.\n")
    else:
        header = (
            "<!-- NOT READY TO FILE. This build is not final: no DOI has been\n"
            "     reserved, so the citation line below has nothing to point\n"
            "     at. Regenerated automatically at release. -->\n\n"
            "> **Not ready to file.** No DOI exists yet. File this only after\n"
            "> the Zenodo deposit is published (author ruling V5), by which\n"
            "> point this file will have been regenerated with the DOI in it.\n"
            "\n")
        citation = ("Full timeline and method: "
                    + release_state.citation_reference(state))
        footer = (f"Prepared for {META['title']}, {state['version_string']}. "
                  "Not yet filed.\n")

    body = f"""<!-- GENERATED FILE — do not edit by hand.
     Written by code/10_cisa_issue.py from report/stats.json, metadata.json and
     the canonical release state. Re-run the pipeline to refresh. -->

# Upstream issue text — cisagov/kev-data

{header}File at <https://github.com/cisagov/kev-data/issues/new> **after** the Zenodo
deposit is published, never before (author ruling V5).

---

**Title:** Published JSON schema does not describe the `forensicTriage` field

The `forensicTriage` field has been present on records in
`known_exploited_vulnerabilities.json` since {first_seen} and, as of the
{S['data_cutoff']} data cutoff, appears on
{sch['forensic_triage_coverage_pct']}% of the {cat['last_count']:,} entries in
the catalog.

It is not among the properties of `$defs.vulnerability` in
`known_exploited_vulnerabilities_schema.json`, which has
{sch['schema_commits']} commit in its entire history, dated
{sch['schema_last_modified']} — {sch['schema_stale_days']} days before that
cutoff.

Because `additionalProperties` is not set, the catalog still validates against
the published schema with {sch['validation_errors']} errors, so this does not
surface as a validation failure. The practical effect falls on consumers who
generate types, columns or documentation from the schema: they silently omit
the field.

{citation}

---

{footer}"""
    out = ROOT / "docs" / "CISA_ISSUE.md"
    out.write_text(body, encoding="utf-8")
    print(f"[cisa-issue] docs/CISA_ISSUE.md generated "
          f"({release_state.describe(state)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
