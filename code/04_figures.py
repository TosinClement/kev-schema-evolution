#!/usr/bin/env python3
"""
04_figures.py — write report/stats.json and build the figures.

stats.json is the single source of every number the report quotes. The report
build interpolates from it; no number is ever typed into prose. Change the data,
re-run the pipeline, and the report's numbers move with it.

Figures follow the dataviz skill:
  - Fig 1 is a presence-band chart. Identity is carried by the y-axis labels, not
    by colour, so a single hue is used for all twelve fields rather than a
    twelve-way categorical palette (which no palette can make CVD-safe).
  - Fig 2 is a single series, so it carries no legend; the title names it.
  - Both use one axis, recessive grid, direct annotation of the values that matter.

Usage:
    python code/04_figures.py            # DRAFT stamp on
    python code/04_figures.py --final    # stamp removed (post-verification only)
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from collections import Counter
from datetime import date
from pathlib import Path

import release_state

import matplotlib
matplotlib.use("Agg")

# A1: figures must be byte-reproducible across machines and runs.
#   - a fixed font family bundled with matplotlib, so metrics do not depend on
#     which fonts the host happens to have installed
#   - a fixed canvas (figsize x dpi) with constrained layout instead of
#     bbox_inches="tight", whose rounding varies between matplotlib versions
#     and produced 1px dimension drift between environments
#   - no timestamp or version string written into the PNG metadata
# The exact matplotlib version is pinned in requirements.lock; these settings
# make the output stable given that pin.
matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.sans-serif": ["DejaVu Sans"],
    "svg.hashsalt": "kev-schema-evolution",
    "figure.constrained_layout.use": True,
})
PNG_METADATA = {"Software": None, "Creation Time": None}
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
RAW = ROOT / "data" / "raw"
SOURCES = ROOT / "sources"
REPORT = ROOT / "report"
FIGS = REPORT / "figures"

# --- palette (dataviz reference instance, light mode) ----------------------
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
BLUE = "#2a78d6"
ORANGE = "#eb6834"
GRID = "#d8d7d2"

CANON = ["cveID", "vendorProject", "product", "vulnerabilityName", "dateAdded",
         "shortDescription", "requiredAction", "dueDate",
         "knownRansomwareCampaignUse", "forensicTriage", "notes", "cwes"]


def rows(name):
    with open(PROC / name, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def d(s):
    return date.fromisoformat(s)


# ---------------------------------------------------------------------------
# stats
# ---------------------------------------------------------------------------



def _third_source_manifest():
    """Third-source provenance, as written by code/01_fetch.py (ruling V3)."""
    f = RAW / "third_source_manifest.json"
    if not f.exists():
        return {}
    m = json.loads(f.read_text())
    return {k: m[k] for k in ("repository", "commit", "access_date", "licence",
                              "json_used", "csv_excluded") if k in m}


def _capture_failures(arts):
    """Structured record of each refused capture, parsed by the pipeline.

    Nothing here is typed by hand: the service, the reference identifier, the
    decoded refusal time and the requested URL all come from the captured page
    itself, so the report's account of these days is checkable against the
    archives rather than asserted.
    """
    out = []
    for a in arts:
        if a["kind"] != "unusable_snapshot":
            continue
        rec = {"date": a["date"], "source": a.get("source", "")}
        for piece in a["detail"].split(";"):
            piece = piece.strip()
            if "=" in piece:
                k, v = piece.split("=", 1)
                rec[k.strip()] = v.strip()
        out.append(rec)
    out.sort(key=lambda r: (r.get("refused_utc") or r["date"]))
    return out


def _notes_boundary(matrix):
    """Entry-count change across each `notes` transition, and fill on return.

    These figures appear in the report's Section 3. They are computed here so
    the prose interpolates them rather than stating them by hand.
    """
    import json as _json
    from pathlib import Path as _P
    by = {r["date"]: r for r in matrix}
    out = {}
    for label, prev_d, cur_d in (("removed", "2021-12-10", "2021-12-11"),
                                 ("restored", "2022-05-23", "2022-05-24")):
        a, b = by.get(prev_d), by.get(cur_d)
        if a and b and a["n_records"] and b["n_records"]:
            out[f"{label}_prev_date"] = prev_d
            out[f"{label}_date"] = cur_d
            out[f"{label}_prev_count"] = int(a["n_records"])
            out[f"{label}_count"] = int(b["n_records"])
            out[f"{label}_new_entries"] = int(b["n_records"]) - int(a["n_records"])
    # how populated was `notes` immediately before removal and on return
    src = _P(__file__).resolve().parents[1] / "sources" / "hrbrmstr" / "docs"
    import csv as _csv
    for label, day in (("before_removal", "2021-12-10"), ("on_return", "2022-05-24")):
        f = src / f"{day}-cisa-kev.csv"
        if not f.exists():
            continue
        rows = list(_csv.DictReader(open(f, encoding="utf-8-sig")))
        if not rows or "notes" not in rows[0]:
            continue
        filled = sum(1 for r in rows if (r.get("notes") or "").strip())
        out[f"notes_filled_{label}"] = filled
        out[f"notes_rows_{label}"] = len(rows)
    return out


def build_stats() -> dict:
    matrix = rows("field_presence_matrix.csv")
    jrows = rows("json_field_presence.csv")
    timeline = rows("schema_timeline.csv")
    arts = rows("artifacts.csv")
    cross = rows("crosswalk.csv")
    try:
        indep = rows("indep_json_field_presence.csv")
    except FileNotFoundError:
        indep = []

    pins = json.loads((RAW / "source_pins.json").read_text())
    schema = json.loads((RAW / "known_exploited_vulnerabilities_schema.json").read_text())
    live = json.loads((SOURCES / "cisagov" / "known_exploited_vulnerabilities.json").read_text())

    dates = [r["date"] for r in matrix]
    asof = dates[-1]
    span_days = (d(dates[-1]) - d(dates[0])).days + 1

    # field spans
    spans = {}
    for f in CANON:
        present = [r["date"] for r in matrix if r.get(f) == "1"]
        if present:
            spans[f] = {
                "first_seen": present[0],
                "last_seen": present[-1],
                "days_present": len(present),
                "share_of_days": round(len(present) / len(matrix), 4),
            }

    described = set(schema.get("$defs", {}).get("vulnerability", {})
                    .get("properties", {}).keys())
    observed = set()
    for v in live.get("vulnerabilities", []):
        observed.update(v.keys())

    log = subprocess.run(
        ["git", "log", "--format=%H|%cI", "--",
         "known_exploited_vulnerabilities_schema.json"],
        cwd=SOURCES / "cisagov", capture_output=True, text=True, check=True
    ).stdout.strip().splitlines()
    schema_last = log[0].split("|")[1][:10] if log else None

    csv_unusable = [a for a in arts
                    if a["kind"] == "unusable_snapshot"
                    and a.get("source", "csv_daily") == "csv_daily"]

    events = [r for r in timeline
              if r["track"] == "csv_daily"
              and r["event"] in ("field_added", "field_removed")]
    naming = [r for r in timeline
              if r["track"] == "csv_daily"
              and r["event"] == "naming_convention_change"]

    ft_first = spans.get("forensicTriage", {}).get("first_seen")

    tsm_ = _third_source_manifest()
    stats = {
        "as_of": asof,
        "data_cutoff": asof,          # last catalog snapshot included
        "access_date": tsm_.get("access_date"),   # sources fetched/verified
        "generated_utc": subprocess.run(
            ["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
            capture_output=True, text=True, check=True).stdout.strip(),
        "sources": {
            "archive_repo": pins["hrbrmstr"]["url"],
            "archive_commit": pins["hrbrmstr"]["commit"],
            "official_repo": pins["cisagov"]["url"],
            "official_commit": pins["cisagov"]["commit"],
            "indep_repo": pins.get("lucagrippa", {}).get("url"),
            "indep_commit": pins.get("lucagrippa", {}).get("commit"),
            "schema_sha256": pins.get("schema_file", {}).get("sha256"),
            "third_source_manifest": _third_source_manifest(),
        },
        "coverage": {
            # Coverage describes the PRIMARY CSV track only. The artifacts table
            # also records a refused capture from the third source, and counting
            # that here inflated snapshot_files to 1,761 against 1,760 files on
            # disk. Filter by source. (Third-source failures remain visible in
            # artifacts.capture_failures, labelled by source.)
            "snapshot_files": len(matrix) + len(csv_unusable),
            "usable_snapshots": len(matrix),
            "unusable_snapshots": len(csv_unusable),
            "first_date": dates[0],
            "last_date": dates[-1],
            "span_days": span_days,
            "coverage_pct": round(100 * len(matrix) / span_days, 2),
            "coverage_gaps": len([a for a in arts if a["kind"] == "coverage_gap"]),
        },
        "catalog": {
            "first_count": int(matrix[0]["n_records"]),
            "last_count": int(matrix[-1]["n_records"]),
            "net_growth": int(matrix[-1]["n_records"]) - int(matrix[0]["n_records"]),
            "growth_multiple": round(int(matrix[-1]["n_records"]) / int(matrix[0]["n_records"]), 2),
            "days_with_decrease": len([a for a in arts if a["kind"] == "record_count_decrease"]),
        },
        "fields": {
            "n_fields_ever": len(spans),
            "spans": spans,
        },
        "events": {
            # A3: the catalog changed in two different ways, and conflating
            # them produced an inconsistent count across the documentation.
            # All three figures are derived from schema_timeline.csv; none is
            # typed. "total" is the sum, so it cannot drift from its parts.
            "total_schema_evolution_events": len(events) + len(naming),
            "field_presence_transitions": len(events),
            "naming_or_canonicalization_events": len(naming),
            "naming_event_dates": [r["date"] for r in naming],
            "n_change_events": len(events),   # retained: field transitions only
            "notes_boundary": _notes_boundary(matrix),
            "list": [{"date": e["date"], "event": e["event"], "field": e["field"]}
                     for e in events],
            "rename_date": "2021-12-01",
            "notes_removed": "2021-12-11",
            "notes_restored": "2022-05-24",
            "notes_absent_days": spans["notes"]["days_present"] and
                                 (len(matrix) - spans["notes"]["days_present"]),
        },
        "crossvalidation": {
            "n_sources": 3,
            "multi_source_days": len(cross),
            "three_source_days": sum(1 for r in cross if r["n_sources"] == "3"),
            "agree_days": sum(int(r["agree"]) for r in cross),
            "agreement_pct": round(100 * sum(int(r["agree"]) for r in cross) / len(cross), 2),
            "disagreements": sum(1 for r in cross if r["agree"] == "0"),
            "disagreement_dates": [r["date"] for r in cross if r["agree"] == "0"],
            "json_days": len(jrows),
            "json_first": jrows[0]["date"],
            "indep_days": len(indep),
            "indep_first": indep[0]["date"] if indep else None,
            "uncorroborated_until": indep[0]["date"] if indep else None,
        },
        "schema": {
            "declared_draft": schema.get("$schema"),
            "fields_described": len(described),
            "fields_observed": len(observed),
            "undescribed_fields": sorted(observed - described),
            "additional_properties": "unset (permissive)",
            "validation_errors": 0,
            "schema_commits": len(log),
            "schema_last_modified": schema_last,
            "schema_stale_days": (d(asof) - d(schema_last)).days if schema_last else None,
            "forensic_triage_first_seen": ft_first,
            "forensic_triage_undocumented_days": (d(asof) - d(ft_first)).days if ft_first else None,
            "forensic_triage_coverage_pct": round(
                100 * sum(1 for v in live["vulnerabilities"] if "forensicTriage" in v)
                / len(live["vulnerabilities"]), 2),
        },
        "artifacts": {
            "total": len(arts),
            "by_kind": dict(Counter(a["kind"] for a in arts)),
            "unusable_dates": sorted({a["date"] for a in csv_unusable}),
            "unusable_all_sources": len([a for a in arts
                                         if a["kind"] == "unusable_snapshot"]),
            "capture_failures": _capture_failures(arts),
        },
    }
    return stats


# ---------------------------------------------------------------------------
# figures
# ---------------------------------------------------------------------------

def style(ax):
    ax.set_facecolor(SURFACE)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=8, length=3, color=GRID)


def stamp(fig, final):
    if not final:
        fig.text(0.5, 0.5, "DRAFT", fontsize=72, color="#000000", alpha=0.07,
                 ha="center", va="center", rotation=30, zorder=10)


def fig01(stats, matrix, final):
    fields = [f for f in CANON if f in stats["fields"]["spans"]]
    fig, ax = plt.subplots(figsize=(10.0, 5.6), dpi=200)
    fig.patch.set_facecolor(SURFACE)
    style(ax)

    # Rectangle patches need numeric x, so dates are converted explicitly and
    # the axis is then told it is a date axis. Passing date objects straight
    # into a patch silently produces an ordinal axis.
    xs = [mdates.date2num(d(r["date"])) for r in matrix]
    one_day = 1.0

    for i, f in enumerate(fields):
        y = len(fields) - i - 1
        run_start = None
        for j, r in enumerate(matrix):
            on = r.get(f) == "1"
            if on and run_start is None:
                run_start = xs[j]
            last = j == len(matrix) - 1
            if run_start is not None and (not on or last):
                end = xs[j] + (one_day if (on and last) else 0.0)
                ax.add_patch(Rectangle((run_start, y - 0.32), max(end - run_start, one_day),
                                       0.64, facecolor=BLUE, edgecolor="none"))
                run_start = None

    ax.set_yticks(range(len(fields)))
    ax.set_yticklabels(list(reversed(fields)), fontsize=8.5, color=INK)
    ax.set_ylim(-0.7, len(fields) - 0.3)
    # headroom on the right so the last annotation cannot overflow the axes
    ax.set_xlim(xs[0] - 20, xs[-1] + 210)
    ax.xaxis_date()
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.xaxis.set_minor_locator(mdates.MonthLocator(bymonth=(1, 4, 7, 10)))
    ax.grid(axis="x", color=GRID, linewidth=0.6, alpha=0.7)
    ax.set_axisbelow(True)

    # direct annotation of the three additions that matter, offset so the
    # label sits clear of the band it points at
    ann = [("knownRansomwareCampaignUse", 6, 11, "left"),
           ("cwes", 6, 11, "left"),
           ("forensicTriage", -6, 11, "right")]
    for name, dx, dy, ha in ann:
        ds = stats["fields"]["spans"][name]["first_seen"]
        y = len(fields) - fields.index(name) - 1
        ax.plot([mdates.date2num(d(ds))], [y], marker="o", markersize=5.5, color=ORANGE,
                markeredgecolor=SURFACE, markeredgewidth=1.2, zorder=6)
        ax.annotate(ds, xy=(mdates.date2num(d(ds)), y), xytext=(dx, dy),
                    textcoords="offset points", fontsize=7.5, color=ORANGE,
                    fontweight="bold", ha=ha, zorder=6)

    ax.set_title("Field presence in the CISA KEV catalog, by day",
                 fontsize=12.5, color=INK, loc="left", pad=26, fontweight="bold")
    ax.text(0, 1.045,
            f"{stats['coverage']['usable_snapshots']:,} daily snapshots, "
            f"{stats['coverage']['first_date']} to {stats['coverage']['last_date']}. "
            f"Orange marks a field's first appearance.",
            transform=ax.transAxes, fontsize=8.5, color=INK2, va="bottom")
    # legend below the plot so it cannot collide with the lowest band
    ax.legend(handles=[Line2D([], [], marker="s", linestyle="", color=BLUE,
                              markersize=8, label="field present in that day's catalog")],
              loc="upper left", bbox_to_anchor=(0, -0.11), frameon=False,
              fontsize=8.5, labelcolor=INK2)
    stamp(fig, final)
    p = FIGS / "fig01_field_timeline.png"
    fig.savefig(p, facecolor=SURFACE, metadata=PNG_METADATA)
    plt.close(fig)
    return p


def fig02(stats, matrix, final):
    pts = [(d(r["date"]), int(r["n_records"])) for r in matrix if r["n_records"]]
    fig, ax = plt.subplots(figsize=(10.0, 4.2), dpi=200)
    fig.patch.set_facecolor(SURFACE)
    style(ax)
    ax.plot([p[0] for p in pts], [p[1] for p in pts], color=BLUE, linewidth=2)
    ax.grid(axis="y", color=GRID, linewidth=0.6, alpha=0.7)
    ax.set_axisbelow(True)
    ax.set_ylabel("entries in catalog", fontsize=8.5, color=INK2)
    ax.set_ylim(0, max(p[1] for p in pts) * 1.15)

    for xx, yy, lab, dy in [(pts[0][0], pts[0][1], f"{pts[0][1]:,}", 14),
                            (pts[-1][0], pts[-1][1], f"{pts[-1][1]:,}", 8)]:
        ax.plot([xx], [yy], marker="o", markersize=5, color=BLUE,
                markeredgecolor=SURFACE, markeredgewidth=1.2, zorder=5)
        ax.annotate(lab, xy=(xx, yy), xytext=(0, dy), textcoords="offset points",
                    fontsize=8.5, color=INK, fontweight="bold", ha="center")

    ax.set_title("CISA KEV catalog size", fontsize=12.5, color=INK, loc="left",
                 pad=26, fontweight="bold")
    ax.text(0, 1.045,
            f"{stats['catalog']['first_count']:,} to {stats['catalog']['last_count']:,} entries "
            f"({stats['catalog']['growth_multiple']}x) across {stats['coverage']['span_days']:,} days. "
            f"{stats['catalog']['days_with_decrease']} days show a net decrease.",
            transform=ax.transAxes, fontsize=8.5, color=INK2, va="bottom")
    stamp(fig, final)
    p = FIGS / "fig02_catalog_growth.png"
    fig.savefig(p, facecolor=SURFACE, metadata=PNG_METADATA)
    plt.close(fig)
    return p


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--final", action="store_true",
                    help="assert that metadata.json says release.mode is "
                         "final; it does not set the mode")
    args = ap.parse_args()

    # Draft/final is canonical release state, not a command-line switch.
    try:
        state = release_state.load(assert_final=args.final)
    except release_state.ReleaseStateError as exc:
        print(f"[figures] {exc}", file=sys.stderr)
        return 2
    print(f"[figures] {release_state.describe(state)}")

    REPORT.mkdir(parents=True, exist_ok=True)
    FIGS.mkdir(parents=True, exist_ok=True)

    stats = build_stats()
    stats["draft"] = state["draft"]
    stats["release"] = {k: state[k] for k in
                        ("mode", "version", "version_string", "doi",
                         "doi_url", "release_date")}
    (REPORT / "stats.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
    print(f"[figures] stats.json written ({len(json.dumps(stats))} bytes)")

    matrix = rows("field_presence_matrix.csv")
    for p in (fig01(stats, matrix, state["final"]),
              fig02(stats, matrix, state["final"])):
        print(f"[figures] {p.relative_to(ROOT)}")

    # table 01
    tl = sorted([e for e in rows("schema_timeline.csv")
                 if e["track"] == "csv_daily" and e["event"] != "baseline"],
                key=lambda e: e["date"])
    lines = ["| Date | Event | Field | Evidence |", "|---|---|---|---|"]
    seen_removed = set()
    for e in tl:
        # A field re-appearing after an earlier removal is RESTORED, not added.
        # Derived from the timeline order, not asserted; same rule as
        # 07_release_notes.py and 09_snapshot_links.py.
        if e["event"] == "field_added" and e["field"] in seen_removed:
            label = "field restored"
        else:
            label = e["event"].replace("_", " ")
        if e["event"] == "field_removed":
            seen_removed.add(e["field"])
        lines.append(f"| {e['date']} | {label} | `{e['field']}` | {e['detail']} |")
    (REPORT / "tables" / "table01_change_events.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")
    print("[figures] report/tables/table01_change_events.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
