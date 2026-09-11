# Build spec — KEV schema evolution, 2021–2026

**Status: DRAFT — not verified, not released.**

```
PROJECT:        Schema evolution in the CISA Known Exploited Vulnerabilities
                catalog, 2021-2026.
                Archetypes: technical report (primary) + dataset (secondary,
                the reconstructed schema timeline is a reusable artifact).

QUESTION:       When did each field in the CISA KEV catalog appear, change, or
                disappear, and does CISA's published machine-readable schema
                accurately describe the data it distributes?

SOURCES:        1. hrbrmstr/cisa-known-exploited-vulns
                   https://github.com/hrbrmstr/cisa-known-exploited-vulns
                   Independent daily archiver. 1,760 dated CSV snapshots,
                   2021-11-12 .. 2026-09-09. Pinned at commit
                   3e428ceaa1e18ce466db17c8b4c23f5a23e53c92 (2026-09-09).
                   License: MIT (archive tooling); archived content is CISA's,
                   which is public domain / CC0.
                   Access date: 2026-09-10.

                2. cisagov/kev-data
                   https://github.com/cisagov/kev-data
                   CISA's own mirror of the KEV data files, including the
                   published JSON schema. 434 commits, 2025-01-27 .. 2026-09-09.
                   Pinned at commit
                   f6fafe2585c7cc2a7568d13d08024cf142b37d3a (2026-09-09).
                   License: CC0.
                   Access date: 2026-09-10.

                Note: www.cisa.gov is not reachable from the build environment
                (egress policy). Source 2 is CISA's own authoritative GitHub
                mirror and is the canonical substitute; this is recorded in
                LIMITATIONS.md rather than hidden.

UNIT:           The (snapshot date, field name) pair. One row per field per day
                of catalog history.

MEASURES:       field_present      1 if the field appears in that day's snapshot
                                   header (CSV) or record keys (JSON), else 0
                first_seen         earliest snapshot date a field appears
                last_seen          latest snapshot date a field appears
                days_present       count of snapshot days where present
                change_event       a transition in field_present between
                                   consecutive available snapshot dates
                schema_lag_days    days between a field entering the data and
                                   the published schema describing it; open-ended
                                   where the schema still does not describe it
                agreement_rate     share of overlap days where the CSV-derived
                                   and JSON-derived field sets agree

OUTPUTS:        data/processed/field_presence_matrix.csv    day x field, 0/1
                data/processed/schema_timeline.csv          change events
                data/processed/artifacts.csv                data-quality events
                data/processed/qa_report.txt                QA
                report/stats.json                           every cited number
                report/figures/fig01_field_timeline.png     presence timeline
                report/figures/fig02_catalog_growth.png     record count growth
                report/tables/table01_change_events.md
                report/kev_schema_evolution.md              the report
                report/kev_schema_evolution.pdf             typeset report

VENUES:         1. GitHub (repository + tagged release v0.1.0)
                2. Zenodo (deposit of the release archive, mints DOI)
                3. Optional later: arXiv cs.CR as a short technical note

VERIFY POINTS:  Mechanical checks (reproduce the pipeline; confirm the finding
                against live CISA; spot-check six dates) are sections A, B and C
                of docs/VERIFY_CHECKLIST.md.

                The five judgment calls that need the author's ruling, and that
                the data cannot settle, are section D of that checklist:
                V1 the notes round trip; V2 the 2024-11-26/27 capture failures;
                V3 pre-2025 single-source reliance; V4 the CC0 derived-data
                choice; V5 publishing a nine-day-old finding.
                docs/VERIFY_CHECKLIST.md is the authoritative list; this spec
                does not restate it.

LICENSE:        Code: MIT
                Derived data: CC-BY-4.0, applying to the original selection,
                             arrangement, reconstruction, annotation and
                             documentation contributed here, to the extent
                             legally protectable. Does not restrict the
                             upstream CISA catalog (CC0, public domain) or
                             third-party content. Attribution is a condition
                             of reuse, not a detection mechanism.
                             Full statement: LICENSE-DATA.
                Report and figures: CC-BY-4.0

ASSUMPTIONS:    A1. GitHub username supplied by the author: TosinClement.
                    Repository URL github.com/TosinClement/kev-schema-evolution.
                A2. "Daily catalog versions" is operationalised as the archiver's
                    daily CSV snapshot, which is a capture of the catalog, not
                    the catalog's own version history. CISA publishes no
                    inline revision log; this is stated as a limitation.
                A3. Report is as-of 2026-09-09. forensicTriage is nine days old
                    at that date and the finding may be overtaken by a schema
                    update; the as-of date is printed on every output.
```

## Why this project, released now

The brief calls this the first public artifact of the program, released early to
prove the pipeline end to end. That purpose is served whether or not any single
finding is large.

The primary contribution is the reconstruction itself: a dated, three-source
history of the catalog's structure that does not exist at the canonical source
and does not depend on the catalog's current state. A supporting, time-bound
observation is also reported: as of the data cutoff, the published JSON schema
did not describe a field then present on every record. That is a
schema-documentation gap, reported with its observation dates attached, not a
claim that the schema is incorrect.
