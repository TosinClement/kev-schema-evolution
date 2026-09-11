# Codebook

Every derived file, every column, its definition, source, and transformation.

## `data/processed/field_presence_matrix.csv`

One row per usable daily snapshot. The primary derived table.

| Column | Type | Definition |
|---|---|---|
| `date` | ISO date | Snapshot date, taken from the archive filename `YYYY-MM-DD-cisa-kev.csv`. |
| `n_records` | integer | Rows parsed from that day's CSV, excluding the header. Blank if the file could not be parsed as CSV. |
| `header_style` | string | `+`-joined encoding descriptors: `BOM` if a UTF-8 byte-order mark is present; `quoted`/`bare` for header field quoting; `label-case`/`camelCase` for the naming convention. Descriptive only — carries no schema meaning. |
| `cveID` … `cwes` | 0/1 | 1 if the canonical field is present in that day's header, else 0. Column order follows the catalog's own field order. |

Canonical naming: pre-2021-12-01 headers use human-readable labels. These are
mapped to camelCase equivalents (`CVE`→`cveID`, `Vendor/Project`→`vendorProject`,
`Date Added to Catalog`→`dateAdded`, `Action`→`requiredAction`, and so on) so
presence is comparable across the rename. The mapping lives in
`code/02_build.py` as `LABEL_TO_CANONICAL`.

## `data/processed/json_field_presence.csv`

The same measure computed from CISA's official JSON mirror. Independent of the
CSV track.

| Column | Type | Definition |
|---|---|---|
| `date` | ISO date | Commit date. Where a day has several commits, the last wins, matching the CSV track's daily grain. |
| `commit` | string | First 12 characters of the commit SHA. |
| `catalogVersion` | string | The catalog's own self-reported version string, e.g. `2026.09.09`. |
| `n_records` | integer | Length of the `vulnerabilities` array. |
| `cveID` … `cwes` | 0/1 | 1 if the field appears in **any** record that day. Presence is union-across-records, not per-record. |

## `data/processed/schema_timeline.csv`

Change events. The report's Table 1 is generated from this.

| Column | Type | Definition |
|---|---|---|
| `track` | string | `csv_daily` (independent archive) or `json_official` (CISA mirror). |
| `date` | ISO date | Date on which the new state was first observed. |
| `event` | string | `baseline` (first observation of a track), `field_added`, or `field_removed`. |
| `field` | string | Canonical field name. Empty for `baseline`. |
| `prev_date` | ISO date | The preceding observed date, i.e. the last date the old state held. |
| `detail` | string | Human-readable evidence, e.g. `absent on 2026-08-31`. For `baseline`, the full field list. |

## `data/processed/crosswalk.csv`

Cross-source agreement, one row per overlapping day.

| Column | Type | Definition |
|---|---|---|
| `date` | ISO date | A date covered by both tracks. |
| `csv_fields` / `json_fields` | string | `|`-joined sorted canonical field sets from each track. |
| `agree` | 0/1 | 1 if the two sets are identical. |
| `csv_only` / `json_only` | string | Fields in one track and not the other. Empty when `agree` is 1. |

## `data/processed/artifacts.csv`

Data-quality events. Descriptive, not corrections — nothing here is repaired.

| Column | Type | Definition |
|---|---|---|
| `date` | ISO date | Date the artefact was observed. |
| `kind` | string | One of: `unusable_snapshot` (markup captured instead of CSV), `bom_change`, `quoting_change`, `record_count_decrease`, `coverage_gap`. |
| `detail` | string | What changed and relative to which prior date. |
| `bytes` | integer | File size, where applicable. |

## `data/processed/catalog_growth.csv`

| Column | Type | Definition |
|---|---|---|
| `date` | ISO date | Observation date. |
| `n_records` | integer | Entry count. |
| `source` | string | `csv_daily` or `json_official`. Both tracks are included; filter before plotting to avoid double-counting overlap days. |

## `data/raw/PROVENANCE.txt`

Tab-separated append-only log. One line per fetch: UTC timestamp, source name,
URL, commit SHA, and detail (commit date, commit count, role, license; or bytes
and SHA-256 for individual files).

## `data/raw/source_pins.json`

The commit each source is pinned to, plus the SHA-256 and size of the published
schema file. This is what makes the build reproducible.

## `report/stats.json`

Every number quoted anywhere in the report. The report build interpolates from
this file; no number is typed into prose. Top-level keys: `as_of`,
`generated_utc`, `sources`, `coverage`, `catalog`, `fields`, `events`,
`crossvalidation`, `schema`, `artifacts`, `draft`.
