<!-- GENERATED FILE — do not edit by hand.
     Written by code/10_cisa_issue.py from report/stats.json, metadata.json and
     the canonical release state. Re-run the pipeline to refresh. -->

# Upstream issue text — cisagov/kev-data

File at <https://github.com/cisagov/kev-data/issues/new> **after** the Zenodo
deposit is published, never before (author ruling V5).

---

**Title:** Published JSON schema does not describe the `forensicTriage` field

The `forensicTriage` field has been present on records in
`known_exploited_vulnerabilities.json` since 2026-09-01 and, as of the
2026-09-09 data cutoff, appears on
100.0% of the 1,703 entries in
the catalog.

It is not among the properties of `$defs.vulnerability` in
`known_exploited_vulnerabilities_schema.json`, which has
1 commit in its entire history, dated
2025-01-27 — 590 days before that
cutoff.

Because `additionalProperties` is not set, the catalog still validates against
the published schema with 0 errors, so this does not
surface as a validation failure. The practical effect falls on consumers who
generate types, columns or documentation from the schema: they silently omit
the field.

Full timeline and method: https://doi.org/10.5281/zenodo.22699424 (DOI 10.5281/zenodo.22699424)

---

Filed for Schema Evolution in the CISA Known Exploited Vulnerabilities Catalog, 2021–2026: A Three-Source Reconstruction, v0.1.0, released 2026-09-11.
