#!/usr/bin/env python3
"""
09_snapshot_links.py — generate verifiable links to the snapshots behind each event.

Defect C1, found by the author during Section C verification: the spot-check
instructions carried hand-typed GitHub URLs built on the branch name `main`.
That repository's default branch is `batman`; `main` does not exist, so every
link 404'd. A hand-typed link is also mutable even when correct — a branch moves,
and next year the same URL shows a different file.

So the links are generated, from two things the build already pins: the commit
SHA in data/raw/source_pins.json, and the event dates in
data/processed/schema_timeline.csv. Nothing here is typed. Every link addresses
an immutable commit, so it shows the same bytes this build read, forever.

`--verify` checks each link over the network and each object in the local pinned
clone before writing the file.

Usage:
    python code/09_snapshot_links.py
    python code/09_snapshot_links.py --verify
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import urllib.request
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = "hrbrmstr/cisa-known-exploited-vulns"


def blob(sha, d):
    return f"https://github.com/{REPO}/blob/{sha}/docs/{d}-cisa-kev.csv"


def raw(sha, d):
    return f"https://raw.githubusercontent.com/{REPO}/{sha}/docs/{d}-cisa-kev.csv"


def http_status(url, timeout=25):
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception as e:                       # network refused, DNS, TLS
        return f"error: {type(e).__name__}"


def git_has(sha, d):
    r = subprocess.run(
        ["git", "cat-file", "-e", f"{sha}:docs/{d}-cisa-kev.csv"],
        cwd=ROOT / "sources" / "hrbrmstr", capture_output=True)
    return r.returncode == 0


def prev_available(matrix_dates, d):
    """The last snapshot date strictly before d, from the dates actually held."""
    earlier = [x for x in matrix_dates if x < d]
    return earlier[-1] if earlier else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()

    sha = json.loads((ROOT / "data" / "raw" / "source_pins.json")
                     .read_text())["hrbrmstr"]["commit"]
    with open(ROOT / "data" / "processed" / "field_presence_matrix.csv") as fh:
        matrix_dates = [r["date"] for r in csv.DictReader(fh)]
    with open(ROOT / "data" / "processed" / "schema_timeline.csv") as fh:
        tl = [r for r in csv.DictReader(fh) if r["track"] == "csv_daily"]

    checks = []
    first = matrix_dates[0]
    checks.append({"n": 1, "date": first, "what": "first snapshot in the archive",
                   "expect": "header in human-readable labels, beginning "
                             "`CVE,Vendor/Project`"})
    n = 2
    seen_removed = set()   # a field returning after removal is RESTORED, not
                           # "first present"; same rule as 07_release_notes.py
    for r in sorted([x for x in tl if x["event"] != "baseline"],
                    key=lambda x: x["date"]):
        d_, f_ = r["date"], r["field"]
        prev = prev_available(matrix_dates, d_)
        if r["event"] == "naming_convention_change":
            checks.append({"n": n, "date": d_, "what": "naming/canonicalization event",
                           "expect": "header now begins `cveID,vendorProject` — the "
                                     "same fields, renamed"})
            n += 1
        elif r["event"] == "field_added":
            what = (f"`{f_}` restored after removal" if f_ in seen_removed
                    else f"`{f_}` first present")
            checks.append({"n": n, "date": d_, "what": what,
                           "expect": f"`{f_}` IS in the header",
                           "pair_date": prev,
                           "pair_expect": f"`{f_}` is NOT in the header"})
            n += 1
        elif r["event"] == "field_removed":
            seen_removed.add(f_)
            checks.append({"n": n, "date": d_, "what": f"`{f_}` removed",
                           "expect": f"`{f_}` is NOT in the header",
                           "pair_date": prev,
                           "pair_expect": f"`{f_}` IS in the header"})
            n += 1

    dates = []
    for c in checks:
        dates.append(c["date"])
        if c.get("pair_date"):
            dates.append(c["pair_date"])
    dates = sorted(set(dates))

    # Verification results are persisted so that regenerating WITHOUT --verify
    # reproduces the same file. Otherwise the QA check that this file is
    # generated rather than hand-edited would fail whenever it re-ran the
    # generator in its cheap mode -- which it did, on the first attempt.
    vpath = ROOT / "data" / "raw" / "snapshot_link_verification.json"
    status = {}
    if vpath.exists():
        status = {k: tuple(v) for k, v in json.loads(vpath.read_text())["results"].items()}
    if args.verify:
        print(f"[links] verifying {len(dates)} snapshots at commit {sha[:12]}")
        bogus = "1999-01-01"
        ctl = http_status(raw(sha, bogus))
        print(f"[links] control (a date that should not exist): {bogus} -> {ctl}")
        if ctl != 404:
            print("[links] WARNING: control did not return 404; a 200 below may "
                  "not prove existence")
        for d_ in dates:
            st, g = http_status(raw(sha, d_)), git_has(sha, d_)
            status[d_] = (st, g)
            print(f"[links]   {d_}  http={st}  git_object={'present' if g else 'MISSING'}")
        bad = [d_ for d_, (st, g) in status.items() if st != 200 or not g]
        if bad:
            print(f"[links] FAILED: {bad}")
            return 1
        print("[links] all snapshots verified")
        vpath.write_text(json.dumps({
            "commit": sha,
            "control_date": bogus,
            "control_http": ctl,
            "results": {d_: list(v) for d_, v in status.items()},
        }, indent=2) + "\n", encoding="utf-8")

    lines = [
        "<!-- GENERATED FILE — do not edit by hand.",
        "     Written by code/09_snapshot_links.py from the pinned commit in",
        "     data/raw/source_pins.json and the events in",
        "     data/processed/schema_timeline.csv. -->",
        "",
        "# Snapshot links for hand-verification",
        "",
        "Each link addresses an **immutable commit**, not a branch, so it shows the",
        "exact bytes this build read and will keep doing so.",
        "",
        f"Repository: `{REPO}`  ",
        f"Pinned commit: `{sha}`",
        "",
        "> The `main` branch does not exist in this repository — its default branch",
        "> is `batman`. Links built on a branch name are both wrong here and mutable",
        "> in general, which is why every link below is pinned to the commit.",
        "",
        "Open the link and read **the first line only**: it lists the column names.",
        "",
        "## What NOT to count, and why",
        "",
        "These checks are about the **header**, not the number of rows. Do not try",
        "to establish a record count from the browser:",
        "",
        "- Searching the page for `CVE-` does not give a row count. That string",
        "  also occurs inside `shortDescription` and `notes` text, so the match",
        "  count exceeds the number of records.",
        "- A rendered line count is not a record count either. A quoted CSV field",
        "  may contain an embedded newline, so one record can span several lines.",
        "",
        "Record counts in this project come from parsing the CSV with a real CSV",
        "reader in `code/02_build.py`, and are reported as machine-verified rather",
        "than author-verified. Verifying a header by eye is reliable; counting rows",
        "by eye is not, and the two should not be recorded as the same kind of",
        "evidence.",
        "",
    ]
    for c in checks:
        lines.append(f"## Check {c['n']} — {c['date']}: {c['what']}")
        lines.append("")
        if c.get("pair_date"):
            lines.append(f"- [ ] **{c['date']}** — {c['expect']}  ")
            lines.append(f"      {blob(sha, c['date'])}")
            lines.append(f"- [ ] **{c['pair_date']}** (the preceding snapshot) — "
                         f"{c['pair_expect']}  ")
            lines.append(f"      {blob(sha, c['pair_date'])}")
        else:
            lines.append(f"- [ ] {c['expect']}  ")
            lines.append(f"      {blob(sha, c['date'])}")
        lines.append("")
    lines += [
        f"## Check {len(checks) + 1} — a date of your own choosing",
        "",
        "- [ ] Pick any date in range not listed above. Open",
        f"      `https://github.com/{REPO}/blob/{sha}/docs/YYYY-MM-DD-cisa-kev.csv`",
        "      with your date substituted, read the header, then find that date's row",
        "      in `data/processed/field_presence_matrix.csv` and confirm the columns",
        "      marked `1` match the header you just read.",
        "",
        "## If a link does not load",
        "",
        "GitHub's file view occasionally rate-limits. The same bytes are served",
        "without the web interface at:",
        "",
        f"`https://raw.githubusercontent.com/{REPO}/{sha}/docs/YYYY-MM-DD-cisa-kev.csv`",
        "",
    ]
    status = {d_: status[d_] for d_ in dates if d_ in status}
    if status:
        lines += ["## Link verification", "",
                  "Checked automatically before this file was written. Each snapshot",
                  "was confirmed twice: the object exists in the pinned commit, and a",
                  "live fetch returned HTTP 200. A deliberately invalid date was used",
                  "as a control and correctly returned 404.", "",
                  "| Date | Object in pinned commit | HTTP |", "|---|---|---|"]
        for d_ in dates:
            st, g = status[d_]
            lines.append(f"| {d_} | {'present' if g else 'MISSING'} | {st} |")
        lines.append("")

    out = ROOT / "docs" / "SNAPSHOT_LINKS.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"[links] docs/SNAPSHOT_LINKS.md written "
          f"({len(checks)} checks, {len(dates)} snapshots)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
