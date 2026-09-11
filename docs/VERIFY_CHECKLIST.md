# Verification checklist

**Nothing in this repository is published until every box below is ticked by the
author personally.** The build is complete; the verification is not. This is the
gate between a pipeline output and a citable artifact carrying your name.

Work through it in order. Where a check fails, fix the pipeline and re-run —
do not edit an output by hand, because the next rebuild will silently revert it.

## A. Reproduce the pipeline — CLOSED

> **These boxes are superseded, not skipped.** They described a manual
> procedure the author was to run. At the author's direction the reproduction
> was instead performed automatically, twice, in isolated clean-room
> environments, and the author reviewed and accepted that evidence. Each item
> below is marked with what discharged it. The authoritative record is the
> Section A result that follows.

- [x] Fresh clone into an empty directory — done twice, in two separate
      temporary directories, each cloning all three sources from scratch.
- [x] Dependencies install — from `requirements.lock` (fully pinned, transitive
      included) into a fresh virtual environment in each clean room. The
      original line here read `pip install jsonschema matplotlib`, which was
      unpinned; defect A1 replaced it with the lock file.
- [x] `code/01_fetch.py` completes; `data/raw/source_pins.json` shows the pinned
      commits — three of them, not two: the third source was added under
      ruling V3 after this line was written.
- [x] `code/02_build.py` completes without error.
- [x] `code/03_qa.py` completes; every `PASS:` line reads `YES` — 10 gates now,
      not the 5 that existed when this line was written.
- [x] Figures and document build — plus `00_metadata`, `07_release_notes`,
      `08_render_docs`, `09_snapshot_links` and the PDF, all via
      `bash code/run_all.sh`.
- [x] Regenerated outputs match the committed ones — verified byte-for-byte
      between two independent clean-room runs, excluding only the timestamp
      files listed in `verification/VOLATILE.txt`.

### Section A — CLOSED, signed off by the author 2026-09-10

**Author's sign-off, in the author's words:**

> "Author reviewed and accepted the automated clean-room reproducibility
> evidence. The author did not personally execute the pipeline or independently
> test it on macOS."

**Scope of the sign-off.** The author signed off twice. The first acceptance was
given on the evidence from the initial pair of clean-room runs. A fifth defect
(A5, the snapshot counters) was then found and fixed, which changed the build,
so both clean-room runs were repeated. The author then reviewed the corrected
report — including the repaired counters and the two repeated runs — and
accepted that corrected evidence under the same qualification. **This sign-off
therefore covers the corrected build and the repeated clean-room runs recorded
in `verification/logs/`, not the superseded earlier runs.**

Signature: ______________________  Date: 2026-09-10

**Evidence this sign-off rests on.** Automated reproducibility test performed by
Claude in a clean Linux environment. Preserved in `verification/`:

| Record | Path |
|---|---|
| Clean-room run A, full log | `verification/logs/cleanroom-A.log` |
| Clean-room run B, full log (independent) | `verification/logs/cleanroom-B.log` |
| File-by-file comparison of A and B | `verification/logs/cleanroom-comparison.log` |
| SHA-256 manifest, 49 release files | `verification/SHA256SUMS.txt` |
| Files expected to vary between runs | `verification/VOLATILE.txt` |
| What the evidence does and does not show | `verification/README.md` |

**Result.** Both runs: all three pinned commits resolved from fresh clones; all
NINE QA gates YES; 1,758 usable snapshots; 1,115 multi-source days; 99.91%
agreement; 6 schema-evolution events (5 field-presence transitions, 1
naming/canonicalization); 1,703 entries at cutoff. Every data table, both
figures, the QA report and all four generated documents byte-identical between
the two independent runs. No manual intervention required.

**History of this section.** The first run found four defects (A1-A4), all now
closed and described below. After the author accepted the corrected evidence, a
FIFTH defect was found and fixed: the third source's refused capture had been
folded into the primary track's coverage counters, so stats.json reported 1,761
snapshot files against 1,760 on disk and docs/LIMITATIONS.md said "3 unusable
captures" where the report correctly said 2 days. A ninth QA gate now asserts
that the counters match the files on disk. Because that fix changed the build,
BOTH clean-room runs were repeated against the corrected archive, and the logs
and manifest above are from those repeated runs — not from the earlier ones the
author first reviewed. The author subsequently reviewed the corrected report and
accepted that corrected evidence, so the sign-off above is not stranded on the
superseded runs.

  A1  CLOSED. requirements.lock pins all dependencies including transitive;
      docs/ENVIRONMENT.md records the validated Python and system tools.
      04_figures.py fixes the font, replaces bbox_inches="tight" with a fixed
      canvas, and strips PNG metadata. Figures byte-identical across runs.
  A2  CLOSED, root cause worse than first reported: build_pdf.sh hardcoded the
      old title AND was failing silently (an en-dash in the title could not be
      encoded by wkhtmltopdf; pandoc aborted; the script exited 0 leaving the
      previous PDF in place). Title now from metadata.json, passed ASCII-safe
      via pagetitle; the script verifies the PDF was rewritten and exits
      non-zero if not. QA Q9 checks the rendered PDF.
  A3  CLOSED. The naming/canonicalization event is derived from the published
      headers by 02_build.py. stats.json carries
      total_schema_evolution_events=6, field_presence_transitions=5,
      naming_or_canonicalization_events=1. README and LIMITATIONS render from
      templates/ so no count is typed. QA Q11 checks it.
  A4  CLOSED. docs/RELEASE_NOTES.md generated by 07_release_notes.py.
      PUBLISH_GUIDE points at it; its stale block is gone. QA Q10 checks it.
  A5  CLOSED. Coverage counters filtered to the primary track; QA Q1 asserts
      counted == files on disk.

All new QA checks were negative-tested: injecting a stale title, a stale figure
and a hand-edit each produced the expected FAIL.

## B. Confirm the headline finding against the live sources — CLOSED

**Performed personally by the author on 2026-09-10.** This is the one check in
the whole verification that Claude could not do: the build environment cannot
reach `www.cisa.gov` (see LIMITATIONS item 10), so the canonical catalog had to
be read from CISA's GitHub mirror. The author reached the canonical URL directly.

**URLs checked.** URL 2 is a branch URL, which is what the author actually
visited and is recorded as such; row 2a gives the immutable equivalent so the
same file can be re-examined after the branch moves.

| # | URL |
|---|---|
| 1 | `https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json` |
| 2 | `https://github.com/cisagov/kev-data/blob/develop/known_exploited_vulnerabilities_schema.json` |
| 2a | Permanent equivalent, pinned to the commit this build read: `https://github.com/cisagov/kev-data/blob/f6fafe2585c7cc2a7568d13d08024cf142b37d3a/known_exploited_vulnerabilities_schema.json` |
| 3 | `https://github.com/cisagov/kev-data/commits/develop/known_exploited_vulnerabilities_schema.json` |

**Observations recorded by the author**

- [x] The live CISA KEV catalog contains `forensicTriage` **1,703 times**.
      (Matches the pipeline's record count of 1,703 exactly: the field is on
      every entry, which is what the report claims.)
- [x] CISA's published JSON schema contains `forensicTriage` **0 times**.
- [x] The schema contains `"additionalProperties": false` **0 times**.
      This is the load-bearing detail. Its absence is why the catalog validates
      cleanly against a schema that does not describe the field, which is the
      report's central explanation in Section 4.
- [x] The GitHub history for `known_exploited_vulnerabilities_schema.json` shows
      **exactly one commit**: "Initial data commit", committed 2025-01-27,
      marked **Verified**.

**What this establishes.** Every element of the headline finding was confirmed
against CISA directly, not against this repository. The author's independent
count of 1,703 occurrences agrees with the pipeline. The "one commit, never
amended" claim and the 590 figure derived from it are sound.
Section 4's explanation of why the omission is silent is sound.

**Author's acceptance:** "I accept Section B as passed."

Signature: ______________________  Date: 2026-09-10

## C. Spot-check the timeline by hand — CLOSED

### Defect C1 — found by the author during verification, 2026-09-10

The spot-check instructions carried hand-typed GitHub links built on the branch
name `main`. That repository's default branch is `batman`; `main` does not exist
in it at all, so every link returned 404 and Check 1 could not be started. The
author found this on the first attempt.

Two things were wrong, not one. The branch name was incorrect, and a branch name
should not have been used at all: a branch moves, so even a correct branch link
would eventually show a different file than the one this build read.

**Corrected.** Links are no longer written by hand. `code/09_snapshot_links.py`
generates `docs/SNAPSHOT_LINKS.md` from the pinned commit in
`data/raw/source_pins.json` and the events in
`data/processed/schema_timeline.csv`, addressing every snapshot by its immutable
commit SHA. Running it with `--verify` confirms each snapshot twice — the object
exists in the pinned commit, and a live fetch returns HTTP 200 — using a
deliberately invalid date as a control to prove a 404 is detectable. All 12
snapshots verified before these instructions were presented.

The generator also found more checks than the hand-written list had: it includes
the `notes` removal and restoration pairs, which the manual version omitted.

Two further branch-based URLs were corrected at the same time: the schema
provenance URL in `code/01_fetch.py` is now pinned to the commit, and Section B
records the immutable equivalent of the branch URL the author visited.

**QA Q12 (link hygiene)** now fails the build if any reader-facing document
contains a GitHub URL whose reference is not a 40-character commit SHA, if
`docs/SNAPSHOT_LINKS.md` has been hand-edited, or if a `main` branch path
reappears. Its first run caught three false positives in the check itself
(an off-by-one in the raw-URL parser, source-code URL templates read as links,
and a generator whose output was unstable between verify and non-verify runs);
all three were fixed before the check was trusted.

### Section C — CLOSED, 2026-09-10

All 8 checks passed, each performed personally by the author against snapshots
pinned to commit `3e428ceaa1e18ce466db17c8b4c23f5a23e53c92`.

**Author-verified across the section:** the header content of 13 snapshots — the
12 boundary dates behind all 6 schema-evolution events, plus one ordinary day
chosen freely by the author. Every date in the reconstructed timeline has now
been confirmed by the author against the primary files, and the derived presence
matrix has been confirmed to agree with a snapshot on a day the build did not
nominate.

**Explicitly NOT covered by the author's sign-off, and recorded as
machine-verified throughout:** all record counts (including the 296/309, 683/703
and 1,302 figures), the observation that `notes` returned unpopulated, the
independent JSON archive's corroboration of the 2023 and 2024 events, the
reconciliation of the single three-source disagreement on 2026-09-01, the
multi-valued structure of `cwes`, and every `header_style` label. The author
read the primary CSV archive in every check.

**Defect found and fixed during this section:** C1, the branch-based snapshot
links (recorded above). One documentation defect, no data defects.

Author's acceptance: recorded per check above; Section C closed on the eighth.

Signature: ______________________  Date: 2026-09-10

### The checks

Follow `docs/SNAPSHOT_LINKS.md`. Every link there is pinned and verified.

- [x] **Check 1 — 2021-11-12, first snapshot: PASS.** Checked personally by the
      author on 2026-09-10, against the pinned snapshot
      `github.com/hrbrmstr/cisa-known-exploited-vulns/blob/3e428ceaa1e18ce466db17c8b4c23f5a23e53c92/docs/2021-11-12-cisa-kev.csv`
      Author's observation: "I opened the pinned 2021-11-12 snapshot. Its first
      row uses human-readable column headings beginning with 'CVE,
      Vendor/Project, Product, Vulnerability Name.'"
      Confirms the launch-state claim in report Section 3, and establishes the
      baseline against which the 2021-12-01 naming/canonicalization event is
      measured. The author's reading also matches the four leading columns of
      the harmonisation map in code/02_build.py (CVE, Vendor/Project, Product,
      Vulnerability Name -> cveID, vendorProject, product, vulnerabilityName).
- [x] **Check 2 — 2021-12-01, naming/canonicalization event: PASS.** Checked
      personally by the author on 2026-09-10, against the pinned snapshot
      `.../blob/3e428ceaa1e18ce466db17c8b4c23f5a23e53c92/docs/2021-12-01-cisa-kev.csv`
      Author's observation: "Its first row begins 'cveID, vendorProject,
      product, vulnerabilityName, dateAdded,' confirming that the earlier
      human-readable headings had been renamed by this date."
      Taken with Check 1, this confirms both sides of the rename boundary from
      the primary files: labels on 2021-11-12, camelCase on 2021-12-01. It
      establishes the one naming/canonicalization event in the count of six,
      and validates the harmonisation in code/02_build.py that keeps field
      presence comparable across the rename rather than reporting nine
      simultaneous removals and nine additions.
- [x] **Check 3 — 2021-12-11 / 2021-12-10, `notes` removed: PASS, with an
      explicit scope qualification.** Checked personally by the author on
      2026-09-10 against both pinned snapshots.
      Author's observation: "2021-12-10: the header ends with `dueDate,notes`.
      2021-12-11: the header ends with `dueDate`, and `notes` is absent."

      **What the author verified personally:** the header content of both
      snapshots, i.e. that `notes` is present on 2021-12-10 and absent on
      2021-12-11. This is the field-presence transition itself, and it is the
      claim Check 3 exists to test.

      **What the author did NOT verify personally:** the record counts of 296
      and 309, and therefore the 13 new entries on the transition day. Those
      figures remain supported only by the automated pipeline and the two
      clean-room reproducibility runs (Section A). They are machine-verified,
      not author-verified, and the distinction is preserved here deliberately.

      **Consequence for the V1 ruling.** V1 attributes the disappearance to the
      catalog rather than to an archiver fault, and rests on three strands:
      (a) the header change, (b) new entries arriving on both boundary days,
      (c) the field returning unpopulated in 2022. Strand (a) is now
      author-verified. Strands (b) and (c) remain machine-verified. The ruling
      is unchanged and the report's wording already cites the evidence rather
      than asserting the conclusion, but the provenance of each strand is now
      recorded separately rather than merged into a single "verified".

      **Counting caveat, raised by the author and adopted.** A browser text
      search for "CVE-" must NOT be used as a row count: the string occurs in
      `shortDescription` and `notes` text as well as in the `cveID` column. Nor
      is a rendered line count reliable, since a quoted CSV field may contain
      embedded newlines. Record counts in this project come from parsing the
      CSV with a proper reader (`code/02_build.py`), which is why they are
      reported as machine-verified.
- [x] **Check 4 — 2022-05-24 / 2022-05-23, `notes` restored: PASS, same scope
      qualification as Check 3.** Checked personally by the author on
      2026-09-10 against both pinned snapshots.
      Author's observation: "2022-05-23: the header ends with `dueDate`, and
      `notes` is absent. 2022-05-24: the header ends with `dueDate,notes`,
      confirming that `notes` returned on that date."

      **Author-verified:** the header content of both snapshots — the closing
      half of the round trip, and with Check 3 the fact that `notes` is the only
      field in the catalog's history withdrawn and then reinstated.

      **NOT author-verified, machine-verified only:** the record counts (683 and
      703), the 20 new entries on the transition day, and the observation that
      the field returned unpopulated (0 of 703 records carried a value).

      **Effect on the 164-day figure.** Checks 3 and 4 together fix both ends of
      the gap from the primary files: last day present 2021-12-10, first day
      absent 2021-12-11, last day absent 2022-05-23, first day present again
      2022-05-24. The span between those author-verified boundaries is
      author-verified. The count of 164 *observed snapshot days* within it
      depends on the archive being complete across that window, which is
      machine-verified from the snapshot inventory, not counted by hand.

      **Effect on the V1 ruling, final position.** Of the three evidential
      strands behind V1 — (a) the header changes, (b) new entries on both
      boundary days, (c) the field returning unpopulated — strand (a) is now
      author-verified at all four boundary dates. Strands (b) and (c) remain
      machine-verified. The report cites the evidence rather than asserting the
      conclusion, so no wording change is required; the provenance of each
      strand is recorded here rather than blurred.
- [x] **Check 5 — 2023-10-12 / 2023-10-11, `knownRansomwareCampaignUse` added:
      PASS.** Checked personally by the author on 2026-09-10 against both pinned
      snapshots.
      Author's observation: "2023-10-11: the header ends with `dueDate,notes`,
      and `knownRansomwareCampaignUse` is absent. 2023-10-12: it is present
      between `dueDate` and `notes`."

      **Author-verified:** the header content of both snapshots — the absence on
      2023-10-11 and the presence on 2023-10-12, including the field's position
      in the column order.

      **Machine-verified, recorded separately:** the independent JSON archive
      also covers both dates, and the crosswalk records two sources in agreement
      on each. That corroboration comes from the pipeline
      (`data/processed/crosswalk.csv`), not from the author, and is not covered
      by the author's sign-off above. The author read the primary CSV archive
      only.

      **Evidential position of this event.** Three lines of evidence now bear on
      it, of two different kinds: the author's own reading of the primary CSV
      snapshots (author-verified), and the agreement of the primary CSV archive
      with an independently collected JSON series (machine-verified). This is
      the first event in the timeline to carry both kinds. Unlike Checks 1-4 it
      does not sit in the pre-corroboration window described in LIMITATIONS
      item 4.
- [x] **Check 6 — 2024-06-26 / 2024-06-25, `cwes` added: PASS.** Checked
      personally by the author on 2026-09-10 against both pinned snapshots.
      Author's observation: "2024-06-25: the header ends with
      `knownRansomwareCampaignUse,notes`, and `cwes` is absent. 2024-06-26: the
      header ends with `knownRansomwareCampaignUse,notes,cwes`, confirming that
      `cwes` appeared on that date."

      **Author-verified:** the header content of both snapshots — absence on
      2024-06-25, presence on 2024-06-26, and the field's position as the final
      column.

      **Machine-verified, recorded separately:** the independent JSON archive
      covers both dates and agrees, per `data/processed/crosswalk.csv`. The
      author read the primary CSV archive only; this corroboration is not
      covered by the sign-off above.

      **Also machine-verified, not author-verified:** that `cwes` is the
      catalog's only multi-valued field — an array in the JSON, flattened into
      one CSV cell. The author confirmed the column's presence and position, not
      its internal structure. That structural claim underpins LIMITATIONS item 5
      (CSV recovers field presence but not field structure before the JSON
      mirror begins) and rests on the pipeline's parse of the JSON sources.
- [x] **Check 7 — 2026-09-01 / 2026-08-31, `forensicTriage` added: PASS.**
      Checked personally by the author on 2026-09-10 against both pinned
      snapshots. This is the date the report's supporting finding rests on.
      Author's observation: "2026-08-31: the header ends with
      `knownRansomwareCampaignUse,notes,cwes`, and `forensicTriage` is absent.
      2026-09-01: `forensicTriage` is present between
      `knownRansomwareCampaignUse` and `notes`."

      **Author-verified:** the header content of both snapshots in the primary
      CSV archive — absence on 2026-08-31, presence on 2026-09-01, and the
      field's position in the column order. Taken with Section B, where the
      author confirmed the field on the live catalog at CISA directly, the date
      of first appearance and the current presence of the field are both
      author-verified, from two different sources.

      **Machine-verified, recorded separately; the author explicitly did NOT
      verify this:** the reconciliation of the three-source disagreement on
      2026-09-01. That date is the only one of 1,115 multi-source days where the
      three sources do not agree: the independent JSON archive shows no
      `forensicTriage`, having captured catalogVersion 2026.08.31 because it
      fetched before CISA published that day. Keyed on catalogVersion rather
      than capture date, all three sources agree. This reconciliation comes from
      the pipeline and is documented in QA check Q3b; it is not covered by the
      author's sign-off. The author read the primary CSV archive only, which is
      one of the two sources showing the field present.

      **Effect on the report.** The first-appearance date underpinning Section 4
      is now confirmed by the author against the primary archive, and the
      field's presence in the live catalog was confirmed by the author against
      CISA in Section B. The 590-day schema-staleness figure and the three-way
      reconciliation remain machine-verified.
- [x] **Check 8 — author-selected date, matched against the presence matrix:
      PASS.** Date chosen independently by the author: **2025-03-15**. Checked
      personally on 2026-09-10.
      Author's observation: "The snapshot header contains cveID, vendorProject,
      product, vulnerabilityName, dateAdded, shortDescription, requiredAction,
      dueDate, knownRansomwareCampaignUse, notes and cwes. In
      field_presence_matrix.csv, the 2025-03-15 row marks all those fields as 1
      and marks forensicTriage as 0. I personally compared the snapshot header
      with the matrix row and confirmed that they match."

      **Author-verified:** that the derived presence matrix agrees with the
      primary snapshot on an ordinary, non-boundary day selected by the author
      rather than nominated by the build.

      **NOT author-verified, machine-verified only:** the `n_records` value of
      1,302 and the `header_style` label `bare+camelCase`.

      **Why this check carries weight the others do not.** Checks 1-7 all tested
      dates the pipeline itself nominated, every one a boundary where something
      changed. A reconstruction could in principle be correct at every boundary
      and wrong on the days between. This check samples one of the 1,746
      unexamined days, chosen by the author from a range the build did not
      constrain, and the matrix agreed. The date also falls inside the
      corroborated window (two sources cover it, in agreement), though the
      author read the primary archive only.

## D. Rule on the judgment calls — CLOSED

**STATUS: ALL FIVE RULED by the author, 2026-09-10.** V1 Option B (balanced
wording); V2 Option B conditional on V3; V3 Option B (third source retained with
independence and licensing limitations stated); V4 Option B (CC BY 4.0 with a
rights statement); V5 Option A (restructured so the reconstruction leads). Each
ruling and its application is recorded in full below.

Any text previously recorded here as an author ruling was entered in error and
has been removed. Nothing in this section may be filled in on the author's
behalf. Each ruling must be typed by the author personally.

These cannot be settled by the data. They need your decision, and the report
states whatever you decide.

- [x] **V1 — the `notes` round trip.** RULED BY THE AUTHOR, 2026-09-10.
      Decision: Option B, the balanced wording.
      In the author's words: "The evidence supports treating the disappearance
      and restoration of the notes field as changes attributable to the
      published catalog, while the report must clearly disclose that no
      independent source covers this period."
      Applied: report Section 3 states the attribution, gives the supporting
      evidence (new entries on both boundary days; field returned unpopulated),
      and points to Limitation 4 for the single-source disclosure. Supporting
      figures are interpolated from stats.json, not typed.
      Date: 2026-09-10  Signature: ______________
- [x] **V2 — the 2024-11-26/27 failures.** RULED BY THE AUTHOR, 2026-09-10.
      Decision: Option B, the balanced wording, CONDITIONAL on retaining and
      validating the independent third source in V3.
      In the author's words: "Keep the language factual. State that the saved
      files were Akamai Access Denied responses and explain the timestamps and
      adjacent-day evidence. Do not characterize the events as a CISA outage,
      bot detection, rate limiting, or a general recurring infrastructure
      problem because the evidence does not establish those causes. If the
      third source is not approved in V3, remove the independent-confirmation
      sentence from the V2 passage."
      Applied: report Section 5 states the service, the decoded refusal times,
      the adjacent-day comparison, and the independent confirmation. It states
      explicitly that the responses do not record WHY the requests were refused
      and that no cause is inferred. The earlier phrase "a refusal of automated
      collection" was removed as an unsupported causal implication.
      CONDITIONALITY ENFORCED IN CODE, NOT BY NOTE: code/05_document.py builds
      the Section 5 paragraph, the Corroborating-source-2 section and the
      cross-validation section only when the third source is present in the
      build. Verified by simulating a rejected V3: the report regenerates
      cleanly with every third-source claim removed and no crash. A bug found
      by that test (crash on missing indep_commit) was fixed.
      All values in the passage are parsed from the captured pages by
      code/02_build.py, not typed.
      Date: 2026-09-10  Signature: ______________
- [x] **V3 — pre-corroboration single-source reliance.** RULED BY THE AUTHOR,
      2026-09-10. Decision: Option B. Retain the third source with the
      independence and licensing limitations stated plainly.
      Author's six required disclosures, all applied and verified present:
        1. repository and URL identified (report S2, README, manifest)
        2. JSON archive date range stated (2023-08-18 to 2026-09-10)
        3. CSV exclusion explained with evidence
        4. absence of a licence file disclosed (report S2, LIMITATIONS 12)
        5. public-domain use for verification, no redistribution, stated
        6. access date recorded and per-date hashes preserved in
           data/raw/third_source_csv_identity.csv and
           data/raw/third_source_manifest.json
      REFINEMENT THE AUTHOR SHOULD NOTE: disclosure 3 as worded said the CSVs
      were excluded because they are copies. Hashing all 1,753 shared dates
      showed that is true for the 668 dates before 2023-09-12 (byte-identical,
      back-filled) but NOT after: 163 later dates differ, and those appear to
      be the repository's own collection. The report therefore gives BOTH
      reasons for excluding the CSV tree in full -- copies before 2023-09-12,
      and duplication of a collector already represented by its JSON after --
      rather than the single reason as worded. This was done to avoid asserting
      something the evidence does not support, consistent with the V2 ruling.
      The author should confirm this refinement is acceptable.
      Date: 2026-09-10  Signature: ______________
- [x] **V4 — derived-data licence.** RULED BY THE AUTHOR, 2026-09-10.
      Decision: Option B, CC BY 4.0 for the derived tables.
      Author's required framing, all applied:
        - CC BY 4.0 applies ONLY to the author's original selection,
          arrangement, reconstruction, annotations and documentation, to the
          extent those elements are legally protectable; where no such rights
          subsist, none are asserted.
        - It does not restrict the underlying CISA data, which remains
          CC0/public-domain, nor any third-party content. Facts about the
          catalog are not owned by this project.
        - No claim that CC BY guarantees discoverable evidence of uptake. The
          text states only that attribution is required of anyone relying on
          rights the licence covers, and that the licence is a condition of
          reuse rather than a detection mechanism. Earlier language about a
          "traceable record of reuse" was removed from BUILD_SPEC and README.
        - Irrevocability of CC0 stated.
      NOTE THE AUTHOR SHOULD CONFIRM: the ruling referred to "the earlier CC0
      release". No CC0 release ever occurred -- this project has never been
      published under any licence, and the CC0 designation existed only inside
      this unreleased draft. Writing it as a past release would have recorded
      something untrue, so LICENSE-DATA states the principle conditionally:
      "Had material in fact been released under CC0, that release would have
      remained available under CC0, which is irrevocable and cannot be
      retroactively withdrawn."
      Applied in: LICENSE-DATA (full rights statement), README (condensed),
      report Data Availability section, docs/BUILD_SPEC.md.
      Date: 2026-09-10  Signature: ______________
- [x] **V5 — publishing a time-sensitive finding.** RULED BY THE AUTHOR,
      2026-09-10. Decision: Option A. Restructure so the durable three-source
      reconstruction is the primary contribution and the forensicTriage
      schema-documentation gap is a significant but time-sensitive supporting
      finding.
      Applied:
        - Title: "Schema Evolution in the CISA Known Exploited Vulnerabilities
          Catalog, 2021-2026: A Three-Source Reconstruction". Propagated to the
          report, README and CITATION.cff.
        - Abstract rewritten reconstruction-first; new Executive summary labels
          the primary contribution and the supporting finding explicitly.
        - Headings: S3 "Primary contribution: the reconstructed schema
          timeline"; S4 "Supporting finding: a schema-documentation gap, as of
          <data cutoff>". New S7 Conclusion leads with the reconstruction.
        - The published schema is nowhere described as wrong or incorrect. The
          words "wrong", "defect" and "outgrown" were removed from the report,
          BUILD_SPEC and PUBLISH_GUIDE.
        - Data cutoff and access date are stated wherever forensicTriage is
          discussed, and S4 states that a later CISA update would close the gap
          without falsifying the dated observation.
      Date: 2026-09-10  Signature: ______________

**V4 clarification, ruled by the author 2026-09-10:** the hypothetical paragraph
about what would have happened had the material been released under CC0 was
removed from LICENSE-DATA. No CC0 release occurred and the licence file does not
discuss an unpublished draft licence. Only the accurate current rights and
licensing statement remains.

## E. Read the prose as your own — CLOSED

**Completed by the author on 2026-09-10**, on the corrected six-page report
(`report/kev_schema_evolution.pdf`, SHA-256 `08309df209bf5cec…`, 6 pages).

- [x] Read the report end to end.
- [x] Every claim is one the author would defend.
- [x] The "validates cleanly" / "is not described" distinction is stated
      correctly throughout.
- [x] The AI-assistance paragraph is accurate as written.
- [x] The voice is the author's.

**Author's acceptance, in the author's words:**

> "I reviewed the corrected six-page report and understand its central claims,
> evidence, limitations, licensing, and AI-assistance disclosure. The
> reconstruction of six schema-evolution events is the primary contribution. The
> `forensicTriage` schema-documentation gap is a supporting, date-specific
> finding — not a claim that the catalog fails validation. The report accurately
> reflects my verification work and involvement. I accept responsibility for the
> content."

Signature: ______________________  Date: 2026-09-10

### Corrections required by the author before acceptance

The first reading did NOT pass. The author returned ten corrections, all
applied and rebuilt before acceptance:

  E1  Abstract and Executive summary described both corroborating sources as
      independently collected archives. One is CISA's official Git mirror.
      Reworded to name them. Also corrected in README, CITATION.cff and the
      release notes, where the same inaccuracy appeared.
  E2  Section 3 said eight fields were present at launch. Nine logical fields
      were present including `notes`; eight core fields are present on every
      usable snapshot day. Distinction now stated.
  E3  Timeline table showed the 2022-05-24 `notes` event as "field added". Now
      renders "field restored", derived in 04_figures.py by the same rule used
      in the release notes and snapshot links.
  E4  The `forensicTriage` corroboration sentence claimed all sources dated the
      field to the same capture day. They do not: the second independent
      archive captured the previous catalog version that day. Rewritten to say
      the sources agree on the catalog VERSION, reconciled by `catalogVersion`,
      not on a capture day.
  E5  Section 6 said "any of the five events". Now "any of the 5 field-presence
      transitions or for the 1 naming/canonicalization event".
  E6  Conclusion said "5 dated change events". Now "6 schema-evolution events —
      5 field-presence transitions and 1 naming/canonicalization event".
  E7  "That history is settled" replaced with "That reconstruction is
      reproducible and explicitly bounded by the available archival coverage".
  E8  Section 8 said "clone both sources" and "Because both sources are
      pinned". Corrected to three, with the dependency lock and
      docs/ENVIRONMENT.md referenced.
  E9  AI-assistance paragraph rewritten to the author's wording. The previous
      text claimed the author made every analytic decision; AI made numerous
      methodological and implementation decisions during the build, so that
      claim was withdrawn as inaccurate.
  E10 Page-7 reproduction code block overflowed the left margin. Block
      rewritten to fit and a wrapping stylesheet added to build_pdf.sh as a
      safety net.

**Additional defect found while applying E6.** The Abstract still read
"identifies 5 field-level change events": an earlier edit had silently failed to
match its target and was never verified. The Abstract now carries the full
6 / 5 / 1 breakdown. Every edit in the correction pass used an assertion so a
non-match fails loudly.

**Delivery defect, no content impact.** The corrected PDF sent alongside the
archive arrived in the author's client as `kev_schema_evolution(1).pdf` — the
client disambiguating against an earlier file of the same name — and the author
opened the superseded copy. The three copies (repo, outputs, archive) were
verified byte-identical at SHA-256 `08309df209bf5cec…`, and the file was resent
under a distinct name. No content was affected.

## F. Release mechanics

- [x] GitHub username supplied by the author and written into `metadata.json`,
      `CITATION.cff`, `README.md` and `docs/PUBLISH_GUIDE.md`. No
      `[GITHUB_USERNAME]` placeholder remains; QA Q9/Q10 would fail if one did.
      (This line previously read "Replace `[GITHUB_USERNAME]` everywhere". A
      global substitution of the placeholder rewrote the instruction itself, so
      it came to read "Replace `TosinClement` everywhere" — telling the author
      to replace their own username. Found on review of the closed sections and
      corrected here; nothing outside this checklist was affected.)
- [x] **Option B implemented** (author ruling, this session). Draft/final mode,
      the DOI and the release date now live in one canonical release state —
      the `release` block in `metadata.json`, read only by
      `code/release_state.py`. Every artifact that mentions any of them is
      generated from it. Implemented, negative-tested and re-verified while the
      project remained in draft mode; nothing was published.
- [x] Create the GitHub repository (empty). *Publish guide, step 1.*
      **Done by the author, 2026-09-11.** `https://github.com/TosinClement/kev-schema-evolution`
      — public, empty, showing GitHub's Quick setup screen. Author-verified: no
      README, `.gitignore`, licence, files, commits or releases were added, so
      the first push will not have to merge past an initial commit and no
      licence from GitHub's picker sits alongside the three this project ships.
      The URL matches the `repository` field in `metadata.json`, which is what
      `CITATION.cff`, the README and the Zenodo related identifier derive from.
- [x] Reserve the Zenodo DOI on a draft deposit — do not delete that draft.
      *Publish guide, step 2.* The GitHub integration cannot pre-reserve a DOI;
      this is why the manual-upload path is used.
      **Done by the author, 2026-09-11.** Reserved DOI
      `10.5281/zenodo.22699424`; publication date 2026-09-11. Author-verified:
      the deposit is saved as an unpublished draft, resource type Dataset, the
      canonical title entered, creator Clement, Tosin with ORCID
      0009-0001-2055-5113 and affiliation Independent Researcher, licence
      CC BY 4.0, no files uploaded, and the expected Files validation error
      showing because the upload is intentionally empty at this stage.
- [x] Set `release.mode`, `release.doi` and `release.release_date` in
      `metadata.json`, then `bash code/run_all.sh --final`. This is the single
      step that drops the DRAFT stamps, switches the README banner to released,
      puts the DOI on the report's first page, writes `doi` and `date-released`
      into `CITATION.cff` and regenerates the CISA issue text.
      **There is nothing to edit by hand.** *Publish guide, step 3.*
      **Done 2026-09-11 at the author's direction**, under the pinned
      environment. Twelve QA gates pass, publish gate prints `gate: clear`.
      Delivered for author review; nothing pushed, uploaded, published or
      filed. **Accepted by the author, 2026-09-11**, after an independent
      inspection confirmed: 6-page PDF rendering cleanly with both figures
      visible, no DRAFT marking remaining, DOI 10.5281/zenodo.22699424 on
      page 1, release date 2026-09-11, the author's Section B verification date
      correctly recorded as 2026-09-10, all twelve QA gates passing and all 57
      archive checksums verifying.
- [x] `python code/06_publish_gate.py .` with the four documented exemptions
      prints `gate: clear`. *Publish guide, step 4.* **Clear, 2026-09-11**, and
      recorded as such by the author. The only remaining findings are warnings
      in `docs/PUBLISH_GUIDE.md`, which is one of the four exempted process
      documents and legitimately contains the words the gate looks for.
- [ ] Push, then create the GitHub release from `docs/RELEASE_NOTES.md`.
      *Publish guide, step 5.*
- [ ] Publish the reserved Zenodo deposit. **Irreversible.**
      *Publish guide, step 6.*
- [ ] Verify the DOI resolves and the badge renders. *Publish guide, step 7.*
- [ ] File the CISA issue by pasting `docs/CISA_ISSUE.md` — after the DOI
      resolves, never before (ruling V5). *Publish guide, step 8.*
- [ ] Evidence log, same day. *Publish guide, step 9.*

### What Option B changed, and the defects it exposed

The author chose Option B over hand-editing the banner, the DOI and the release
date at release time. Implementing it surfaced four defects, three of which
would have reached the permanent public record:

1. **`date-released: "[RELEASE_DATE]"` was invisible to the publish gate.** The
   gate's bracketed-placeholder pattern matches `[DOI]` and `[date]` but not
   `[RELEASE_DATE]`. Verified against the live gate before the change: the
   citation file cleared every automated check with a literal placeholder as
   its release date. `CITATION.cff` now emits `date-released` and `doi` only in
   final mode, from the release state, and emits neither in draft mode rather
   than emitting a placeholder.
2. **`[Zenodo DOI]` in the CISA issue text was invisible for the same reason.**
   The issue text is now generated (`code/10_cisa_issue.py`), with its figures
   from `report/stats.json` and its DOI from the release state.
3. **The DOI badge would have blocked every correct release.** The badge the
   old guide told the author to paste into `README.md` has the literal alt text
   `[DOI]`, which the gate's placeholder pattern matched. The guide's claim
   that the gate command had been "tested against a simulated release state"
   cannot have been true of a state containing the badge. The patterns now
   exclude markdown link and image syntax, and case D1 of the negative tests is
   a correct simulated release that must clear the gate.
4. **A generated file was documented as hand-editable.** The old guide's step 0
   said to remove the README STATUS banner by hand; `README.md` is generated,
   so the edit would have been reverted by the next run and failed QA gate Q11.
   The banner is generated in both modes and there is nothing to edit.

New guard rails, each negative-tested in
`code/tests/negative_release_tests.py` (29/29 passing):

- a final build **refuses to run** if the DOI or release date is unset,
  malformed or placeholder-shaped;
- `--final` is an assertion, not a switch: it cannot put the build into final
  mode, only confirm that the canonical state already says so;
- QA gate **Q13** checks that the README banner, the report's identity line,
  `CITATION.cff` and the generated issue text all still agree with the release
  state, and that a draft build contains **no DOI at all** — real, reserved or
  example;
- the publish gate refuses a draft release state, a DOI in a draft build, a
  DRAFT README status, and any DOI, version or release date that disagrees
  across files.

The draft PDF displays no DOI of any kind. The DOI appears on the report's
first page only in final mode.

### Correction: the CSV-exclusion language (author-reported, 2026-09-11)

The author inspected the Option B archive, confirmed its 57 checksums and its
PDF, and found a factual defect the whole Option B review had passed over. The
generated QA report said, under Q3:

> **superseded wording** — its csv/ files are byte-identical to hrbrmstr's
> (back-filled from them)

That is an unconditional claim and it is false. It contradicted
`data/raw/third_source_manifest.json`, `report/stats.json`, the report, the
README, `docs/LIMITATIONS.md` and author ruling V3, all of which already carried
the two-part finding. The accurate statement, and the one now generated
everywhere:

* all 668 shared dates before 2023-09-12 are byte-identical and appear
  back-filled;
* 163 later shared-date CSV files differ;
* those later files are excluded anyway, because the repository's
  independently collected JSON already represents that collector, and using
  both formats would count one collector twice.

Searching the whole project for the same unconditional claim found it in three
more places, two of them published artifacts rather than comments:

1. `code/03_qa.py` — the Q3 note, the defect the author reported. The wording
   is now built from the manifest's own figures.
2. `code/01_fetch.py` — the `role` description for the third source, which is
   written verbatim into `data/raw/source_pins.json` and appended to
   `data/raw/PROVENANCE.txt` on every run. This one was published twice over.
   It carries no hard-coded counts, because it is written before the comparison
   runs; it now states the scope and points at the derived record.
3. `code/02_build.py` — the docstring of `build_indep_track()`, the function
   that actually implements the exclusion.

`docs/LIMITATIONS.md` item 4 was also tightened: it said "pre-2023 CSV files",
which is close but not the derived boundary, and it gave only the first of the
two reasons. Both now come from the manifest.

`data/raw/PROVENANCE.txt` is an append-only ledger and its earlier lines carry
the superseded wording. They are left in place, with a dated `# CORRECTION`
marker appended recording what was wrong, what the derived finding is, and that
lines after the marker carry the corrected text. Rewriting a provenance ledger
to hide an error would be worse than the error.

**New gate: QA Q14, CSV-exclusion language integrity.** Every claim in the
project that the third source's CSVs are byte-identical must now be scoped —
the sentence has to say the identity holds *before* some boundary — and must
carry a derived reference: one of the figures in
`data/raw/third_source_manifest.json`, one of its field names, or a pointer to
that file. Any calendar date inside such a
sentence must equal the derived boundary. Comments and source strings are
scanned, not just documents, because two of the four defects were in code.

Negative-tested as cases G1-G6 in `code/tests/negative_release_tests.py`
(35/35 passing): an unconditional claim is rejected; a scoped claim with no
derived reference is rejected; a claim naming the wrong boundary date is
rejected; the original defect reintroduced into a source comment is caught; and
the gate goes clear again when each is reverted. Writing those tests exposed a
further subtlety worth recording: the first version of the wrong-date fixture
omitted the word CSV and passed, because the gate deliberately inspects only
claims about the third source's csv/ tree rather than every use of that
phrase in the project. The fixture was corrected, not the gate.

Re-verified after the change: full pipeline re-run, all twelve QA gates pass,
35/35 negative tests, clean room D, and a regenerated checksum manifest. The
project remained in draft mode throughout; nothing was published.

**Accepted by the author, 2026-09-11.** Quoting the author's record:

> The corrected Option B implementation and Clean Room D build pass my review.
> The PDF matches the PDF inside the archive, all 57 checksum entries verify,
> the revised Q3 wording accurately distinguishes the 668 earlier identical
> files from the 163 later differing files, and Q14 passes. I accept the
> decision to preserve the earlier provenance entries with an explicit dated
> correction rather than rewriting the append-only record.

Author-verified: the delivered PDF matches the archive copy, the 57 checksums
verify, the corrected Q3 wording is accurate, and the append-only handling of
`data/raw/PROVENANCE.txt` is accepted. Machine-verified: the twelve QA gates,
the 35 negative tests, clean room D and its comparison. This closes the
technical re-verification. Section F's release actions remain open and the
project stays in draft mode until the author directs each one.

### Defect found during the final build: an author's date derived from a build date

`docs/LIMITATIONS.md` item 10 records that the author personally fetched the
canonical CISA URLs and checked them against the mirror. That sentence took its
date from `stats.access_date` — the date the *build* last fetched its pinned
sources. The two are unrelated: the author performed that check on 2026-09-10
(Section B), while the pipeline was re-run on 2026-09-11 during the CSV-language
correction, at the same pinned commits.

The effect was that item 10 came to say the author had checked the live URLs on
2026-09-11, which is not what happened. **This was already true of the draft the
author accepted**, not introduced by the release: the accepted archive carries
the same sentence with the same wrong date. It is disclosed here rather than
quietly corrected.

The author's verification dates are now a recorded constant,
`author_verification.section_b_live_check_date` in `metadata.json`, and QA gate
Q13 checks both that the constant is present and well-formed and that the
rendered item 10 cites it rather than the build's access date. A pipeline re-run
on any future day can no longer move a date that describes something a person
did.

`sources accessed 2026-09-11` elsewhere in the outputs is correct and stays: the
build did access the pinned sources that day. Only the sentence about the
author's own action was wrong.

## Sign-off

I have personally reproduced the pipeline, checked the findings against the
primary sources, ruled on every judgment call above, and read the report as my
own work.

Name: ______________________  Date: ____________
