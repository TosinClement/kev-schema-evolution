#!/usr/bin/env python3
"""Pre-publication gate: refuse to publish while draft markers or secrets remain.

Scans a project directory for:
  - DRAFT stamps and banners in text-bearing files (md, txt, html, py, js, csv, json, tex, cff)
  - [VERIFY ...] and [ASK ...] tags, and bracketed placeholders like [insert], [DOI], [journal]
  - likely secrets: tokens, private keys, .env files
  - a missing LICENSE, README, or CITATION.cff (warning, not failure)

Exit code 0 means clear to publish; 1 means blocked. The human half of the gate
(the author's own verification) cannot be scripted; this enforces the mechanical half.

Usage:
  python publish_gate.py <project_dir> [--allow-draft-in path/prefix ...]
"""

import argparse
import os
import re
import sys

TEXT_EXT = {".md", ".txt", ".html", ".py", ".js", ".csv", ".json", ".tex", ".cff", ".yml", ".yaml", ".rst", ".bib"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv",
             "sources"}  # sources/ holds the git-ignored upstream clones;
                          # their contents are not part of this release

DRAFT_PATTERNS = [
    (re.compile(r"\bDRAFT\b"), "DRAFT stamp or banner"),
    (re.compile(r"\[VERIFY[^\]]*\]"), "[VERIFY] tag"),
    (re.compile(r"\[ASK[^\]]*\]"), "[ASK] tag"),
    (re.compile(r"\[TARGET\]"), "[TARGET] tag (planning artifact, not publishable)"),
    # The trailing (?!\() keeps markdown link and image syntax out of the
    # placeholder patterns. Found by code/tests/negative_release_tests.py case
    # D1: the released README carries the Zenodo badge
    # `[![DOI](https://zenodo.org/badge/DOI/<doi>.svg)](https://doi.org/<doi>)`,
    # whose alt text is the literal `[DOI]` — which this pattern matched. The
    # gate would therefore have blocked every correct release, and the claim in
    # docs/PUBLISH_GUIDE.md that the command had been tested against a
    # simulated release state was wrong: that test cannot have included the
    # badge the guide itself tells you to add. A placeholder left in prose is
    # not followed by an opening parenthesis; a markdown link always is.
    (re.compile(r"\[(insert|DOI|journal|tracking number|repository URL|n|date|name)[^\]]*\](?!\()", re.I),
     "bracketed placeholder"),
    (re.compile(r"XXXX-XXXX|zenodo\.XXXX+"), "placeholder identifier"),
    # Added after the Option B review. The pattern above matches [DOI] and
    # [date] but did NOT match [RELEASE_DATE] or [Zenodo DOI], both of which
    # were live in this project: CITATION.cff shipped `date-released:
    # "[RELEASE_DATE]"` and the CISA issue text carried `[Zenodo DOI]`. A
    # release could therefore have cleared this gate with a literal
    # placeholder as its citation date. Verified against the gate before the
    # fix; covered by the negative tests in code/tests/.
    (re.compile(r"\[[A-Z][A-Z0-9_]{2,}\](?!\()"),
     "bracketed placeholder (all-caps)"),
    (re.compile(r"\[[^\]]*\bDOI\b[^\]]*\](?!\()"), "bracketed DOI placeholder"),
]
SECRET_PATTERNS = [
    (re.compile(r"ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}"), "GitHub token"),
    (re.compile(r"-----BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY-----"), "private key"),
    (re.compile(r"(?i)(api[_-]?key|secret|token)\s*[=:]\s*['\"][A-Za-z0-9_\-]{16,}['\"]"), "hardcoded credential"),
]
REQUIRED = ["README.md", "LICENSE"]
RECOMMENDED = ["CITATION.cff", ".gitignore"]


def scan(root, allow_prefixes):
    blockers, warnings = [], []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            path = os.path.join(dirpath, fn)
            rel = os.path.relpath(path, root)
            if fn == ".env" or fn.endswith(".pem"):
                blockers.append((rel, "secrets file present"))
                continue
            if os.path.splitext(fn)[1].lower() not in TEXT_EXT:
                continue
            try:
                with open(path, encoding="utf-8", errors="ignore") as f:
                    text = f.read()
            except OSError:
                continue
            for pat, label in SECRET_PATTERNS:
                if pat.search(text):
                    blockers.append((rel, label))
            allowed = any(rel.startswith(p) for p in allow_prefixes)
            for pat, label in DRAFT_PATTERNS:
                m = pat.search(text)
                if m:
                    line = text.count("\n", 0, m.start()) + 1
                    (warnings if allowed else blockers).append((f"{rel}:{line}", label))
    for req in REQUIRED:
        if not os.path.exists(os.path.join(root, req)):
            blockers.append((req, "required file missing"))
    for rec in RECOMMENDED:
        if not os.path.exists(os.path.join(root, rec)):
            warnings.append((rec, "recommended file missing"))
    return blockers, warnings


# --------------------------------------------------------------------------
# Project release-state checks (author ruling: Option B, Section F).
#
# The scan above is generic: it looks for markers that should not survive to
# release. These checks are specific to this project's canonical release state
# and answer a different question — not "is a placeholder left behind" but "do
# the generated artifacts still agree with the one place the DOI, the release
# date, the version and the draft/final mode are recorded".
#
# They are skipped silently for any project without a metadata.json release
# block, so the gate remains reusable.
# --------------------------------------------------------------------------

DOI_SHAPED = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+")


def dois_in(text):
    """DOIs mentioned in a text, normalised.

    The DOI suffix grammar allows brackets and dots, so a bare regex swallows
    the markdown punctuation around a link and the `.svg` of a Zenodo badge
    URL, and the same DOI then reads as three different ones. Found by
    code/tests/negative_release_tests.py case D1, which failed on a correct
    simulated release before this normalisation existed."""
    found = set()
    for m in DOI_SHAPED.findall(text):
        d = m.rstrip(".,;:)]}\"'")
        if d.endswith(".svg"):
            d = d[:-4]
        found.add(d)
    return found
RELEASE_SCANNED = ["README.md", "CITATION.cff", "docs/CISA_ISSUE.md",
                   "docs/RELEASE_NOTES.md", "report/kev_schema_evolution.md"]


def release_checks(root):
    """Return (blockers, warnings) for the canonical release state."""
    meta_p = os.path.join(root, "metadata.json")
    if not os.path.exists(meta_p):
        return [], []
    try:
        import json as _json
        if "release" not in _json.load(open(meta_p, encoding="utf-8")):
            return [], []
    except Exception:
        return [], []

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        import release_state
    except ImportError:
        return [("code/release_state.py", "release state module missing")], []

    blockers, warnings = [], []
    try:
        state = release_state.load(root)
    except release_state.ReleaseStateError as exc:
        first = str(exc).strip().splitlines()[0]
        return [("metadata.json", f"release state unusable: {first}")], []

    def read(rel):
        p = os.path.join(root, rel)
        if not os.path.exists(p):
            return None
        with open(p, encoding="utf-8", errors="ignore") as fh:
            return fh.read()

    texts = {rel: read(rel) for rel in RELEASE_SCANNED}
    for rel, txt in texts.items():
        if txt is None:
            blockers.append((rel, "generated release artifact missing"))
    stats_p = os.path.join(root, "report", "stats.json")

    if not state["final"]:
        blockers.append(("metadata.json",
                         "release.mode is 'draft' — this build is not a "
                         "release. Set the canonical release state to final, "
                         "with the reserved DOI and release date, and re-run "
                         "the pipeline"))
        # A draft must contain no DOI at all: not a real one, not a reserved
        # one, not an example. Anything DOI-shaped here is a fake.
        for rel, txt in texts.items():
            found = dois_in(txt) if txt else set()
            if found:
                blockers.append((rel, "DOI present in a draft build "
                                      f"({sorted(found)[0]})"))
        return blockers, warnings

    doi, date, ver = state["doi"], state["release_date"], state["version"]

    if os.path.exists(stats_p):
        import json as _json
        stats = _json.load(open(stats_p, encoding="utf-8"))
        if stats.get("draft") is not False:
            blockers.append(("report/stats.json",
                             "stats.json still marks this build as draft — "
                             "re-run the pipeline after setting the release "
                             "state"))
        expected = release_state.readme_banner(state, stats).rstrip("\n")
        if texts.get("README.md") is not None and expected not in texts["README.md"]:
            blockers.append(("README.md",
                             "STATUS banner does not match the release state "
                             "(regenerate; do not edit README.md by hand — it "
                             "is generated from templates/)"))
        rep = texts.get("report/kev_schema_evolution.md")
        if rep is not None:
            exp_id = release_state.report_identity_line(
                state, stats).split(" · generated")[0]
            if exp_id not in rep:
                blockers.append(("report/kev_schema_evolution.md",
                                 "first-page identity line does not match the "
                                 "release state (version, DOI or dates)"))

    if texts.get("README.md") and "STATUS: DRAFT" in texts["README.md"]:
        blockers.append(("README.md", "README still carries a DRAFT status"))

    cff = texts.get("CITATION.cff")
    if cff is not None:
        for needle, what in ((f'doi: "{doi}"', "DOI"),
                             (f'date-released: "{date}"', "release date"),
                             (f'version: "{ver}"', "version")):
            if needle not in cff:
                blockers.append(("CITATION.cff",
                                 f"{what} missing or does not match the "
                                 f"release state (expected {needle})"))

    for rel in ("report/kev_schema_evolution.md", "docs/CISA_ISSUE.md"):
        if texts.get(rel) is not None and doi not in texts[rel]:
            blockers.append((rel, "release DOI absent"))

    notes = texts.get("docs/RELEASE_NOTES.md")
    if notes is not None and f"v{ver}" not in notes:
        blockers.append(("docs/RELEASE_NOTES.md",
                         f"version v{ver} absent — regenerate"))

    stray = sorted({d for txt in texts.values() if txt
                    for d in dois_in(txt) if d != doi})
    for d in stray:
        blockers.append(("(release artifacts)",
                         f"DOI {d} disagrees with the release state ({doi})"))
    return blockers, warnings


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project_dir")
    ap.add_argument("--allow-draft-in", nargs="*", default=[],
                    help="relative path prefixes where draft markers are tolerated (e.g. docs/planning)")
    a = ap.parse_args()
    root = os.path.abspath(a.project_dir)
    blockers, warnings = scan(root, a.allow_draft_in)
    rb, rw = release_checks(root)
    blockers += rb
    warnings += rw
    for rel, label in warnings:
        print(f"warning  {label}: {rel}")
    for rel, label in blockers:
        print(f"BLOCKED  {label}: {rel}")
    if blockers:
        print(f"\n{len(blockers)} blocker(s). Resolve every one, then re-run. "
              "Draft markers come off only after the author has verified the work.")
        sys.exit(1)
    print("gate: clear (mechanical checks passed; the author's own verification is still required)")


if __name__ == "__main__":
    main()
