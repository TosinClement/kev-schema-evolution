# Validated build environment

The pipeline was built and reproduced in the environment below. Figures are
byte-reproducible only when the pinned Python dependencies are used; the data
tables reproduce on any reasonable Python 3.10+.

## Python

| | Validated |
|---|---|
| Python | 3.11.15 |
| Platform | Linux x86_64 |
| Dependencies | `requirements.lock` (fully pinned, transitive included) |

Direct dependencies are `matplotlib`, `jsonschema` and `PyYAML`; the lock file
carries the complete resolved set.

```bash
python -m venv venv
venv/bin/pip install -r requirements.lock
```

## System-level tools

These are not Python packages and must be present on the host.

| Tool | Validated version | Used by | Required for |
|---|---|---|---|
| `git` | 2.43.0 | `code/01_fetch.py` | cloning the three pinned sources — **required** |
| `pandoc` | 3.1.3 | `code/build_pdf.sh` | Markdown → HTML → PDF — required for the PDF only |
| `wkhtmltopdf` | 0.12.6 | `code/build_pdf.sh` | PDF rendering engine — required for the PDF only |

If `pandoc` or `wkhtmltopdf` is unavailable, every other stage still runs and
every data output is still produced; only `report/kev_schema_evolution.pdf` is
skipped. The Markdown report is the source of record.

## Figure determinism

`code/04_figures.py` fixes the font family to DejaVu Sans (bundled with
matplotlib, so it does not depend on host fonts), fixes the canvas size via
`figsize × dpi` with constrained layout rather than `bbox_inches="tight"`, and
strips the software and timestamp fields from PNG metadata. With the pinned
matplotlib this makes the figures byte-identical across runs and machines.

## Network

`code/01_fetch.py` clones three public GitHub repositories. No other network
access is required. `www.cisa.gov` is **not** contacted: CISA's own GitHub
mirror is used instead, which is recorded in `docs/LIMITATIONS.md` item 10.
