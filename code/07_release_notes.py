#!/usr/bin/env python3
"""
07_release_notes.py — generate docs/RELEASE_NOTES.md from the canonical sources.

Defect A4: the publish guide carried a hand-written release-notes block whose
figures were superseded three rulings ago — "229 overlapping days", "100%
agreement", "derived data CC0-1.0" — and that block is written to be pasted
straight into a GitHub release. Publishing from it would have put stale numbers
on the permanent public record.

Release notes are therefore generated, never typed. Every figure comes from
report/stats.json, the title and licences from metadata.json, the author from
AUTHORS.json. docs/PUBLISH_GUIDE.md points at the generated file rather than
embedding a copy, and code/03_qa.py fails the build if this file is missing or
disagrees with the statistics.

Usage:
    python code/07_release_notes.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    S = json.loads((ROOT / "report" / "stats.json").read_text())
    META = json.loads((ROOT / "metadata.json").read_text())
    author = json.loads((ROOT / "AUTHORS.json").read_text())["authors"][0]

    cov, cat, sch, xv, ev = (S["coverage"], S["catalog"], S["schema"],
                             S["crossvalidation"], S["events"])
    tl = [r for r in _timeline() if r["track"] == "csv_daily"
          and r["event"] != "baseline"]

    bullets = []
    seen_removed = set()
    for r in sorted(tl, key=lambda r: r["date"]):
        if r["event"] == "naming_convention_change":
            bullets.append(f"- {r['date']} — naming/canonicalization: columns "
                           f"renamed from human-readable labels to camelCase")
        elif r["event"] == "field_added":
            # A field re-appearing after an earlier removal is a restoration,
            # not a first appearance. Derived from the timeline, not asserted.
            word = "restored" if r["field"] in seen_removed else "added"
            bullets.append(f"- {r['date']} — field-presence transition: "
                           f"`{r['field']}` {word}")
        elif r["event"] == "field_removed":
            seen_removed.add(r["field"])
            bullets.append(f"- {r['date']} — field-presence transition: "
                           f"`{r['field']}` removed")

    lic = META["licenses"]
    notes = f"""<!-- GENERATED FILE — do not edit by hand.
     Written by code/07_release_notes.py from report/stats.json, metadata.json
     and AUTHORS.json. Re-run the pipeline to refresh. code/03_qa.py fails if
     this file disagrees with the statistics. -->

# Release notes — v{META['version']}

Paste the block below into the GitHub release body.

---

First release of **{META['title']}**.

A dated, three-source reconstruction of schema evolution in the CISA Known
Exploited Vulnerabilities catalog, which is published without a revision
history. Built from {cov['usable_snapshots']:,} daily snapshots spanning
{cov['first_date']} to {cov['last_date']} ({cov['coverage_pct']}% calendar
coverage) and cross-validated against two additional sources — CISA's official
Git mirror and a second independent archive — across
{xv['multi_source_days']:,} multi-source days
({xv['three_source_days']} of them carrying all three sources) at
{xv['agreement_pct']}% agreement, with {xv['disagreements']} disagreement,
explained in the report as a fetch-timing artefact.

**{ev['total_schema_evolution_events']} schema-evolution events**
({ev['field_presence_transitions']} field-presence transitions and
{ev['naming_or_canonicalization_events']} naming/canonicalization event):

{chr(10).join(bullets)}

The two kinds are counted separately because they are different: a
field-presence transition changes which fields exist, while a
naming/canonicalization event renames every column without changing the set of
logical fields. Conflating them is what produced an inconsistent count in an
earlier draft.

**Supporting finding, time-bound.** As of the {S['data_cutoff']} data cutoff,
with sources accessed {S['access_date']}, `forensicTriage` was present on
{sch['forensic_triage_coverage_pct']}% of the {cat['last_count']:,} records in
the live catalog but was not described in CISA's published JSON schema, which
had {sch['schema_commits']} commit in its entire history, dated
{sch['schema_last_modified']} ({sch['schema_stale_days']} days before the data
cutoff). Because that schema does not restrict additional properties, the
catalog validates against it with {sch['validation_errors']} errors, so the
omission does not surface as a validation failure. This is a
schema-documentation gap reported as observed on the stated dates; if CISA
subsequently describes the field, the dated observation remains accurate as a
record of the interval.

**Reproducibility.** All three sources are pinned to specific commits. Python
dependencies are fully pinned in `requirements.lock`; the validated environment
is documented in `docs/ENVIRONMENT.md`. Figures are byte-reproducible under the
pinned dependencies.

**Licences.** Code {lic['code']}; derived data {lic['derived_data']}; report and
figures {lic['report']}. The upstream CISA catalog remains CC0 public-domain
material and is unrestricted; see `LICENSE-DATA` for the full rights statement.

Author: {author['name']}, {author['affiliation']}, ORCID {author['orcid']}.
"""
    out = ROOT / "docs" / "RELEASE_NOTES.md"
    out.write_text(notes, encoding="utf-8")
    print(f"[release-notes] docs/RELEASE_NOTES.md generated "
          f"({ev['total_schema_evolution_events']} events, "
          f"{xv['agreement_pct']}% agreement, {lic['derived_data']} data)")
    return 0


def _timeline():
    import csv
    with open(ROOT / "data" / "processed" / "schema_timeline.csv",
              encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


if __name__ == "__main__":
    raise SystemExit(main())
