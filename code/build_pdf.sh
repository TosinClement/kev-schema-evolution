#!/usr/bin/env bash
# Render the report to PDF.
#
# Two defects fixed here, both found by the Section A clean-room test:
#
#  A2a  This script used to hardcode the report title. It now takes it from
#       metadata.json, the canonical source, so it cannot drift.
#
#  A2b  More seriously, it used to fail silently. Passing a title containing an
#       en-dash through `--metadata title=` makes wkhtmltopdf abort with an
#       encoding error, but the script still exited 0 and left the PREVIOUS
#       PDF in place -- so a stale document with a superseded title survived a
#       apparently successful build. The title is now passed to wkhtmltopdf as a
#       document property in an ASCII-safe form via pandoc's `pagetitle`
#       variable -- which sets the HTML <title>, and hence the PDF document
#       title, WITHOUT rendering a second visible heading above the document's
#       own H1 -- and the build verifies afterwards that the PDF was actually
#       rewritten.
#
# Run after code/05_document.py.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/report/kev_schema_evolution.md"
OUT="$ROOT/report/kev_schema_evolution.pdf"

TITLE_ASCII="$(python3 -c "import json;print(json.load(open('$ROOT/metadata.json'))['title_ascii'])")"

# Record the pre-build state so a silent failure cannot pass as success.
BEFORE=""
[ -f "$OUT" ] && BEFORE="$(sha256sum "$OUT" | cut -d' ' -f1)"
rm -f "$OUT"

# Correction 10: long lines inside a code block used to run off the page
# instead of wrapping. Lines are now short enough not to need it, but this
# stylesheet is the safety net so a future long line degrades to a wrap rather
# than to text in the margin.
cat > /tmp/kev_pdf.css <<'CSS'
pre, pre code { white-space: pre-wrap; word-wrap: break-word; overflow-wrap: break-word; }
table { width: 100%; table-layout: fixed; word-wrap: break-word; }
img { max-width: 100%; }
CSS

cd "$ROOT/report"
pandoc kev_schema_evolution.md \
  --css=/tmp/kev_pdf.css \
  -o kev_schema_evolution.pdf \
  --pdf-engine=wkhtmltopdf \
  -V pagetitle="$TITLE_ASCII" \
  -V margin-top=18mm -V margin-bottom=18mm -V margin-left=18mm -V margin-right=18mm \
  2> >(tee /tmp/pandoc_stderr.txt >&2)

# wkhtmltopdf 0.12.6 does not carry the HTML <title> through to the PDF's own
# Title property, so it is set explicitly afterwards with pdftk. Cosmetic, but
# it is what a reference manager reads when the file is imported.
if command -v pdftk >/dev/null 2>&1 && [ -s "$OUT" ]; then
  printf 'InfoBegin\nInfoKey: Title\nInfoValue: %s\n' "$TITLE_ASCII" > /tmp/kev_pdfinfo.txt
  if pdftk "$OUT" update_info /tmp/kev_pdfinfo.txt output "$OUT.tmp" 2>/dev/null; then
    mv "$OUT.tmp" "$OUT"
  else
    rm -f "$OUT.tmp"
    echo "build_pdf: note - could not set the PDF Title property (non-fatal)" >&2
  fi
  rm -f /tmp/kev_pdfinfo.txt
fi

if [ ! -s "$OUT" ]; then
  echo "build_pdf: FAILED - no PDF produced" >&2
  exit 1
fi
AFTER="$(sha256sum "$OUT" | cut -d' ' -f1)"
if [ -n "$BEFORE" ] && [ "$BEFORE" = "$AFTER" ]; then
  echo "build_pdf: FAILED - output unchanged, stale PDF retained" >&2
  exit 1
fi
echo "report/kev_schema_evolution.pdf"
