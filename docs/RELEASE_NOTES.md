<!-- GENERATED FILE — do not edit by hand.
     Written by code/07_release_notes.py from report/stats.json, metadata.json
     and AUTHORS.json. Re-run the pipeline to refresh. code/03_qa.py fails if
     this file disagrees with the statistics. -->

# Release notes — v0.1.0

Paste the block below into the GitHub release body.

---

First release of **Schema Evolution in the CISA Known Exploited Vulnerabilities Catalog, 2021–2026: A Three-Source Reconstruction**.

A dated, three-source reconstruction of schema evolution in the CISA Known
Exploited Vulnerabilities catalog, which is published without a revision
history. Built from 1,758 daily snapshots spanning
2021-11-12 to 2026-09-09 (99.72% calendar
coverage) and cross-validated against two additional sources — CISA's official
Git mirror and a second independent archive — across
1,115 multi-source days
(223 of them carrying all three sources) at
99.91% agreement, with 1 disagreement,
explained in the report as a fetch-timing artefact.

**6 schema-evolution events**
(5 field-presence transitions and
1 naming/canonicalization event):

- 2021-12-01 — naming/canonicalization: columns renamed from human-readable labels to camelCase
- 2021-12-11 — field-presence transition: `notes` removed
- 2022-05-24 — field-presence transition: `notes` restored
- 2023-10-12 — field-presence transition: `knownRansomwareCampaignUse` added
- 2024-06-26 — field-presence transition: `cwes` added
- 2026-09-01 — field-presence transition: `forensicTriage` added

The two kinds are counted separately because they are different: a
field-presence transition changes which fields exist, while a
naming/canonicalization event renames every column without changing the set of
logical fields. Conflating them is what produced an inconsistent count in an
earlier draft.

**Supporting finding, time-bound.** As of the 2026-09-09 data cutoff,
with sources accessed 2026-09-11, `forensicTriage` was present on
100.0% of the 1,703 records in
the live catalog but was not described in CISA's published JSON schema, which
had 1 commit in its entire history, dated
2025-01-27 (590 days before the data
cutoff). Because that schema does not restrict additional properties, the
catalog validates against it with 0 errors, so the
omission does not surface as a validation failure. This is a
schema-documentation gap reported as observed on the stated dates; if CISA
subsequently describes the field, the dated observation remains accurate as a
record of the interval.

**Reproducibility.** All three sources are pinned to specific commits. Python
dependencies are fully pinned in `requirements.lock`; the validated environment
is documented in `docs/ENVIRONMENT.md`. Figures are byte-reproducible under the
pinned dependencies.

**Licences.** Code MIT; derived data CC BY 4.0; report and
figures CC BY 4.0. The upstream CISA catalog remains CC0 public-domain
material and is unrestricted; see `LICENSE-DATA` for the full rights statement.

Author: Tosin Clement, Independent Researcher, ORCID 0009-0001-2055-5113.
