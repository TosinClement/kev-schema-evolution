# Publish guide

Everything here is a step **you** perform. Nothing was pushed for you: no
GitHub token and no Zenodo token entered the build session, by your choice. The
repository is complete and ready; these are the twenty minutes that make it
public and citable.

Do not start until `docs/VERIFY_CHECKLIST.md` is fully ticked and signed.

## What changed in this guide, and why

Three instructions in the previous version were wrong, and each would have
caused a visible defect on the permanent record:

1. It told you to **edit `README.md` by hand**. `README.md` is generated from
   `templates/README.md.template`; a hand edit is overwritten by the next
   pipeline run and fails QA gate Q11. The STATUS banner is now generated from
   the canonical release state and there is nothing to edit.
2. It recommended the **Zenodo GitHub integration**, under which the DOI is
   minted only *after* the release is archived — so the DOI cannot be inside
   the files being archived, and the guide then had to tell you to delete and
   re-create the `v0.1.0` release. Zenodo does not support pre-reserving a DOI
   through that integration; it does support it on a manual upload. This guide
   now uses the reserved-DOI manual path, and the delete-and-re-create step is
   gone.
3. It claimed the gate command had been **tested against a simulated release
   state**. It had not been tested against one containing the DOI badge the
   guide itself tells you to add: the badge's alt text is the literal `[DOI]`,
   which the gate's placeholder pattern matched, so the gate would have blocked
   every correct release. Fixed, and covered by
   `code/tests/negative_release_tests.py` case D1.

## The canonical release state

One block in `metadata.json` holds the release facts:

```json
"release": { "mode": "draft", "doi": null, "release_date": null }
```

Everything that mentions any of them is generated from it: the README STATUS
banner and DOI badge, `date-released` and `doi` in `CITATION.cff`, the version
and DOI on the report's first page, the DOI in the CISA issue text, the QA
header, the figure stamps. Nothing is typed by hand, and `--final` no longer
sets the mode — it asserts that this block already says `final`, and fails if
it does not.

Setting `mode` to `"final"` with either value missing or placeholder-shaped
makes the build refuse to run. See `code/release_state.py`.

---

## Step 0 — Pre-flight (5 min)

```bash
cd kev-schema-evolution

# Reproduce from the pinned environment (see docs/ENVIRONMENT.md)
python -m venv venv
venv/bin/pip install -r requirements.lock

# Confirm a clean draft build before touching the release state
bash code/run_all.sh
python code/tests/negative_release_tests.py     # 29/29 expected
```

Read `data/processed/qa_report.txt`. Gate Q13 reports the release state and
must say `release state coherent: YES`.

---

## Step 1 — Create the GitHub repository (2 min)

<https://github.com/new>

- **Name:** `kev-schema-evolution`
- **Description:** `Reconstructing schema change in the CISA KEV catalog, 2021-2026, from 1,758 daily snapshots.`
- **Public.** Do **not** initialise with a README, licence, or `.gitignore` —
  this repository has all three.

Nothing is pushed yet. Only the empty repository name is public at this point.

---

## Step 2 — Reserve the Zenodo DOI (3 min)

Log in at <https://zenodo.org> **using ORCID**, so `0009-0001-2055-5113` is
attached to the record automatically.

1. **New upload.**
2. Under *Digital Object Identifier*, answer **No** to "Do you already have a
   DOI for this upload?" and click **Get a DOI now!**
3. Copy the reserved DOI. It looks like `10.5281/zenodo.1234567`.
4. **Save the draft. Do not delete it** — deleting the draft loses the reserved
   DOI permanently, and Zenodo will not reassign it.

The DOI now exists but does not resolve yet. It begins resolving when the
deposit is published in Step 6.

---

## Step 3 — Set the release state and regenerate everything (3 min)

Edit `metadata.json`, and nothing else:

```json
"release": {
  "mode": "final",
  "doi": "10.5281/zenodo.1234567",
  "release_date": "2026-09-11"
}
```

Then one command regenerates every artifact that mentions any of them:

```bash
bash code/run_all.sh --final
```

`--final` asserts the state; it does not set it. If either value is missing or
placeholder-shaped, the build stops with the reason and writes nothing.

This is the step that removes the DRAFT stamps, switches the README banner to
released, puts the DOI on the report's first page, writes `doi` and
`date-released` into `CITATION.cff`, and regenerates the CISA issue text with
the DOI in it. There is nothing to edit by hand afterwards.

---

## Step 4 — Run the gate (1 min)

```bash
python code/06_publish_gate.py . \
  --allow-draft-in code/ docs/VERIFY_CHECKLIST.md docs/BUILD_SPEC.md docs/PUBLISH_GUIDE.md
```

It must print `gate: clear`. Beyond the draft markers and secrets it always
looked for, it now also refuses:

- a release state still set to draft;
- a DOI or release date that is unset or placeholder-shaped;
- a README STATUS banner that does not match the release state, or still says
  DRAFT;
- a DOI, version or release date in `CITATION.cff`, the report, the release
  notes or the issue text that disagrees with the release state;
- any DOI at all in a draft build.

The `--allow-draft-in` list is not a way around the gate. Those four paths
legitimately contain the words it looks for: the pipeline scripts implement the
release-state logic and so mention DRAFT in their docstrings, and the three
process documents are instructions *about* drafting and placeholders.
Everything the public reads — the report, the README, the figures, the QA
report, the derived data, `CITATION.cff`, the issue text — is scanned with no
exemption.

If it blocks, fix the cause and re-run. Do not work around it.

---

## Step 5 — Push and release on GitHub (5 min)

```bash
git init -b main
git add -A
git commit -m "v0.1.0: $(python3 -c "import json;print(json.load(open('metadata.json'))['title'])")

See docs/RELEASE_NOTES.md for the release summary; every figure in it is
generated from report/stats.json."

git remote add origin https://github.com/TosinClement/kev-schema-evolution.git
git push -u origin main
```

`sources/` is git-ignored, so the upstream clones are not pushed. The pinned
commits in `data/raw/source_pins.json` are what make the build reproducible —
that file **is** committed.

Then **Releases → Draft a new release**:

- Tag `v0.1.0` (create on publish)
- Title: the canonical title, from `metadata.json`
- Notes: **paste the generated block from `docs/RELEASE_NOTES.md`**

> `docs/RELEASE_NOTES.md` is generated by `code/07_release_notes.py` from
> `report/stats.json`, `metadata.json` and `AUTHORS.json`. Do not retype the
> figures here or in the release body — an earlier draft of this guide carried
> a hand-written block whose numbers were three rulings out of date, and it was
> written to be pasted straight onto the permanent public record.
> `code/03_qa.py` fails the build if the generated notes disagree with the
> statistics.

**Publish release**, then download the release `.zip`.

Between this step and the next, the repository is public and states a DOI that
does not resolve yet. That window is expected on this path and closes in Step 6.
Keep it short.

---

## Step 6 — Publish the Zenodo deposit (5 min)

Return to the **draft you reserved in Step 2** — not a new upload, or the
reserved DOI is wasted.

Attach the GitHub release `.zip` and `report/kev_schema_evolution.pdf`, then:

| Field | Value |
|---|---|
| Upload type | Dataset (the report is included as documentation) |
| Title | the canonical title from `metadata.json` |
| Authors | Clement, Tosin — ORCID `0009-0001-2055-5113` — Independent Researcher |
| Description | the generated body of `docs/RELEASE_NOTES.md`, or the report's abstract |
| Version | `0.1.0` |
| Language | English |
| Licence | Creative Commons Attribution 4.0 International |
| Keywords | the `keywords` list in `metadata.json` |
| Related identifiers | `https://github.com/TosinClement/kev-schema-evolution` — *is supplement to* |

Then **Publish**.

> **This is the irreversible point.** A Zenodo record cannot be withdrawn, only
> superseded by a new version. Everything before this can be undone; nothing
> after it can.

---

## Step 7 — Verify (2 min)

- The DOI resolves to the record.
- The record shows the ORCID and the CC BY 4.0 licence.
- The README badge renders on GitHub and links to the record.
- `CITATION.cff` on GitHub shows the DOI in the "Cite this repository" panel.

---

## Step 8 — File the upstream issue — AFTER the DOI resolves

> **Ordering matters, and it was ruled on in verification (V5).** Do not file
> this before Step 6 is complete. Filing it is the single most likely thing to
> prompt CISA to amend the schema, which would close the gap the report
> documents. The dated observation stays accurate either way. Deposit first,
> then report the gap.

The most useful outcome of this work is CISA updating the schema.
`cisagov/kev-data` explicitly accepts issues for "accidental schema violations
and the like".

The issue text is generated: **paste `docs/CISA_ISSUE.md`** into
<https://github.com/cisagov/kev-data/issues/new>. Every figure in it comes from
`report/stats.json` and the DOI from the release state, so it cannot carry a
stale number or a placeholder. Do not retype it.

Filing this makes the report actionable rather than merely observational, and
the issue is public evidence of the contribution.

---

## Step 9 — Evidence log

Append one row per publication event to your evidence log the same day:

```csv
date,artifact,venue,url_or_doi,status,files_saved
2026-XX-XX,KEV schema evolution v0.1.0,GitHub,https://github.com/TosinClement/kev-schema-evolution,released,release zip
2026-XX-XX,KEV schema evolution v0.1.0,Zenodo,<the resolved DOI>,published,PDF + record screenshot
2026-XX-XX,forensicTriage schema issue,cisagov/kev-data,<issue URL>,open,issue screenshot
```

Publications not logged the day they happen are the ones that go missing later.

---

## Later — arXiv (optional, not part of v0.1.0)

If you want the report indexed as a preprint, `cs.CR` is the right category.
Two things to know before you start: arXiv requires **endorsement** for a first
submission in a category, and moderation takes one to several days. The report
is already the right length and shape for a short technical note. This is a
deliberate later step, not a v0.1.0 blocker — get the DOI first.
