#!/usr/bin/env python3
"""
01_fetch.py — acquire the three source mirrors at pinned commits and log provenance.

Both sources are git repositories. Pinning to a commit is what makes this build
reproducible: re-running the pipeline a month from now against the same pins
reproduces the same outputs, even though both repositories keep growing.

Usage:
    python code/01_fetch.py                # clone/checkout at pinned commits
    python code/01_fetch.py --update-pins  # move pins to current HEAD (then
                                           # the whole pipeline must be re-run
                                           # and the report re-verified)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES_DIR = ROOT / "sources"          # git-ignored; not part of the release
RAW_DIR = ROOT / "data" / "raw"
PROVENANCE = RAW_DIR / "PROVENANCE.txt"
PINS_FILE = ROOT / "data" / "raw" / "source_pins.json"

SOURCES = {
    "hrbrmstr": {
        "url": "https://github.com/hrbrmstr/cisa-known-exploited-vulns.git",
        "commit": "3e428ceaa1e18ce466db17c8b4c23f5a23e53c92",
        "role": "daily CSV snapshots, 2021-11-12 onward",
        "license": "MIT (tooling); archived CISA content is public domain",
    },
    "cisagov": {
        "url": "https://github.com/cisagov/kev-data.git",
        "commit": "f6fafe2585c7cc2a7568d13d08024cf142b37d3a",
        "role": "CISA official mirror: JSON, CSV, published JSON schema",
        "license": "CC0-1.0",
    },
    "lucagrippa": {
        "url": "https://github.com/lucagrippa/cisa-kev-archive.git",
        "commit": "276aa25018e0b1ba945ea0638f71682bd70422c1",
        # Corrected. This carried the superseded wording: the repository's
        # csv/ files "are byte-identical to the hrbrmstr archive (back-filled
        # from it)", stated without qualification, which the full hash
        # comparison in data/raw/third_source_manifest.json contradicts —
        # only the shared dates before the first differing date are identical.
        # No count is hard-coded here because this constant is written before
        # the comparison runs; it points at the derived record instead.
        "role": ("independent daily JSON snapshots, 2023-08-18 onward. "
                 "ONLY the json/ directory is used. The csv/ directory is "
                 "excluded in full: for the shared dates before the first "
                 "differing date those files are byte-identical to the "
                 "hrbrmstr archive and appear back-filled from it, while the "
                 "later shared dates are already covered by this repository's "
                 "own JSON, so counting both formats would count one "
                 "collector twice. Per-date hashes and counts are in "
                 "data/raw/third_source_manifest.json."),
        "license": ("no license file on the repository; the archived content is "
                    "CISA's KEV catalog, a US government work released CC0. "
                    "Only that content is used; no repository code is copied "
                    "and no files are redistributed (sources/ is git-ignored)."),
    },
}


def run(cmd, cwd=None, check=True):
    return subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def log_provenance(name: str, url: str, commit: str, detail: str) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"{stamp}\t{name}\t{url}\t{commit}\t{detail}\n"
    with open(PROVENANCE, "a", encoding="utf-8") as fh:
        fh.write(line)


def ensure_source(name: str, spec: dict, update_pins: bool) -> str:
    dest = SOURCES_DIR / name
    dest.parent.mkdir(parents=True, exist_ok=True)

    if not dest.exists():
        print(f"[fetch] cloning {name} from {spec['url']}")
        run(["git", "clone", "--quiet", spec["url"], str(dest)])
    else:
        print(f"[fetch] {name} already present; fetching")
        run(["git", "fetch", "--quiet", "--all"], cwd=dest)

    if update_pins:
        head = run(["git", "rev-parse", "HEAD"], cwd=dest).stdout.strip()
        print(f"[fetch] {name}: pin updated to {head}")
        commit = head
    else:
        commit = spec["commit"]
        run(["git", "checkout", "--quiet", commit], cwd=dest)
        print(f"[fetch] {name}: checked out pinned {commit[:12]}")

    commit_date = run(
        ["git", "show", "-s", "--format=%cI", commit], cwd=dest
    ).stdout.strip()
    n_commits = run(["git", "rev-list", "--count", commit], cwd=dest).stdout.strip()

    log_provenance(
        name,
        spec["url"],
        commit,
        f"commit_date={commit_date} n_commits={n_commits} role={spec['role']} "
        f"license={spec['license']}",
    )
    return commit




def write_third_source_manifest(pins: dict) -> None:
    """Evidence manifest for the third source (author ruling V3, item 6).

    Two things must be reproducible by anyone re-running this build:

      1. The claim that the third repository's CSV files are copies of the
         primary archive's, and therefore cannot count as independent
         corroboration. Proven here by hashing every date both repositories
         hold and recording how many are byte-identical.

      2. The JSON files that DO provide corroboration. Hashes are recorded for
         the dates that carry the report's change events, so a reader can
         confirm they are examining the same bytes this build examined.

    No file from the third repository is copied into this repository. Only
    hashes, counts and dates are recorded.
    """
    third = SOURCES_DIR / "lucagrippa"
    primary = SOURCES_DIR / "hrbrmstr" / "docs"
    if not third.exists():
        return

    # --- 1. CSV identity evidence ------------------------------------------
    csv_rows = []
    identical = differing = 0
    third_csv = third / "csv"
    if third_csv.exists():
        for f in sorted(third_csv.glob("*-cisa-kev.csv")):
            day = f.name[:10]
            counterpart = primary / f"{day}-cisa-kev.csv"
            if not counterpart.exists():
                continue
            h_third = sha256_file(f)
            h_primary = sha256_file(counterpart)
            same = h_third == h_primary
            identical += same
            differing += (not same)
            csv_rows.append({"date": day, "sha256_third": h_third,
                             "sha256_primary": h_primary, "identical": same})

    # Where does the back-filled run end? Everything before the first differing
    # date is byte-identical, which is what identifies it as a copy.
    diffs = [r["date"] for r in csv_rows if not r["identical"]]
    first_diff = min(diffs) if diffs else None
    n_before = sum(1 for r in csv_rows if first_diff and r["date"] < first_diff)

    # --- 2. hashes of the JSON actually relied on --------------------------
    event_dates = ["2023-08-18", "2023-10-11", "2023-10-12", "2024-06-25",
                   "2024-06-26", "2024-11-26", "2026-08-31", "2026-09-01",
                   "2026-09-02"]
    json_rows = []
    for day in event_dates:
        f = third / "json" / f"{day}-cisa-kev.json"
        if f.exists():
            json_rows.append({"date": day, "bytes": f.stat().st_size,
                              "sha256": sha256_file(f)})

    json_files = sorted((third / "json").glob("*-cisa-kev.json"))
    manifest = {
        "purpose": ("Reproducibility evidence for the third source. Records why "
                    "its CSV files are excluded and pins the JSON files the "
                    "corroboration rests on."),
        "repository": pins["lucagrippa"]["url"],
        "commit": pins["lucagrippa"]["commit"],
        "access_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "accessed_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "licence": ("No licence file is present on the repository. The archived "
                    "content is the CISA Known Exploited Vulnerabilities "
                    "catalog, a US government work released under CC0 by CISA. "
                    "This build reads that archived public-domain content for "
                    "verification only. No file from the repository is copied "
                    "into, redistributed by, or released with this project; the "
                    "working clone lives in the git-ignored sources/ directory."),
        "json_used": {
            "directory": "json/",
            "file_count": len(json_files),
            "first_date": json_files[0].name[:10] if json_files else None,
            "last_date": json_files[-1].name[:10] if json_files else None,
            "role": ("Independently collected. The primary archive stored CSV "
                     "only and never held these JSON files, which is what makes "
                     "them a second witness rather than a copy."),
            "event_date_hashes": json_rows,
        },
        "csv_excluded": {
            "directory": "csv/",
            "dates_compared_with_primary": len(csv_rows),
            "byte_identical_to_primary": identical,
            "differing_from_primary": differing,
            "all_identical_before": first_diff,
            "dates_before_that_all_identical": n_before,
            "conclusion": (
                f"Excluded in full, for two distinct reasons. For every one of "
                f"the {n_before} dates before {first_diff}, the third "
                f"repository's CSV is byte-identical to the primary archive's, "
                f"indicating it was back-filled from that archive and is a copy "
                f"rather than a witness. From {first_diff} onward the "
                f"repository appears to collect its own CSVs, but those dates "
                f"are already covered by its JSON files, which this build does "
                f"use; counting both would count one collector twice. "
                f"code/02_build.py reads only json/."),
            "per_date_hashes_file": "third_source_csv_identity.csv",
        },
    }
    (RAW_DIR / "third_source_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    import csv as _csv
    with open(RAW_DIR / "third_source_csv_identity.csv", "w", newline="",
              encoding="utf-8") as fh:
        w = _csv.DictWriter(fh, fieldnames=["date", "sha256_third",
                                            "sha256_primary", "identical"])
        w.writeheader()
        for r in csv_rows:
            w.writerow({**r, "identical": int(r["identical"])})

    log_provenance(
        "lucagrippa_manifest", pins["lucagrippa"]["url"],
        pins["lucagrippa"]["commit"],
        f"csv_dates_compared={len(csv_rows)} byte_identical={identical} "
        f"differing={differing} json_files={len(json_files)} "
        f"licence=none_on_repo content=CISA_CC0 redistributed=no")
    # A ratio, not a universal claim: the full breakdown, including the
    # boundary date, is written to data/raw/third_source_manifest.json above.
    print(f"[fetch] third-source manifest: {identical}/{len(csv_rows)} CSVs "
          f"byte-identical to primary; {len(json_files)} JSON files used")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--update-pins", action="store_true")
    args = ap.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    pins = {}
    for name, spec in SOURCES.items():
        pins[name] = {
            "url": spec["url"],
            "commit": ensure_source(name, spec, args.update_pins),
            "role": spec["role"],
            "license": spec["license"],
        }

    # The published schema is small and central to the finding, so a copy is
    # kept in data/raw with its own hash. Everything else is read from the
    # pinned working trees.
    schema_src = SOURCES_DIR / "cisagov" / "known_exploited_vulnerabilities_schema.json"
    if schema_src.exists():
        schema_dst = RAW_DIR / "known_exploited_vulnerabilities_schema.json"
        schema_dst.write_bytes(schema_src.read_bytes())
        digest = sha256_file(schema_dst)
        size = schema_dst.stat().st_size
        log_provenance(
            "cisagov_schema_file",
            # Pinned to the commit, not to a branch: a branch URL shows whatever
            # that branch points at today, which is not what this build read.
            f"https://github.com/cisagov/kev-data/blob/"
            f"{pins['cisagov']['commit']}/"
            "known_exploited_vulnerabilities_schema.json",
            pins["cisagov"]["commit"],
            f"bytes={size} sha256={digest}",
        )
        pins["schema_file"] = {"bytes": size, "sha256": digest}
        print(f"[fetch] schema copied: {size} bytes, sha256={digest[:16]}...")
    else:
        print("[fetch] WARNING: schema file not found in cisagov mirror", file=sys.stderr)

    if "lucagrippa" in pins:
        write_third_source_manifest(pins)

    pins["fetched_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    PINS_FILE.write_text(json.dumps(pins, indent=2) + "\n", encoding="utf-8")
    print(f"[fetch] pins written to {PINS_FILE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
