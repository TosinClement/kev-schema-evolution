# Verification records

Audit trail for the Section A reproducibility evidence in
`docs/VERIFY_CHECKLIST.md`. These files exist so the author's sign-off can be
checked by someone who was not present when the tests ran.

| File | What it is |
|---|---|
| `logs/cleanroom-A.log` | Complete log of the first clean-room run: environment, exact installed package versions, and every line of pipeline output including the full QA report. |
| `logs/cleanroom-B.log` | The same for a second, fully independent run — separate directory, separate virtual environment, separate clones of all three sources. |
| `logs/cleanroom-comparison.log` | File-by-file comparison of the two runs, with SHA-256 for every output that must not vary, and the timestamp-stripped equivalence checks for those that do. |
| `logs/cleanroom-C.log` | Complete log of a third clean-room run, made after the Option B release-state change: fresh venv, fresh clones, the full pipeline, the 29 negative tests, and the publish gate (which correctly refuses a draft). |
| `logs/cleanroom-C-comparison.log` | File-by-file comparison of clean room C against the working tree, produced by `code/tests/compare_cleanroom.py`. Verdict line: no unexplained differences. |
| `logs/negative-release-tests.log` | The 29 negative tests for the release-state gates: each check is made to fail on purpose and must fail for the stated reason. |
| `logs/cleanroom-D.log` | A fourth clean-room run, made after the CSV-exclusion language correction and the addition of QA gate Q14. |
| `logs/cleanroom-D-comparison.log` | Comparison of clean room D against the working tree: 54 files identical, six differing for stated timestamp or append-only reasons, verdict `NO UNEXPLAINED DIFFERENCES`. |
| `SHA256SUMS.txt` | SHA-256 of every release file. Verify with `sha256sum -c verification/SHA256SUMS.txt`. |
| `VOLATILE.txt` | Files expected to differ from the clean-room runs: six that embed a build timestamp, plus `docs/VERIFY_CHECKLIST.md`, which records sign-offs given after the tests. Every other file in the manifest was byte-identical across both runs. |

## What the evidence shows

Runs A and B pass all nine QA gates. Every data table, both figures, the QA report
and all four generated documents are byte-identical between two independent
runs. The six volatile files are identical once their timestamps are removed:
`stats.json` minus `generated_utc`, the report minus its dateline, the PDF text
layer minus its timestamp.

## Clean room C — after the release-state change (2026-09-10)

The author ruled that the README status banner, the DOI, the release date, the
version and the draft/final mode must all come from one canonical release state
rather than being typed in at release time (Option B, `docs/VERIFY_CHECKLIST.md`
Section F). That changed code after Sections A-E had been accepted, so the
evidence was regenerated rather than assumed to carry over.

* `logs/cleanroom-C.log` — the pipeline, the negative tests (29/29) and the
  publish gate, run from the archive in a fresh environment. The gate refuses
  the build, which is the correct result: this is a draft.
* `logs/cleanroom-C-comparison.log` — 52 files byte-identical to the working
  tree. Seven differ, each with a checked explanation: five embed a build
  timestamp, `data/raw/PROVENANCE.txt` is an append-only ledger whose five new
  lines differ only in their timestamps, and `.gitignore` gained `venv/` after
  the archive was built. Verdict: no unexplained differences.
* Both figures are byte-identical to the clean room, which is the regression
  check for defect A1. The first working-tree rebuild after the change was made
  with the system interpreter rather than the pinned one and produced figures
  that differed from the clean room; rebuilding under `requirements.lock`
  restored byte-identity. The pinned environment is not optional.

The draft build contains no DOI of any kind — not in the README, not in
`CITATION.cff`, not in the report, and not in the PDF. `CITATION.cff` omits
`date-released` entirely rather than carrying a placeholder.

## Clean room D — after the CSV-exclusion language correction (2026-09-11)

The author found that the generated QA report still stated, without
qualification, that the third source's CSV files match the primary archive's.
That holds only for the shared dates before the derived boundary; the later
shared dates differ and are excluded for a different reason. The same
unconditional claim was found in the pin description written into
`data/raw/source_pins.json` and appended to `data/raw/PROVENANCE.txt`, and in a
docstring in `code/02_build.py`. All were corrected and tied to the derived
manifest statistics by new QA gate Q14.

* `logs/cleanroom-D.log` — pipeline exit 0, all twelve QA gates pass, 35/35
  negative tests, publish gate correctly refuses (still a draft).
* `logs/cleanroom-D-comparison.log` — 54 files byte-identical; verdict: no
  unexplained differences.

The first run of clean room D did **not** come out clean, and the defect was in
the new gate rather than in the project: Q14 reported 24 claims in the working
tree against 25 in the room. `data/raw/PROVENANCE.txt` is append-only, so each
pipeline run added another copy of the same sentence and the counter rose with
the number of runs — a figure in a published QA report that depended on how
many times the pipeline had been run. Claims are now counted once per distinct
sentence per file, and the second run of clean room D agrees exactly. This is
the kind of drift the clean-room comparison exists to surface, and it is
recorded here rather than quietly fixed.

## What the evidence does not show

These are automated tests run by Claude in a Linux container. They demonstrate
that the pipeline reproduces itself from the pinned sources and pinned
dependencies. They are not an independent replication by a second party, and
they were not run on the author's own machine or operating system. See
`docs/LIMITATIONS.md` item 11.

## Reproducing the check yourself

```bash
tar xzf kev-schema-evolution-v0.1.0-draft.tar.gz -C /tmp/check
cd /tmp/check
python -m venv venv && venv/bin/pip install -r requirements.lock
PYTHON=venv/bin/python bash code/run_all.sh
sha256sum -c verification/SHA256SUMS.txt   # volatile files will differ; see VOLATILE.txt
```

## Note: manifest used in anger, 2026-09-10

Mid-verification the build container was reclaimed and the working directory
lost. The repository was restored from the release archive and checked against
`SHA256SUMS.txt`: all 52 files verified OK, so the restored tree is
bit-identical to the one the clean-room evidence describes and verification
continued without re-running anything. The pinned source clones are not carried
in the archive by design; `code/01_fetch.py` re-creates them from the pinned
commits in about 40 seconds.
