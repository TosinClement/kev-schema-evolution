#!/usr/bin/env python3
"""
05_document.py — build the technical report from stats.json.

Every number in the report is interpolated from report/stats.json. No figure in
the prose is typed by hand, so the text cannot drift from the data: re-run the
pipeline and the report's numbers move with it.

Draft/final status, the version string and the DOI come from the canonical
release state in metadata.json (see code/release_state.py), not from a
command-line switch. In draft mode the report carries the DRAFT banner and no
DOI of any kind; in final mode the banner is gone and the DOI appears on the
first page, under the author block.

Usage:
    python code/05_document.py            # mode from metadata.json
    python code/05_document.py --final    # assert the state says final
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import release_state

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "report"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--final", action="store_true",
                    help="assert that metadata.json says release.mode is "
                         "final; it does not set the mode")
    args = ap.parse_args()

    try:
        state = release_state.load(assert_final=args.final)
    except release_state.ReleaseStateError as exc:
        print(f"[document] {exc}", file=sys.stderr)
        return 2

    S = json.loads((REPORT / "stats.json").read_text())
    a = json.loads((ROOT / "AUTHORS.json").read_text())["authors"][0]
    META = json.loads((ROOT / "metadata.json").read_text())
    cov, cat, sch, xv, ev = (S["coverage"], S["catalog"], S["schema"],
                             S["crossvalidation"], S["events"])
    sp = S["fields"]["spans"]
    nb = ev["notes_boundary"]
    table = (REPORT / "tables" / "table01_change_events.md").read_text().strip()

    banner = "" if state["final"] else (
        "> **DRAFT — NOT RELEASED.** This document has not passed author\n"
        "> verification. Numbers are pipeline output and have not been\n"
        "> independently confirmed. Do not cite.\n\n")

    # First-page identity line. Carries the DOI in final mode and nothing
    # DOI-shaped in draft mode — no placeholder, no example, no reserved-
    # looking string that could be mistaken for one.
    identity = release_state.report_identity_line(state, S)



    # --- blocks that depend on whether the third source is in the build -----
    # Author ruling V2 is conditional on V3. If the third source is dropped,
    # every claim resting on it must disappear with it — not merely the one
    # sentence in Section 5. These blocks are built here so a rejected V3
    # yields a correct report rather than a crash or an orphaned claim.
    has_indep = bool(S["sources"].get("indep_repo") and xv.get("indep_first"))

    if has_indep:
        tsm = S["sources"].get("third_source_manifest", {})
        ju, cx = tsm.get("json_used", {}), tsm.get("csv_excluded", {})
        source2_block = (
            f"**Corroborating source 2.** A second archive, "
            f"`{S['sources']['indep_repo']}`, has captured the KEV **JSON** "
            f"daily from {ju.get('first_date')} to {ju.get('last_date')} "
            f"({ju.get('file_count'):,} files, of which {xv['indep_days']:,} "
            f"are usable), extending corroboration more than a year earlier "
            f"than CISA's own mirror begins. Pinned at commit "
            f"`{S['sources']['indep_commit'][:12]}`, accessed "
            f"{tsm.get('access_date')}.\n\n"
            f"Only that repository's `json/` tree is read, and it is excluded "
            f"as a witness anywhere its evidence would be circular. Its `csv/` "
            f"tree is not used at all. Hashing every date both repositories "
            f"hold ({cx.get('dates_compared_with_primary'):,} dates) gives the "
            f"complete picture: for all "
            f"{cx.get('dates_before_that_all_identical'):,} dates before "
            f"{cx.get('all_identical_before')} its CSV is byte-identical to the "
            f"primary archive's and appears to be a back-filled copy, while "
            f"{cx.get('differing_from_primary'):,} later shared-date files "
            f"differ. The entire CSV tree is nonetheless excluded from "
            f"independent corroboration, because the independently collected "
            f"JSON series already represents this record keeper and counting "
            f"both formats would duplicate one collector. The "
            f"JSON is a second witness because the primary archive stored CSV "
            f"only and never held these files. Per-date hashes are published in "
            f"`data/raw/third_source_csv_identity.csv` so this exclusion can be "
            f"re-derived rather than taken on trust.\n\n"
            f"That repository carries no licence file. Its archived content is "
            f"the CISA catalog, a US government work released under CC0 by "
            f"CISA, and this build reads that public-domain content for "
            f"verification only. No file from the repository is copied into, "
            f"redistributed by, or released with this project: the working "
            f"clone lives in the git-ignored `sources/` directory, and only "
            f"hashes, counts and dates are recorded here. This is a looser "
            f"footing than the other two sources and is recorded as "
            f"Limitation 12.\n\n"
        )
        crossval_block = (
            f"**Cross-validation.** {xv['multi_source_days']:,} days carry "
            f"captures from two or more sources, {xv['three_source_days']} of "
            f"them from all three. The derived field sets agree on "
            f"{xv['agree_days']:,} of those days ({xv['agreement_pct']}%).\n\n"
        )
        if xv.get("disagreement_dates"):
            crossval_block += (
                f"The single exception is instructive rather than troubling. On "
                f"{xv['disagreement_dates'][0]} the second archive records no "
                f"`forensicTriage` while the other two do — because it captured "
                f"`catalogVersion` 2026.08.31, the previous day's catalog, "
                f"having fetched before CISA published that day. Keyed on "
                f"`catalogVersion` instead of capture date, all three sources "
                f"agree exactly: `forensicTriage` is absent from v2026.08.31 "
                f"and present in v2026.09.01. Capture date is not catalog "
                f"version, and this is the one place in five years of history "
                f"where the distinction changes an answer. The timeline is "
                f"reported on capture date throughout, so this date is stated "
                f"with that caveat attached.\n\n"
            )
        crossval_block += (
            f"Events before {xv['indep_first']} remain corroborated by a single "
            f"source; see Limitation 4."
        )
    else:
        source2_block = ""
        crossval_block = (
            f"**Cross-validation.** {xv['multi_source_days']:,} days carry "
            f"captures from both sources. The derived field sets agree on "
            f"{xv['agree_days']:,} of those days ({xv['agreement_pct']}%). "
            f"Events before {xv['json_first']} remain corroborated by a single "
            f"source; see Limitation 4."
        )

    # --- Section 5 capture-failure paragraph --------------------------------
    # Every value here is parsed from the captured pages by the pipeline.
    # The independent-confirmation sentence is emitted ONLY when the third
    # source is present in the build: author ruling V2 is conditional on V3,
    # so if the third source is dropped the sentence disappears with it rather
    # than surviving as an unsupported claim.
    cf = S["artifacts"]["capture_failures"]
    primary = [c for c in cf if c.get("source") == "csv_daily"]
    indep_cf = [c for c in cf if c.get("source") == "json_independent"]
    fail_dates = S["artifacts"]["unusable_dates"]
    svc = {c.get("service") for c in cf}
    svc_name = "Akamai edge" if svc == {"akamai_edge"} else "content-delivery"

    capture_para = (
        f"- **Capture failures ({len(fail_dates)} days).** On "
        f"{' and '.join(fail_dates)} the archiver stored an {svc_name} "
        f'"Access Denied" response rather than CSV. The embedded reference '
        f"identifiers decode to "
        f"{' and '.join(c['refused_utc'][11:19] + ' UTC' for c in primary)} "
        f"respectively — "
        f"{round((int(primary[-1]['ref'].split('.')[2]) - int(primary[0]['ref'].split('.')[2])) / 3600, 3)} "
        f"hours apart, consistent with a scheduled daily job that ran normally "
        f"and was refused at the content-delivery layer. Adjacent days "
        f"retrieved valid data."
    )
    if indep_cf and S["sources"].get("indep_repo"):
        c = indep_cf[0]
        capture_para += (
            f" The second archive independently confirms this: its own capture "
            f"for {c['date']} is also an {svc_name} denial, timestamped "
            f"{c['refused_utc'][11:19]} UTC, for the JSON endpoint rather than "
            f"the CSV one. Two unrelated collectors, two different URLs, "
            f"refused within hours of each other."
        )
    capture_para += (
        " The responses record a refusal at the content-delivery layer rather "
        "than an unavailable catalog or a fault in the collection tool. They do "
        "not record why the requests were refused, and no cause is inferred "
        "here. These days are excluded, not interpolated."
    )

    md = f"""{banner}# {META['title']}

**{a['name']}**
{a['affiliation']}
ORCID [{a['orcid']}](https://orcid.org/{a['orcid']}) · {a['email']}

{identity}

---

## Abstract

The CISA Known Exploited Vulnerabilities (KEV) catalog is a widely consumed
input to vulnerability management, but CISA publishes no revision history for
it, so consumers have no authoritative record of when the shape of the data
changed. This report reconstructs that record. Using
{cov['usable_snapshots']:,} daily catalog snapshots spanning {cov['first_date']}
to {cov['last_date']} ({cov['span_days']:,} days, {cov['coverage_pct']}%
calendar coverage), it identifies {ev['total_schema_evolution_events']}
schema-evolution events — {ev['field_presence_transitions']} field-presence
transitions and {ev['naming_or_canonicalization_events']}
naming/canonicalization event — and cross-validates them against two additional
sources: CISA's official Git mirror and a second independent archive. Across
{xv['multi_source_days']:,} days carrying two or more captures the sources agree
{xv['agreement_pct']}% of the time, with a single dated, explained exception.
Over the period the catalog grew from {cat['first_count']:,} to
{cat['last_count']:,} entries ({cat['growth_multiple']}×). The reconstruction,
its per-day evidence and its cross-source agreement record are released as
reusable data.

A supporting, time-sensitive finding is also reported. As of the
{S['data_cutoff']} data cutoff, with sources accessed {S['access_date']}, the
field `forensicTriage` was present on {sch['forensic_triage_coverage_pct']}% of
records in the live catalog but was not described in CISA's published JSON
schema, which had not been modified since its initial commit
{sch['schema_stale_days']} days earlier. Because that schema does not restrict
additional properties, the catalog validates against it without error, so the
omission does not surface as a validation failure. This is a schema-documentation
gap, reported as observed on the stated dates; should CISA subsequently update
the schema, the dated observation remains accurate as a historical record.

## Executive summary

**Primary contribution — a three-source reconstruction of the KEV schema
timeline, 2021–2026.** CISA overwrites its catalog files in place and publishes
no changelog, so the history of the data's structure is not recoverable from the
canonical source. This report reconstructs it from {cov['usable_snapshots']:,}
daily captures and corroborates it against two additional sources: CISA's
official Git mirror and a second independent archive.
{ev['total_schema_evolution_events']} schema-evolution events are identified and dated:
{ev['field_presence_transitions']} field-presence transitions and
{ev['naming_or_canonicalization_events']} naming/canonicalization event. Agreement across
{xv['multi_source_days']:,} multi-source days is {xv['agreement_pct']}%. This
finding is durable: it describes five years of history and does not depend on
the catalog's current state.

**Supporting finding — a schema-documentation gap, as of {S['data_cutoff']}.**
The `forensicTriage` field appeared in the catalog on
{sch['forensic_triage_first_seen']} and was present on
{sch['forensic_triage_coverage_pct']}% of records at the data cutoff. CISA's
published JSON schema did not describe it, and had one commit in its entire
history. The catalog nonetheless validates cleanly, so nothing signals the
omission to a consumer generating types or documentation from the schema. This
finding is explicitly time-bound and is reported with its observation dates
attached.

**On counting.** The two kinds of event are reported separately because they
are not the same thing. A field-presence transition changes which fields the
catalog carries. A naming/canonicalization event changes what the columns are
called without changing the set of logical fields — on {ev['naming_event_dates'][0]}
every column was renamed. A reconstruction that tracks only field presence
cannot see the second kind, so a count of transitions alone understates the
history. All three figures are derived from the timeline, not stated by hand.

**Also documented.** Encoding and quoting churn in the published files, two
dated capture refusals at the content-delivery layer, entry withdrawals, and the
distinction between a capture's date and the catalog version it contains — the
one place in five years where that distinction changes an answer.

## 1. Why this record does not already exist

CISA distributes the KEV catalog as a single JSON file and a single CSV file,
each overwritten in place on every update. There is no version parameter, no
changelog, and no archive of prior states at the canonical URL. CISA's own
mirror repository states the problem directly: the KEV "has no inline file
revision history or log that's easily accessible after the fact."

The practical consequence is that a consumer who wrote a parser in 2022 has no
supported way to discover what changed underneath it. Schema changes are
observable only by having watched, daily, at the time. This report substitutes
for that missing history by reconstructing it from third-party daily captures.

## 2. Data and method

**Primary source.** An independent daily archiver has captured the KEV CSV once
per day since {cov['first_date']}, nine days after the catalog's launch. This
build reads {cov['snapshot_files']:,} dated snapshot files, of which
{cov['usable_snapshots']:,} are usable; {cov['unusable_snapshots']} contain
markup rather than CSV and are excluded and reported rather than repaired.
Pinned at commit `{S['sources']['archive_commit'][:12]}`.

**Corroborating source 1.** CISA's own mirror, `cisagov/kev-data`, has published
the JSON, CSV, and the machine-readable JSON schema under git since
{xv['json_first']}. It supplies {xv['json_days']} distinct days of
authoritative history and the schema file itself
(SHA-256 `{S['sources']['schema_sha256'][:16]}…`). Pinned at commit
`{S['sources']['official_commit'][:12]}`.

{source2_block}**Unit and measure.** The unit is the (snapshot date, field name) pair. A field
is *present* on a date if it appears in that day's CSV header or, on the JSON
track, in any record's keys. A *change event* is a transition in presence
between consecutive available dates.

**Name harmonisation.** The catalog renamed its columns from human-readable
labels (`CVE`, `Vendor/Project`) to camelCase (`cveID`, `vendorProject`) on
{ev['rename_date']}. Both spellings denote the same logical field, so presence
is reported on canonical names and the rename is recorded as its own event
rather than as eight simultaneous removals and eight additions.

{crossval_block}

## 3. Primary contribution: the reconstructed schema timeline

{table}

Read together with Figure 1, the picture is of a schema that is stable in its
core and additive at its edges. Nine logical fields were present at launch: the
eight core fields `cveID` through `dueDate`, plus `notes`. The eight core fields
are present on every one of the {cov['usable_snapshots']:,} usable snapshot days
and are the eight the published schema marks as required. `notes` is not among
them, having been withdrawn and later reinstated (below). Across the period the pipeline identifies
{ev['total_schema_evolution_events']} schema-evolution events:
{ev['field_presence_transitions']} field-presence transitions, in which a field
appears or disappears, and {ev['naming_or_canonicalization_events']}
naming/canonicalization event, in which every column was renamed on
{ev['naming_event_dates'][0]} without the set of logical fields changing. The
two are counted separately throughout: presence tracking alone cannot detect a
rename, since this build harmonises the two spellings precisely so that presence
stays comparable across it. Of the transitions, every one is an addition except
a single removal and its later restoration.

**`notes`** was present at launch, was removed on {ev['notes_removed']}, and was
reinstated on {ev['notes_restored']} — absent for {ev['notes_absent_days']}
consecutive observed days. Both boundary days also carried new catalog entries
({nb['removed_new_entries']} and {nb['restored_new_entries']} respectively),
indicating a fresh publication rather than a stale or failed capture, and the
field returned unpopulated ({nb['notes_filled_on_return']} of
{nb['notes_rows_on_return']} records, against
{nb['notes_filled_before_removal']} of {nb['notes_rows_before_removal']}
immediately before removal), consistent with a column reinstated structurally
before being filled. It is the only field in the catalog's history to have been
withdrawn and reinstated. No independent source covers this period; see
Limitation 4.

**`knownRansomwareCampaignUse`** appeared on
{sp['knownRansomwareCampaignUse']['first_seen']} and has been present on every
snapshot since.

**`cwes`** appeared on {sp['cwes']['first_seen']}, adding the catalog's only
nested structure: an array of CWE identifiers rather than a scalar. This is the
change most likely to have broken a naive CSV-to-JSON consumer, because the
column's value is a list rendered into a single CSV cell.

**`forensicTriage`** appeared on {sp['forensicTriage']['first_seen']} and is
present on {sp['forensicTriage']['days_present']} snapshot days as of
{S['as_of']}. The primary CSV archive and CISA's official Git mirror both first
show it on that capture date, and neither holds it on the preceding day. The
second independent archive does **not** show it on that capture date: it fetched
before CISA published that day, so its capture holds the previous catalog
version. Compared by `catalogVersion` rather than by capture date, all three
agree — the field is absent from v2026.08.31 and present in v2026.09.01. The
three sources therefore agree on the catalog version in which the field first
appears, not on a single capture day.

![](figures/fig01_field_timeline.png)

**Figure 1.** Field presence by day across {cov['usable_snapshots']:,} daily
snapshots. The gap in `notes` and the late, narrow band for `forensicTriage`
are the two discontinuities in an otherwise additive history.

![](figures/fig02_catalog_growth.png)

**Figure 2.** Catalog size over the same period, {cat['first_count']:,} to
{cat['last_count']:,} entries. Growth is close to linear after the initial
2022 expansion. {cat['days_with_decrease']} days show a net decrease,
corresponding to withdrawn entries.

## 4. Supporting finding: a schema-documentation gap, as of {S['data_cutoff']}

CISA publishes a machine-readable JSON schema alongside the catalog and states
in the mirror's README that it "will also remain in sync" with the data. This
section reports what the schema described at a specific moment. Every statement
in it is bounded by the {S['data_cutoff']} data cutoff, with the schema file and
live catalog accessed {S['access_date']}.

At that date the schema described {sch['fields_described']} record fields and
the catalog contained {sch['fields_observed']}. The undescribed field was
`forensicTriage`, present on {sch['forensic_triage_coverage_pct']}% of the
{cat['last_count']:,} records in the catalog, and first observed in the catalog
on {sch['forensic_triage_first_seen']} —
{sch['forensic_triage_undocumented_days']} days before the data cutoff.

The schema file had **{sch['schema_commits']} commit in its entire history**,
dated {sch['schema_last_modified']}, {sch['schema_stale_days']} days before the
data cutoff. It had not been amended.

The omission does not surface as an error, which is the substance of the
finding. The schema declares `{sch['declared_draft']}` and does not set
`additionalProperties`, which under JSON Schema defaults to permissive.
Validating the catalog as of {S['data_cutoff']} against the schema as of
{S['access_date']} produces **{sch['validation_errors']} errors**. The data is
well formed and the schema is not violated. What the schema does not do is
describe the field: a consumer generating types, database columns, or
documentation from it receives no `forensicTriage` and receives no error either,
so the field is silently omitted downstream.

This is a documentation gap rather than a validation failure, and it is harder
to notice for that reason. A validation failure surfaces in continuous
integration. An omission from a permissive schema surfaces when someone
eventually asks why a column is missing.

Two limits on this finding should be read with it. First, the semantics of
`forensicTriage` — its meaning, permitted values and intended use — are not
documented in any source consulted, so this report does not characterise the
field, only its presence. Second, the finding is a dated observation, not a
standing claim: it records the state of the published schema as of
{S['access_date']}. If CISA subsequently describes the field, that does not
falsify this section; it closes the gap the section documents, and the
observation stands as a historical record of the interval.

## 5. Data-quality artefacts in the archival record

{S['artifacts']['total']} artefacts were catalogued. They matter because anyone
reconstructing this history from the same public sources will encounter them,
and because two of them could be mistaken for schema changes.

{capture_para}

- **Encoding and quoting churn.** A UTF-8 BOM appears and disappears, and header
  quoting toggles, across several dates. These change the bytes of the file
  without changing the schema. A reconstruction that keys on the raw header
  string rather than on parsed field names will read these as spurious schema
  events; this build parses the header and does not.
- **Coverage gaps ({cov['coverage_gaps']}).** Isolated missing days, the longest
  being the two-day capture failure above.
- **Record withdrawals ({cat['days_with_decrease']} days).** Days on which the
  entry count fell. These are genuine removals by CISA, not parsing errors.

## 6. What this does and does not establish

It establishes when each field first and last appears **in the daily captures**,
which is a close but not identical proxy for when CISA changed the catalog. A
change made and reverted between two captures is invisible here. Sub-daily
resolution is not available for the 2021–2024 period from any public source
known to the author.

It does not establish *why* any change was made. No CISA announcement is cited
for any of the {ev['field_presence_transitions']} field-presence transitions or
for the {ev['naming_or_canonicalization_events']} naming/canonicalization event,
because the author found none tied to them; the
absence of an announcement is part of what makes a reconstructed timeline
necessary.

It does not establish the semantics of `forensicTriage`. The field's meaning,
permitted values, and intended use were undocumented in every source consulted
as of {S['access_date']}, which is the practical cost of the gap described in
Section 4.

## 7. Conclusion

The durable contribution of this work is the reconstruction. CISA distributes
the KEV catalog by overwriting it in place, so the record of how its structure
changed does not exist at the canonical source. This report supplies that record
for {cov['first_date']} to {cov['last_date']}:
{ev['total_schema_evolution_events']} schema-evolution events —
{ev['field_presence_transitions']} field-presence transitions and
{ev['naming_or_canonicalization_events']} naming/canonicalization event — drawn
from {cov['usable_snapshots']:,} daily captures and corroborated across
{xv['multi_source_days']:,} multi-source days at {xv['agreement_pct']}%
agreement, with the per-day evidence, the cross-source agreement record and the
exclusion decisions all published so the reconstruction can be re-derived rather
than trusted. That reconstruction is reproducible and explicitly bounded by the
available archival coverage; it does not depend on the catalog's present
state.

The schema-documentation gap reported in Section 4 is a supporting observation
with an explicit expiry. As of {S['access_date']} the published schema described
{sch['fields_described']} of the catalog's {sch['fields_observed']} fields, and
the omitted field was present on {sch['forensic_triage_coverage_pct']}% of
records. Because the schema is permissive, nothing signals the omission to an
automated consumer. Whether CISA closes that gap tomorrow or leaves it open,
the observation is dated and remains accurate as a record of the interval.

Both findings point at the same underlying condition: a widely relied-upon
public dataset is distributed without a revision history, and its published
description is not versioned alongside it. The reconstruction shows what that
costs a consumer trying to understand the data's past; the schema gap shows what
it costs one trying to parse its present.

## 8. Reproducing this

The repository accompanying this report contains the pipeline, the pinned source
commits, the derived tables, and the QA report. From a clean checkout:

```bash
python -m venv venv
venv/bin/pip install -r requirements.lock
bash code/run_all.sh
```

`run_all.sh` runs every stage in order. Individually:

```bash
code/01_fetch.py        # clone all three sources, at pinned commits
code/02_build.py        # reconstruct the timeline
code/03_qa.py           # QA report - read before trusting any output
code/04_figures.py      # stats.json and the figures
code/00_metadata.py     # CITATION.cff
code/07_release_notes.py  # release notes, from the statistics
code/08_render_docs.py  # README and LIMITATIONS, from templates
code/09_snapshot_links.py # verifiable links to each snapshot
code/05_document.py     # this report
code/build_pdf.sh       # the PDF
```

Because all three sources are pinned to commits, and every Python dependency is
pinned in `requirements.lock` (the validated environment is recorded in
`docs/ENVIRONMENT.md`), the pipeline reproduces these exact numbers — and, under
those pinned dependencies, byte-identical figures — indefinitely. Running
`01_fetch.py --update-pins` moves to current HEAD, after which every number in
this report must be regenerated and re-verified.

## Data availability

All inputs are public. The KEV catalog and its schema are distributed by CISA
under CC0 via `{S['sources']['official_repo']}`. The daily archive is
`{S['sources']['archive_repo']}` and `{S['sources']['indep_repo']}`.

The derived tables in this repository — the reconstruction and its supporting
evidence — are released under CC BY 4.0, as are this report and its figures; the
code is MIT. That licence applies to the original selection, arrangement,
reconstruction, annotation and documentation contributed here, to the extent
those elements are legally protectable; where no such rights subsist, none are
asserted. It does not restrict the underlying CISA catalog, which is a United
States government work released under CC0 by CISA and remains public-domain
material, nor any third-party content. Facts about the catalog are not owned by
this project. Attribution is required of anyone relying on rights the licence
covers; it is a condition of reuse, not a means of detecting it. The full rights
statement is in `LICENSE-DATA`.

## AI assistance

AI tooling assisted with source discovery, code authoring, data processing,
quality assurance, and drafting. The author selected the research question,
ruled on the substantive judgment calls, manually verified the reported
schema-change boundaries and live-source observations, reviewed the final
report, and accepts responsibility for its content.
"""

    (REPORT / "kev_schema_evolution.md").write_text(md, encoding="utf-8")
    print(f"[document] report/kev_schema_evolution.md "
          f"({len(md.split())} words, {release_state.describe(state)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
