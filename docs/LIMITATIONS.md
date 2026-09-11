<!-- GENERATED from templates/LIMITATIONS.md.template by code/08_render_docs.py. Edit the template, not this file. -->
# Limitations

Numbered, specific, and written before the report's discussion so the report
cannot outrun them.

## 1. Snapshot dates are a proxy for change dates

A field's "first seen" date is the first *daily capture* containing it, not the
moment CISA changed the catalog. The true change occurred at some point in the
interval between the previous capture and that one — up to roughly 24 hours
earlier, longer across a coverage gap. Every date in this report should be read
as "first observed on", not "changed on".

## 2. Sub-daily changes are invisible

A field added and removed between two captures leaves no trace. The catalog is
typically updated on weekday afternoons US Eastern; a same-day add-and-revert
would not appear here. Nothing in the record suggests this happened, but the
method could not detect it if it had.

## 3. Coverage is 99.72%, not 100%

4 coverage gaps and
2 unusable captures (where the
archiver stored an Akamai edge "Access Denied" response rather than CSV; see the
report, Section 5). Missing days are excluded, never interpolated. A change
occurring entirely within a gap would be dated to the next available capture.

## 4. The period before corroboration rests on a single source

Corroboration begins 2023-08-18, when the second
independent JSON archive starts; CISA's own mirror begins later still,
2025-01-27. Before
2023-08-18 the timeline depends entirely on one
archiver.

Of the 6 schema-evolution events,
three fall in that uncorroborated window: the naming/canonicalization event of
2021-12-01, the removal of `notes` on
2021-12-11, and its restoration on
2022-05-24. The three later events —
`knownRansomwareCampaignUse` (2023-10-12),
`cwes` (2024-06-26) and
`forensicTriage` (2026-09-01) — are each
confirmed by at least two independently collected sources.

Agreement across 1,115 multi-source days
is 99.91%, with the single exception
explained in the report as a fetch-timing artefact. That is strong evidence the
primary archiver is faithful, but it is not proof of fidelity for the period
preceding corroboration. The three earliest events should be treated as
well-supported rather than independently confirmed.

No further corroboration was available. A second candidate archive was examined
and its CSV files were rejected as corroboration. For all 668 shared
dates before 2023-09-12 they are byte-identical to the primary
archiver's, having been back-filled from them, so they are a copy rather than a
witness. The 163 later shared dates that do differ are already
covered by that repository's independently collected JSON, which this build does
use, so counting both formats would count one collector twice. Item 13 gives the
full breakdown. The Wayback Machine was not reachable from the build
environment.

## 5. CSV is a lossy view of the catalog

The 2021–2024 reconstruction reads CSV headers. CSV flattens the nested `cwes`
array into a single cell and cannot express the JSON structure. Field
*presence* is recoverable from CSV; field *type and structure* are not, before
2025.

## 6. Canonical-name harmonisation is an analytic choice

The 2021-12-01 rename from human-readable labels to camelCase is treated as one
rename event affecting nine fields, rather than nine removals and nine
additions. That mapping is an interpretation. It is stated explicitly in
`code/02_build.py` (`LABEL_TO_CANONICAL`) and a reader who disagrees can
recompute without it.

## 7. No causal or motivational claims

No CISA announcement, directive, or release note is cited for any of the five
change events, because the author found none tied to them. This report says
when things changed, not why. The absence of a discoverable announcement is
itself part of the motivation for the work, but it is not evidence that no
announcement exists.

## 8. `forensicTriage` semantics are unknown

The field's meaning, permitted values, cardinality, and intended use are not
documented in any source consulted. This report deliberately does not infer them
from the values observed. Nine days of data is not a basis for characterising a
field.

## 9. The central finding is time-sensitive

The schema gap described in Section 4 of the report is true as of 2026-09-09. If
CISA updates the published schema, the finding becomes historical rather than
current. Every output is stamped with its as-of date for this reason. A reader
encountering this report later should re-check the live schema before treating
the gap as current.

## 10. canonical cisa.gov was not directly reachable from the build environment

The build environment could not reach `www.cisa.gov` (egress policy), so the
current catalog and schema were read from `cisagov/kev-data`, CISA's own mirror,
which CISA states is synchronised with the canonical source within minutes. This
is a strong substitute but it is a substitute.

That substitution was checked. On 2026-09-10 the author fetched the
canonical catalog URL directly and counted `forensicTriage`
1,703 times — matching the record count derived here
from the mirror — and confirmed against CISA's published schema and its commit
history that the field is not described, that `"additionalProperties": false`
does not appear, and that the schema file carries a single commit dated
2025-01-27. The mirror and the canonical source
agreed on every point the report depends on. See `docs/VERIFY_CHECKLIST.md`
Section B for the URLs and the author's record.

## 11. Single-analyst work

One author, one pipeline, no independent replication. The QA report and the
pinned commits exist so that a second party can replicate cheaply; none had done
so at the time of release.

## 12. The third source carries no licence file

Corroboration from 2023-08-18 onward depends in part on
`https://github.com/lucagrippa/cisa-kev-archive.git`, which has no licence file. Its archived content is the CISA
Known Exploited Vulnerabilities catalog, a US government work released under CC0
by CISA, so the underlying data is unrestricted. This build reads that
public-domain content for verification only, and redistributes nothing from the
repository: the working clone lives in the git-ignored `sources/` directory, and
what this project publishes about it is limited to hashes, counts and dates.

This is nonetheless a looser footing than the other two sources, both of which
state their terms explicitly, and a reader weighing the corroboration should
know it. Accessed 2026-09-11, pinned at commit
`276aa25018e0b1ba945ea0638f71682bd70422c1`.

## 13. Only the third source's JSON is treated as evidence

That repository also holds CSV files, and they are excluded in full. Hashing
every date both repositories hold
(1,753 dates)
gives the complete picture:

1. For all 668 dates before
   2023-09-12, its CSV is byte-identical to the primary
   archive's and appears to be a back-filled copy rather than an independent
   record of the catalog.
2. 163 later shared-date files differ, and from
   2023-09-12 onward the repository appears to collect
   its own CSVs.
3. The entire CSV tree is nonetheless excluded from independent corroboration,
   because the independently collected JSON series already represents this
   record keeper, and counting both formats would duplicate one collector.

The consequence is that the corroboration is narrower than the repository's
apparent coverage suggests: it begins
2023-08-18, not 2021. Per-date
hashes are published in `data/raw/third_source_csv_identity.csv` so a reader can
re-derive this instead of accepting it.

## 14. Two kinds of schema-evolution event are counted separately

This report counts 6
schema-evolution events: 5
field-presence transitions and
1 naming/canonicalization
event. The distinction matters and the two should not be summed casually.

A field-presence transition changes which fields the catalog carries. A
naming/canonicalization event changes what the columns are called without
changing the set of logical fields: on 2021-12-01
every column was renamed from a human-readable label to camelCase, and this
build harmonises the two spellings so that presence remains comparable across
the rename. A reconstruction that tracks only field presence cannot see that
event at all, which is why it is derived separately, from the published headers
rather than from the harmonised field names.

Readers comparing this count with another analysis should check which definition
that analysis used. All three figures here are derived from
`data/processed/schema_timeline.csv`.
