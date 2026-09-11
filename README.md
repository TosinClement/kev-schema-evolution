<!-- GENERATED from templates/README.md.template by code/08_render_docs.py. Edit the template, not this file. -->
# Schema Evolution in the CISA Known Exploited Vulnerabilities Catalog, 2021–2026: A Three-Source Reconstruction

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.22699424.svg)](https://doi.org/10.5281/zenodo.22699424)

> **STATUS: released v0.1.0 — DOI [10.5281/zenodo.22699424](https://doi.org/10.5281/zenodo.22699424) — released 2026-09-11.**
> Data cutoff 2026-09-09; sources accessed 2026-09-11.

A dated, three-source reconstruction of how the CISA Known Exploited
Vulnerabilities (KEV) catalog's structure changed between 2021 and 2026, built
from 1,758 daily catalog snapshots and
cross-validated against two additional sources — CISA's official Git mirror and
a second independent archive — across
1,115 multi-source days at
99.91% agreement.

**Primary contribution.** CISA overwrites its catalog files in place and
publishes no changelog, so the history of the data's structure is not
recoverable from the canonical source. This repository supplies it:
6 schema-evolution events, dated
and corroborated, with the per-day evidence, the cross-source agreement record
and the source-exclusion decisions all published so the reconstruction can be
re-derived rather than trusted. This finding is durable and does not depend on
the catalog's current state.

Those 6 events are of two kinds,
counted separately because they are not the same thing:
5 **field-presence transitions**, in
which a field appears in or disappears from the catalog, and
1
**naming/canonicalization event**, in which every column was renamed
(2021-12-01) without the set of logical fields
changing. Presence tracking alone cannot see the second kind, so a count that
reports only transitions understates the history. All three figures are derived
from `data/processed/schema_timeline.csv`; none is typed by hand.

**Supporting finding, time-bound.** As of the 2026-09-09 data cutoff,
sources accessed 2026-09-11, the field `forensicTriage` was present
on 100% of records in the live catalog
but was not described in CISA's published JSON schema, which had one commit in
its entire history, 590 days earlier. Because the
schema does not restrict additional properties, the catalog validates without
error, so the omission does not surface as a validation failure. This is a
schema-documentation gap reported as observed on the stated dates. If CISA
subsequently describes the field, the dated observation remains accurate as a
record of the interval.

## What is here

```
code/          numbered pipeline scripts, run in order
data/raw/      provenance log, pinned source commits, the published schema
data/processed/derived tables and the QA report
docs/          build spec, codebook, limitations, verification checklist, publish guide
report/        stats.json, figures, tables, the report itself
```

## Reproducing it

Use the pinned environment. Validated on Python 3.11.15, Linux x86_64; see
`docs/ENVIRONMENT.md` for the system-level tools (`git`, and `pandoc` +
`wkhtmltopdf` for the PDF only).

```bash
python -m venv venv
venv/bin/pip install -r requirements.lock
bash code/run_all.sh
```

`code/run_all.sh` runs every stage in order. The stages are also runnable
individually and each is idempotent:

```
code/01_fetch.py        clone the three sources at pinned commits
code/02_build.py        reconstruct the timeline
code/03_qa.py           QA report — read this before trusting anything
code/04_figures.py      stats.json and figures
code/00_metadata.py     CITATION.cff, from metadata.json + AUTHORS.json + stats
code/07_release_notes.py  docs/RELEASE_NOTES.md, from stats
code/08_render_docs.py  README.md and docs/LIMITATIONS.md, from templates + stats
code/05_document.py     the report
code/build_pdf.sh       the PDF
```

All three sources are pinned to specific commits and all Python dependencies are
pinned in `requirements.lock`, so the pipeline reproduces the same numbers — and,
under the pinned dependencies, byte-identical figures — indefinitely.
`python code/01_fetch.py --update-pins` moves to current HEAD, after which every
number must be regenerated and re-verified.

**Generated files.** `README.md`, `docs/LIMITATIONS.md`, `CITATION.cff` and
`docs/RELEASE_NOTES.md` are generated. Edit `templates/` and `metadata.json`
instead; the QA report fails if a generated file has been hand-edited.

Read `data/processed/qa_report.txt` before trusting any output. It reports
coverage, cross-source agreement, schema conformance, and six named spot checks
you can reproduce by hand against the sources.

## Sources

| Source | Role | Coverage | Pinned commit | License |
|---|---|---|---|---|
| [hrbrmstr/cisa-known-exploited-vulns](https://github.com/hrbrmstr/cisa-known-exploited-vulns) | daily CSV snapshots | 2021-11-12 → 2026-09-09 | `3e428cea` | MIT (tooling); archived content public domain |
| [cisagov/kev-data](https://github.com/cisagov/kev-data) | CISA official mirror: JSON, CSV, published schema | 2025-01-27 → 2026-09-09 | `f6fafe25` | CC0-1.0 |
| [lucagrippa/cisa-kev-archive](https://github.com/lucagrippa/cisa-kev-archive) | independent daily JSON (`json/` tree only) | 2023-08-18 → 2026-09-10 | `276aa250` | **no licence file on the repository**; archived content is CISA CC0 |

Accessed 2026-09-11. **Only the third source's `json/` tree is read.** Its
`csv/` tree is excluded in full: for all 668
dates before 2023-09-12 those files are byte-identical to the
hrbrmstr archive, i.e. back-filled copies rather than an independent record; from
2023-09-12 onward they duplicate dates already covered by its
JSON. Per-date hashes are in `data/raw/third_source_csv_identity.csv` and the
full provenance record in `data/raw/third_source_manifest.json`.

That repository has no licence file. This build reads its archived CISA
public-domain content for verification only and redistributes none of its files;
`sources/` is git-ignored. See `docs/LIMITATIONS.md` items 12 and 13.

`www.cisa.gov` was not reachable from the build environment, so CISA's own
GitHub mirror was used as the authoritative source. This is recorded in
`docs/LIMITATIONS.md` rather than glossed over.

## Limitations

See `docs/LIMITATIONS.md`. The short version: snapshot dates are a close proxy
for change dates, not the changes themselves; sub-daily changes are invisible;
the events before 2023-08-18 predate any corroborating
source and rest on one archiver; no CISA announcement is cited for any event because none was
found; and the semantics of `forensicTriage` are undocumented upstream, so this
report does not speculate about them.

## License

| Component | License |
|---|---|
| Code (`code/`) | MIT — `LICENSE` |
| Derived data (`data/processed/`, `data/raw/`) | CC BY 4.0 — `LICENSE-DATA` |
| Report and figures (`report/`) | CC BY 4.0 — `LICENSE-REPORT` |

**Rights statement.** CC BY 4.0 applies to the original selection, arrangement,
reconstruction, annotation and documentation contributed by this project, to the
extent those elements are legally protectable; where no such rights subsist,
none are asserted. It does not restrict the underlying CISA KEV catalog, which
is a US government work released under CC0 by CISA and remains public-domain
material, nor any third-party content. Attribution is required from anyone
relying on rights the licence covers; the licence is a condition of reuse, not a
mechanism for detecting it. Full statement in `LICENSE-DATA`.

## Citation

See `CITATION.cff`. Once released and deposited, cite the versioned DOI.

## Author

Tosin Clement, Independent Researcher
ORCID [0009-0001-2055-5113](https://orcid.org/0009-0001-2055-5113)
