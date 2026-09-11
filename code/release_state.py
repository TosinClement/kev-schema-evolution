#!/usr/bin/env python3
"""
release_state.py — the canonical release state, and the only reader of it.

Author ruling (Option B, Section F). Before this module existed, four things
that must be correct at release were typed by hand into generated files:

  * the README STATUS banner, hard-coded in templates/README.md.template with
    its own literal version string;
  * `date-released` in CITATION.cff, emitted as the literal `[RELEASE_DATE]`;
  * the DOI, which appeared nowhere until it was pasted in after deposit;
  * the DOI inside the CISA issue text, written as `[Zenodo DOI]`.

Three of those four were invisible to the publish gate: its bracketed
placeholder pattern matches `[DOI]` and `[date]` but not `[RELEASE_DATE]` or
`[Zenodo DOI]`, so a release could clear every automated check with an unset
citation date. That was verified against the live gate before this change.

The fix is the rule the rest of the project already follows: derive, do not
type. `metadata.json` carries one `release` block — mode, doi, release_date —
and every artifact that mentions any of them is generated from it.

    mode "draft"  doi and release_date are null. No DOI appears in any output;
                  the draft PDF must not display a placeholder or a fake one.
    mode "final"  both must be present and well-formed, or the build refuses to
                  run. There is no way to produce a final artifact with a
                  missing or placeholder DOI or date short of editing this file
                  to lie, and the gate cross-checks the generated outputs
                  against it afterwards.

Nothing here mints, reserves or validates a DOI against Zenodo. It checks shape
and internal consistency only.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 10.NNNN/suffix — the DataCite/Crossref shape. Deliberately permissive about
# the suffix and strict about the prefix.
DOI_RE = re.compile(r"^10\.\d{4,9}/[-._;()/:A-Za-z0-9]+$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# Anything that looks like a stand-in rather than a value. Checked on top of
# the shape tests, because `10.5281/zenodo.XXXXXXX` is a well-formed DOI.
PLACEHOLDER_RE = re.compile(
    r"(XXXX|\bTBD\b|\bTODO\b|placeholder|example|\[|\]|"
    r"RELEASE_DATE|ZENODO_ID|NNNN|0000000)", re.I)


class ReleaseStateError(RuntimeError):
    """Raised when the release state is unusable for the requested mode."""


def _placeholder(value: str) -> bool:
    return bool(PLACEHOLDER_RE.search(value))


def load(root: Path = ROOT, *, assert_final: bool = False) -> dict:
    """Read and validate the canonical release state.

    `assert_final` is the meaning of the pipeline's `--final` switch: it no
    longer *sets* the mode (that would be a second source of truth), it asserts
    that the canonical state already says final and fails loudly if not.
    """
    meta = json.loads((Path(root) / "metadata.json").read_text())
    rel = meta.get("release")
    if rel is None:
        raise ReleaseStateError(
            "metadata.json has no `release` block. The canonical release state "
            "is required; see code/release_state.py.")

    mode = rel.get("mode", "draft")
    if mode not in ("draft", "final"):
        raise ReleaseStateError(
            f"release.mode is {mode!r}; expected 'draft' or 'final'.")

    doi = rel.get("doi")
    date = rel.get("release_date")
    version = meta["version"]

    if assert_final and mode != "final":
        raise ReleaseStateError(
            "--final was passed but metadata.json says release.mode is "
            f"{mode!r}. The mode is not set by a command-line switch. Set "
            "release.mode to \"final\" in metadata.json, together with the "
            "reserved DOI and the release date, then re-run.")

    if mode == "final":
        problems = []
        if not doi:
            problems.append("release.doi is not set")
        elif not isinstance(doi, str) or not DOI_RE.match(doi):
            problems.append(f"release.doi {doi!r} is not a well-formed DOI "
                            "(expected 10.NNNN/suffix)")
        elif _placeholder(doi):
            problems.append(f"release.doi {doi!r} is a placeholder, not a DOI")
        if not date:
            problems.append("release.release_date is not set")
        elif not isinstance(date, str) or not DATE_RE.match(date):
            problems.append(f"release.release_date {date!r} is not YYYY-MM-DD")
        elif _placeholder(date):
            problems.append(f"release.release_date {date!r} is a placeholder")
        if problems:
            raise ReleaseStateError(
                "refusing to build in final mode:\n  - "
                + "\n  - ".join(problems)
                + "\n\nReserve the DOI on Zenodo first (see "
                  "docs/PUBLISH_GUIDE.md), then set release.doi and "
                  "release.release_date in metadata.json. Nothing downstream "
                  "will invent or approximate them.")
    else:
        # Draft mode tolerates unset, and validates anything that *is* set so a
        # half-filled state cannot sit unnoticed until release day.
        if doi and (not DOI_RE.match(str(doi)) or _placeholder(str(doi))):
            raise ReleaseStateError(
                f"release.doi {doi!r} is set but malformed. Set it to null "
                "until a real DOI is reserved.")
        if date and (not DATE_RE.match(str(date)) or _placeholder(str(date))):
            raise ReleaseStateError(
                f"release.release_date {date!r} is set but malformed. Set it "
                "to null until the release date is known.")

    final = mode == "final"
    return {
        "mode": mode,
        "final": final,
        "draft": not final,
        "version": version,
        "version_string": f"v{version}" if final else f"v{version}-draft",
        "doi": doi if final else None,
        "doi_url": f"https://doi.org/{doi}" if final and doi else None,
        "release_date": date if final else None,
    }


def readme_banner(state: dict, stats: dict) -> str:
    """The README STATUS block. Generated in both modes, never hand-written."""
    if state["final"]:
        doi, url = state["doi"], state["doi_url"]
        return (
            f"[![DOI](https://zenodo.org/badge/DOI/{doi}.svg)]({url})\n"
            "\n"
            f"> **STATUS: released {state['version_string']} — "
            f"DOI [{doi}]({url}) — released {state['release_date']}.**\n"
            f"> Data cutoff {stats['data_cutoff']}; sources accessed "
            f"{stats['access_date']}.\n"
        )
    return (
        f"> **STATUS: DRAFT {state['version_string']} — not released, not "
        "verified, no DOI yet.**\n"
        "> This repository has not passed author verification. Do not cite it.\n"
        "> See `docs/VERIFY_CHECKLIST.md` for what has to happen before "
        "release.\n"
        f"> Data cutoff {stats['data_cutoff']}; sources accessed "
        f"{stats['access_date']}.\n"
    )


def report_identity_line(state: dict, stats: dict) -> str:
    """The italic identity line under the author block on the report's first
    page. In final mode it carries the DOI; in draft mode it carries no DOI at
    all, real or placeholder."""
    if state["final"]:
        return (f"*{state['version_string']} · DOI "
                f"[{state['doi']}]({state['doi_url']}) · released "
                f"{state['release_date']} · data cutoff {stats['data_cutoff']} "
                f"· sources accessed {stats['access_date']} · generated "
                f"{stats['generated_utc']}*")
    return (f"*{state['version_string']} · data cutoff {stats['data_cutoff']} "
            f"· sources accessed {stats['access_date']} · generated "
            f"{stats['generated_utc']}*")


def citation_reference(state: dict) -> str:
    """How the work should be cited, for the CISA issue and anywhere else that
    needs one line. No DOI exists in draft mode, and none is invented."""
    if state["final"]:
        return f"{state['doi_url']} (DOI {state['doi']})"
    return "DOI pending — not yet reserved; this text is regenerated at release"


def describe(state: dict) -> str:
    if state["final"]:
        return (f"release state: FINAL {state['version_string']}, DOI "
                f"{state['doi']}, released {state['release_date']}")
    return f"release state: DRAFT {state['version_string']}, no DOI"


if __name__ == "__main__":
    import sys
    try:
        st = load(assert_final="--final" in sys.argv)
    except ReleaseStateError as exc:
        print(f"release_state: {exc}", file=sys.stderr)
        raise SystemExit(2)
    print(describe(st))
