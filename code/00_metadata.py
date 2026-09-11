#!/usr/bin/env python3
"""
00_metadata.py — render CITATION.cff from the canonical sources.

CITATION.cff is generated, never hand-edited. It draws its title and version
from metadata.json, its author block from AUTHORS.json, and its abstract figures
from report/stats.json. That is what stops the title, the author spelling and
the headline numbers drifting apart across the report, the README, the citation
file and the PDF.

Run order note: this reads report/stats.json when it exists, so the abstract
carries current figures. On a cold build (no stats yet) it emits the citation
file without the numeric abstract and should be re-run after 04_figures.py.
code/run_all.sh does that automatically.

Usage:
    python code/00_metadata.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import release_state

ROOT = Path(__file__).resolve().parents[1]


def yaml_block(text: str, indent: str = "  ") -> str:
    """Fold a paragraph into a CFF block scalar."""
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > 74:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return "\n".join(indent + ln for ln in lines)


def main() -> int:
    try:
        state = release_state.load()
    except release_state.ReleaseStateError as exc:
        print(f"[metadata] {exc}", file=sys.stderr)
        return 2

    meta = json.loads((ROOT / "metadata.json").read_text())
    author = json.loads((ROOT / "AUTHORS.json").read_text())["authors"][0]

    stats_path = ROOT / "report" / "stats.json"
    S = json.loads(stats_path.read_text()) if stats_path.exists() else None

    if S:
        cov, xv, ev, sch, cat = (S["coverage"], S["crossvalidation"],
                                 S["events"], S["schema"], S["catalog"])
        abstract = (
            f"A dated, three-source reconstruction of schema evolution in the "
            f"CISA Known Exploited Vulnerabilities (KEV) catalog, which is "
            f"published without a revision history. Built from "
            f"{cov['usable_snapshots']:,} daily snapshots spanning "
            f"{cov['first_date']} to {cov['last_date']} and cross-validated "
            f"against two additional sources — CISA's official Git mirror "
            f"and a second independent archive — across "
            f"{xv['multi_source_days']:,} multi-source days at "
            f"{xv['agreement_pct']}% agreement, it identifies and dates "
            f"{ev['total_schema_evolution_events']} schema-evolution events: "
            f"{ev['field_presence_transitions']} field-presence transitions and "
            f"{ev['naming_or_canonicalization_events']} naming or "
            f"canonicalization event. A supporting, time-bound observation is "
            f"also reported: as of the {S['data_cutoff']} data cutoff, with "
            f"sources accessed {S['access_date']}, the forensicTriage field was "
            f"present on {sch['forensic_triage_coverage_pct']}% of the "
            f"{cat['last_count']:,} records in the live catalog but was not "
            f"described in CISA's published JSON schema."
        )
    else:
        abstract = ("A dated, three-source reconstruction of schema evolution "
                    "in the CISA Known Exploited Vulnerabilities catalog. "
                    "Regenerate after code/04_figures.py for current figures.")

    kw = "\n".join(f'  - "{k}"' for k in meta["keywords"])

    # date-released and the DOI are emitted only in final mode, from the
    # canonical release state. The former `date-released: "[RELEASE_DATE]"`
    # was invisible to the publish gate — its bracketed-placeholder pattern
    # does not match [RELEASE_DATE] — so a release could have gone out with a
    # literal placeholder as its citation date. Emitting nothing in draft mode
    # removes the class of defect rather than adding another pattern to catch.
    if state["final"]:
        release_block = (f'date-released: "{state["release_date"]}"\n'
                         f'doi: "{state["doi"]}"\n')
    else:
        release_block = (
            "# date-released and doi are emitted here in final mode, from the\n"
            "# release block in metadata.json. This build is not final: no\n"
            "# release date and no DOI exist yet, and neither is invented.\n")
    cff = f"""# GENERATED FILE — do not edit by hand.
# Written by code/00_metadata.py from metadata.json, AUTHORS.json and
# report/stats.json. Edit those, then re-run the pipeline.
cff-version: 1.2.0
message: "If you use this work, please cite it as below."
type: dataset
title: "{meta['title']}"
abstract: >-
{yaml_block(abstract)}
version: "{state['version']}"
{release_block}authors:
  - family-names: "{author['family']}"
    given-names: "{author['given']}"
    orcid: "https://orcid.org/{author['orcid']}"
    email: "{author['email']}"
    affiliation: "{author['affiliation']}"
license: CC-BY-4.0
license-url: "https://creativecommons.org/licenses/by/4.0/"
repository-code: "{meta['repository']}"
keywords:
{kw}
references:
  - type: data
    title: "Known Exploited Vulnerabilities Catalog"
    authors:
      - name: "Cybersecurity and Infrastructure Security Agency"
    url: "https://github.com/cisagov/kev-data"
    license: CC0-1.0
"""
    (ROOT / "CITATION.cff").write_text(cff, encoding="utf-8")
    print(f"[metadata] CITATION.cff generated "
          f"({'with' if S else 'without'} stats figures; "
          f"{release_state.describe(state)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
