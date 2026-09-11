# Next steps

`v0.1.0` is deliberately narrow: one catalog, field-level presence, five years.
It is the first artifact of the program and its job is to prove the pipeline
end to end. These are the directions that would make it more than that.

## v0.2 — value-level evolution

Presence is the coarsest possible measure, and v0.1 verification turned up a
concrete example of what it misses: between the 2024-11-25 and 2024-11-28
captures, `CVE-2023-28461`'s `vulnerabilityName` changed from "Improper
Authentication Vulnerability" to "Missing Authentication for Critical Function
Vulnerability". No field appeared or disappeared, so v0.1 records nothing. The
next version should track *within-field* change: when `knownRansomwareCampaignUse` values shifted between
`Known`/`Unknown` vocabularies, how `cwes` cardinality is distributed, whether
`dueDate` intervals changed after BOD revisions. This is a larger build because
it requires parsing every record on every day rather than only headers.

## v0.3 — parser-impact analysis

For each change event, classify what it would do to a naive consumer: silent
column drop, type error, crash, or nothing. `cwes` is the interesting case — a
nested array flattened into CSV. This converts the report from a chronology into
something a practitioner acts on, and was scoped out of v0.1 deliberately.

## v0.4 — the same treatment for adjacent catalogs

CVE List V5 and Vulnrichment are both git-versioned and both feed the same
pipelines. A comparative schema-stability analysis across the three would say
something about vulnerability-data governance generally rather than about KEV
specifically.

## Continuous monitoring

The pipeline is cheap to run. A scheduled job that re-runs it and opens an issue
whenever a new field appears — or whenever the published schema changes — would
turn this from a snapshot into a service, and would catch the next
`forensicTriage` on the day it lands rather than nine days later.

## Upstream contribution

The most useful outcome of this work is not the report. It is CISA updating the
published schema to describe `forensicTriage`. `cisagov/kev-data` accepts issues
for "accidental schema violations and the like". Filing one, citing this
analysis, is a concrete next action and arguably the point of the exercise.
