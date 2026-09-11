#!/usr/bin/env python3
"""
02_build.py — reconstruct the KEV schema timeline from daily catalog snapshots.

Two independent reconstructions are produced:

  CSV track   1,760 dated snapshots from the independent daily archiver,
              2021-11-12 onward. This is the only source covering 2021-2024.

  JSON track  the commit history of CISA's own mirror, 2025-01-27 onward.
              Shorter, but authoritative, and it carries the nested `cwes`
              structure that CSV flattens.

Where the two overlap they are compared, and the agreement rate is reported.
A timeline asserted from one uncorroborated source would be a weaker claim.

Outputs (data/processed/):
    field_presence_matrix.csv   one row per snapshot date, one column per field
    schema_timeline.csv         change events, both tracks
    json_field_presence.csv     JSON-track field sets by date
    artifacts.csv               data-quality events
    catalog_growth.csv          record count by date
    crosswalk.csv               CSV vs JSON agreement over the overlap
"""
from __future__ import annotations

import csv
import io
import json
import re
import subprocess
import sys
from collections import OrderedDict
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "sources"
PROC = ROOT / "data" / "processed"

SNAPSHOT_GLOB = "docs/*-cisa-kev.csv"
SNAPSHOT_RE = re.compile(r"(\d{4}-\d{2}-\d{2})-cisa-kev\.csv$")

# The catalog renamed its columns from human-readable labels to camelCase on
# 2021-12-01. Both spellings denote the same logical field, so the timeline is
# reported on canonical names with the rename recorded as its own event.
LABEL_TO_CANONICAL = {
    "CVE": "cveID",
    "Vendor/Project": "vendorProject",
    "Product": "product",
    "Vulnerability Name": "vulnerabilityName",
    "Date Added to Catalog": "dateAdded",
    "Short Description": "shortDescription",
    "Action": "requiredAction",
    "Due Date": "dueDate",
    "Notes": "notes",
}

CANONICAL_ORDER = [
    "cveID", "vendorProject", "product", "vulnerabilityName", "dateAdded",
    "shortDescription", "requiredAction", "dueDate",
    "knownRansomwareCampaignUse", "forensicTriage", "notes", "cwes",
]


def git(args, cwd):
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout


# --------------------------------------------------------------------------
# CSV track
# --------------------------------------------------------------------------


DENIAL_REF_RE = re.compile(r"Reference[^0-9]*#?\s*([0-9a-f]+(?:\.[0-9a-f]+){2,})",
                           re.I)
DENIAL_URL_RE = re.compile(r"permission to access\s+\"?([^\"<]+?)\"?\s+on this server",
                           re.I)


def parse_denial(text):
    """Pull the machine-checkable details out of a captured denial page.

    Akamai denial pages embed a reference identifier whose third dot-separated
    component is a Unix timestamp. Decoding it gives the exact moment the
    request was refused, which is what lets the capture failures be dated
    rather than merely noted. Returns {} for any page that does not match, so
    an unrecognised error page is reported as such rather than guessed at.
    """
    import html as _html
    flat = _html.unescape(text)
    out = {}
    if "access denied" in flat.lower():
        out["denial_kind"] = "access_denied"
    m = DENIAL_REF_RE.search(flat)
    if m:
        out["denial_ref"] = m.group(1)
        parts = m.group(1).split(".")
        for part in parts:
            if part.isdigit() and 1_000_000_000 < int(part) < 4_000_000_000:
                out["denial_epoch"] = int(part)
                out["denial_utc"] = datetime.fromtimestamp(
                    int(part), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                break
    m = DENIAL_URL_RE.search(flat)
    if m:
        out["denial_url"] = m.group(1).strip()
    if "edgesuite.net" in flat or "akamai" in flat.lower():
        out["denial_service"] = "akamai_edge"
    return out


def read_snapshot(path: Path) -> dict:
    """Return header info and row count for one dated snapshot."""
    raw = path.read_bytes()
    out = {
        "date": SNAPSHOT_RE.search(path.name).group(1),
        "bytes": len(raw),
        "has_bom": raw.startswith(b"\xef\xbb\xbf"),
        "usable": False,
        "fields_raw": [],
        "fields": [],
        "quoted_header": False,
        "n_records": None,
        "note": "",
    }

    text = raw.decode("utf-8-sig", errors="replace")
    first_line = text.split("\n", 1)[0].strip()

    if not first_line:
        out["note"] = "empty file"
        return out
    if first_line.lstrip().upper().startswith(("<HTML", "<!DOCTYPE", "<?XML")):
        out["note"] = "markup captured instead of CSV"
        out.update(parse_denial(text))
        return out

    out["quoted_header"] = first_line.startswith('"')
    try:
        cols = next(csv.reader([first_line]))
    except Exception as exc:  # pragma: no cover - defensive
        out["note"] = f"unparseable header: {exc}"
        return out

    cols = [c.strip() for c in cols]
    cols = [c for c in cols if c]          # drop trailing empty columns
    if not cols:
        out["note"] = "header parsed to zero columns"
        return out

    out["fields_raw"] = cols
    out["fields"] = [LABEL_TO_CANONICAL.get(c, c) for c in cols]
    # Naming convention of the header as published, before harmonisation.
    # A change here is a real schema-evolution event even though no field
    # appears or disappears, so it is detected from the data rather than
    # asserted in prose. See naming_events().
    out["naming_convention"] = ("label_case"
                                if any(c in LABEL_TO_CANONICAL for c in cols)
                                else "camel_case")

    try:
        rdr = csv.DictReader(io.StringIO(text))
        out["n_records"] = sum(1 for _ in rdr)
    except Exception:
        out["n_records"] = None

    out["usable"] = True
    return out


def build_csv_track():
    src = SOURCES / "hrbrmstr"
    paths = sorted(src.glob(SNAPSHOT_GLOB), key=lambda p: SNAPSHOT_RE.search(p.name).group(1))
    snaps = [read_snapshot(p) for p in paths]
    snaps.sort(key=lambda s: s["date"])
    return snaps


# --------------------------------------------------------------------------
# JSON track (CISA official mirror commit history)
# --------------------------------------------------------------------------

def build_json_track():
    src = SOURCES / "cisagov"
    log = git(
        ["log", "--reverse", "--format=%H|%cI", "--", "known_exploited_vulnerabilities.json"],
        cwd=src,
    ).strip().splitlines()

    seen_by_date = OrderedDict()
    for line in log:
        sha, iso = line.split("|", 1)
        day = iso[:10]
        blob = git(["show", f"{sha}:known_exploited_vulnerabilities.json"], cwd=src)
        try:
            doc = json.loads(blob)
        except json.JSONDecodeError:
            continue
        vulns = doc.get("vulnerabilities", [])
        fields = set()
        for v in vulns:
            fields.update(v.keys())
        # Last commit of a given day wins, matching the CSV track's daily grain.
        seen_by_date[day] = {
            "date": day,
            "commit": sha,
            "catalogVersion": doc.get("catalogVersion"),
            "n_records": len(vulns),
            "fields": sorted(fields),
            "top_level": sorted(doc.keys()),
        }
    return list(seen_by_date.values())


# --------------------------------------------------------------------------
# Independent JSON track (third source)
# --------------------------------------------------------------------------

def build_indep_track():
    """Independently-collected daily JSON, 2023-08-18 onward.

    Only the json/ directory of this source is read. Its csv/ directory is
    excluded in full, for two distinct reasons recorded in
    data/raw/third_source_manifest.json: for the shared dates before the first
    differing date those CSVs are byte-identical to the hrbrmstr archive and
    appear back-filled from it, so they are a copy rather than a witness; the
    later shared dates differ, but are already covered by this repository's own
    JSON, so counting both formats would count one collector twice. (This docstring
    carried the superseded wording "the csv/ directory is byte-identical to the
    hrbrmstr archive", which the full hash comparison contradicts.) The JSON was collected
    separately, in a format hrbrmstr never stored, which is what makes it
    independent evidence.
    """
    src = SOURCES / "lucagrippa" / "json"
    if not src.exists():
        return []
    rows = []
    for p in sorted(src.glob("*-cisa-kev.json")):
        day = p.name[:10]
        raw = p.read_text(encoding="utf-8", errors="replace")
        try:
            doc = json.loads(raw)
        except json.JSONDecodeError:
            r = {"date": day, "n_records": None, "fields": [], "usable": False,
                 "note": "markup captured instead of JSON"}
            r.update(parse_denial(raw))
            rows.append(r)
            continue
        vulns = doc.get("vulnerabilities", [])
        if not vulns:
            rows.append({"date": day, "n_records": 0, "fields": [],
                         "usable": False})
            continue
        f = set()
        for v in vulns:
            f.update(v.keys())
        rows.append({"date": day, "n_records": len(vulns),
                     "catalogVersion": doc.get("catalogVersion"),
                     "fields": sorted(f), "usable": True})
    return rows


# --------------------------------------------------------------------------
# Change events
# --------------------------------------------------------------------------

def naming_events(series, track_name):
    """Transitions in the published header's naming convention.

    These are schema-evolution events that field-presence tracking cannot see:
    on 2021-12-01 every column was renamed, but the set of logical fields was
    unchanged. Counting them separately is what lets the report state a total
    without conflating two different kinds of change.
    """
    events, prev = [], None
    for row in series:
        cur = row.get("naming_convention")
        if cur is None:
            continue
        if prev is not None and cur != prev["naming_convention"]:
            events.append({
                "track": track_name,
                "date": row["date"],
                "event": "naming_convention_change",
                "field": "(all fields)",
                "prev_date": prev["date"],
                "detail": (f"{prev['naming_convention']} -> {cur}; "
                           f"example: {prev['fields_raw'][0]} -> "
                           f"{row['fields_raw'][0]}"),
            })
        prev = row
    return events


def change_events(series, track_name):
    """series: list of dicts with 'date' and 'fields' (usable snapshots only)."""
    events = []
    prev_fields, prev_date = None, None
    for row in series:
        cur = set(row["fields"])
        if prev_fields is None:
            events.append({
                "track": track_name, "date": row["date"], "event": "baseline",
                "field": "", "detail": "|".join(row["fields"]),
                "prev_date": "",
            })
        else:
            for f in sorted(cur - prev_fields):
                events.append({
                    "track": track_name, "date": row["date"], "event": "field_added",
                    "field": f, "detail": f"absent on {prev_date}", "prev_date": prev_date,
                })
            for f in sorted(prev_fields - cur):
                events.append({
                    "track": track_name, "date": row["date"], "event": "field_removed",
                    "field": f, "detail": f"present on {prev_date}", "prev_date": prev_date,
                })
        prev_fields, prev_date = cur, row["date"]
    return events


def main() -> int:
    PROC.mkdir(parents=True, exist_ok=True)

    print("[build] reading CSV snapshots ...")
    snaps = build_csv_track()
    usable = [s for s in snaps if s["usable"]]
    print(f"[build]   {len(snaps)} snapshot files, {len(usable)} usable")

    print("[build] reading JSON history from CISA mirror ...")
    jrows = build_json_track()
    print(f"[build]   {len(jrows)} distinct JSON days")

    print("[build] reading independent JSON archive (third source) ...")
    irows_all = build_indep_track()
    irows = [r for r in irows_all if r["usable"]]
    print(f"[build]   {len(irows)} usable of {len(irows_all)} independent JSON days")

    # ---- field presence matrix (CSV track, canonical names) ----------------
    all_fields = []
    for s in usable:
        for f in s["fields"]:
            if f not in all_fields:
                all_fields.append(f)
    ordered = [f for f in CANONICAL_ORDER if f in all_fields] + \
              [f for f in all_fields if f not in CANONICAL_ORDER]

    with open(PROC / "field_presence_matrix.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "n_records", "header_style", *ordered])
        for s in usable:
            style = []
            if s["has_bom"]:
                style.append("BOM")
            style.append("quoted" if s["quoted_header"] else "bare")
            if s["fields_raw"] and s["fields_raw"][0] == "CVE":
                style.append("label-case")
            else:
                style.append("camelCase")
            present = set(s["fields"])
            w.writerow([s["date"], s["n_records"], "+".join(style),
                        *[1 if f in present else 0 for f in ordered]])

    # ---- JSON presence -----------------------------------------------------
    jfields = []
    for r in jrows:
        for f in r["fields"]:
            if f not in jfields:
                jfields.append(f)
    jordered = [f for f in CANONICAL_ORDER if f in jfields] + \
               [f for f in jfields if f not in CANONICAL_ORDER]
    with open(PROC / "json_field_presence.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "commit", "catalogVersion", "n_records", *jordered])
        for r in jrows:
            present = set(r["fields"])
            w.writerow([r["date"], r["commit"][:12], r["catalogVersion"], r["n_records"],
                        *[1 if f in present else 0 for f in jordered]])

    # ---- independent JSON presence ----------------------------------------
    ifields = []
    for r in irows:
        for f in r["fields"]:
            if f not in ifields:
                ifields.append(f)
    iordered = [f for f in CANONICAL_ORDER if f in ifields] + \
               [f for f in ifields if f not in CANONICAL_ORDER]
    with open(PROC / "indep_json_field_presence.csv", "w", newline="",
              encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "catalogVersion", "n_records", *iordered])
        for r in irows:
            present = set(r["fields"])
            w.writerow([r["date"], r.get("catalogVersion"), r["n_records"],
                        *[1 if f in present else 0 for f in iordered]])

    # ---- change events -----------------------------------------------------
    ev = (change_events(usable, "csv_daily")
          + naming_events(usable, "csv_daily")
          + change_events(jrows, "json_official")
          + change_events(irows, "json_independent"))
    ev.sort(key=lambda e: (e["track"], e["date"], e["event"]))
    with open(PROC / "schema_timeline.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["track", "date", "event", "field", "prev_date", "detail"])
        w.writeheader()
        w.writerows(ev)

    # ---- catalog growth ----------------------------------------------------
    with open(PROC / "catalog_growth.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "n_records", "source"])
        for s in usable:
            if s["n_records"] is not None:
                w.writerow([s["date"], s["n_records"], "csv_daily"])
        for r in jrows:
            w.writerow([r["date"], r["n_records"], "json_official"])

    # ---- data-quality artifacts -------------------------------------------
    arts = []
    for s in snaps:
        if not s["usable"]:
            bits = [s["note"]]
            if s.get("denial_service"):
                bits.append(f"service={s['denial_service']}")
            if s.get("denial_kind"):
                bits.append(f"kind={s['denial_kind']}")
            if s.get("denial_ref"):
                bits.append(f"ref={s['denial_ref']}")
            if s.get("denial_utc"):
                bits.append(f"refused_utc={s['denial_utc']}")
            if s.get("denial_url"):
                bits.append(f"url={s['denial_url']}")
            arts.append({"date": s["date"], "kind": "unusable_snapshot",
                         "detail": "; ".join(bits), "bytes": s["bytes"],
                         "source": "csv_daily"})
    prev = None
    for s in usable:
        if prev is not None:
            if s["has_bom"] != prev["has_bom"]:
                arts.append({"date": s["date"], "kind": "bom_change",
                             "detail": f"BOM {'added' if s['has_bom'] else 'removed'} "
                                       f"(prev {prev['date']})", "bytes": s["bytes"]})
            if s["quoted_header"] != prev["quoted_header"]:
                arts.append({"date": s["date"], "kind": "quoting_change",
                             "detail": f"header quoting {'on' if s['quoted_header'] else 'off'} "
                                       f"(prev {prev['date']})", "bytes": s["bytes"]})
            if s["n_records"] is not None and prev["n_records"] is not None:
                if s["n_records"] < prev["n_records"]:
                    arts.append({"date": s["date"], "kind": "record_count_decrease",
                                 "detail": f"{prev['n_records']} -> {s['n_records']} "
                                           f"(prev {prev['date']})", "bytes": s["bytes"]})
        prev = s
    # gaps in daily coverage
    dts = [date.fromisoformat(s["date"]) for s in usable]
    for a, b in zip(dts, dts[1:]):
        gap = (b - a).days
        if gap > 1:
            arts.append({"date": b.isoformat(), "kind": "coverage_gap",
                         "detail": f"{gap - 1} day(s) missing after {a.isoformat()}",
                         "bytes": ""})
    for r in irows_all:
        if not r["usable"] and r.get("denial_kind"):
            bits = [r.get("note", "unusable")]
            for k, lbl in (("denial_service", "service"), ("denial_kind", "kind"),
                           ("denial_ref", "ref"), ("denial_utc", "refused_utc"),
                           ("denial_url", "url")):
                if r.get(k):
                    bits.append(f"{lbl}={r[k]}")
            arts.append({"date": r["date"], "kind": "unusable_snapshot",
                         "detail": "; ".join(bits), "bytes": "",
                         "source": "json_independent"})
    arts.sort(key=lambda a: (a["date"], a["kind"]))
    with open(PROC / "artifacts.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["date", "kind", "detail", "bytes",
                                           "source"], restval="")
        w.writeheader()
        w.writerows(arts)

    # ---- crosswalk: every day covered by two or more sources --------------
    jmap = {r["date"]: set(r["fields"]) for r in jrows}
    imap = {r["date"]: set(r["fields"]) for r in irows}
    cmap = {s["date"]: set(s["fields"]) for s in usable}
    all_days = sorted(set(cmap) | set(jmap) | set(imap))
    n_multi = n_agree = 0
    with open(PROC / "crosswalk.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "n_sources", "csv_daily", "json_official",
                    "json_independent", "agree", "disagreement"])
        for d in all_days:
            present = {k: v for k, v in
                       (("csv_daily", cmap.get(d)),
                        ("json_official", jmap.get(d)),
                        ("json_independent", imap.get(d))) if v is not None}
            if len(present) < 2:
                continue
            sets = list(present.values())
            agree = all(x == sets[0] for x in sets)
            n_multi += 1
            n_agree += int(agree)
            diff = ""
            if not agree:
                union = set().union(*sets)
                diff = "; ".join(
                    f"{k} missing:{'|'.join(sorted(union - v)) or 'none'}"
                    for k, v in present.items())
            w.writerow([d, len(present),
                        "|".join(sorted(cmap[d])) if d in cmap else "",
                        "|".join(sorted(jmap[d])) if d in jmap else "",
                        "|".join(sorted(imap[d])) if d in imap else "",
                        int(agree), diff])

    print(f"[build] wrote {len(ev)} change events, {len(arts)} artifacts, "
          f"{n_multi} multi-source days ({n_agree} in agreement)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
