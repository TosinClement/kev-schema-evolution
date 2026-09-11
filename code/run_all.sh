#!/usr/bin/env bash
# Run the whole pipeline in order.
#
#   bash code/run_all.sh            # mode from the canonical release state
#   bash code/run_all.sh --final    # same, but ASSERT the state says final
#
# Draft/final is not set by this switch. It is read from the `release` block in
# metadata.json (see code/release_state.py), together with the DOI and the
# release date, so there is one source of truth rather than a flag that can be
# forgotten on one stage and passed on another. `--final` asserts that the
# canonical state already says final and fails loudly if it does not.
#
# Use the pinned environment: see docs/ENVIRONMENT.md and requirements.lock.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PY="${PYTHON:-python3}"
FINAL="${1:-}"

$PY code/release_state.py $FINAL   # fail fast if the release state is unusable
$PY code/01_fetch.py
$PY code/02_build.py
$PY code/03_qa.py $FINAL
$PY code/04_figures.py $FINAL
$PY code/00_metadata.py          # CITATION.cff, now that stats exist
$PY code/07_release_notes.py     # docs/RELEASE_NOTES.md, from stats
$PY code/08_render_docs.py       # README.md and docs/LIMITATIONS.md, from stats
$PY code/10_cisa_issue.py         # docs/CISA_ISSUE.md, from stats + release state
$PY code/09_snapshot_links.py     # docs/SNAPSHOT_LINKS.md, pinned to the commit
$PY code/05_document.py $FINAL
bash code/build_pdf.sh
$PY code/03_qa.py $FINAL         # re-run: Q9/Q10 need the PDF and notes present
echo "run_all: complete"
