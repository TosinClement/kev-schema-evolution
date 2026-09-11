#!/usr/bin/env python3
"""
negative_release_tests.py — prove the release-state checks actually fail.

A check that has never been seen to fail is not evidence. Every gate added for
the Option B release-state work is exercised here against a deliberately broken
copy of the project, and the test asserts the specific failure, not merely a
non-zero exit.

Nothing here touches the working tree. Each case runs in a throwaway copy with
`sources/` symlinked, and the copy is deleted afterwards. No network, no
deposit, no publication: the "release" simulated here uses an obviously
non-existent test DOI and never leaves the temporary directory.

Usage:
    python code/tests/negative_release_tests.py
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PY = sys.executable

# Obviously fake, and never written to the real repository.
TEST_DOI = "10.5281/zenodo.9999999"
TEST_DATE = "2026-09-11"

results: list[tuple[str, bool, str]] = []


def log(s: str = "") -> None:
    print(s)
    LOG_LINES.append(s)


LOG_LINES: list[str] = []


def make_copy(tmp: Path) -> Path:
    dst = tmp / "repo"
    shutil.copytree(
        ROOT, dst,
        ignore=shutil.ignore_patterns("sources", "venv", "__pycache__",
                                      ".git", "*.pyc"))
    (dst / "sources").symlink_to(ROOT / "sources")
    return dst


def set_state(repo: Path, **kw) -> None:
    p = repo / "metadata.json"
    m = json.loads(p.read_text())
    m["release"].update(kw)
    p.write_text(json.dumps(m, indent=2) + "\n", encoding="utf-8")


def run(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([PY, *args], cwd=repo, capture_output=True,
                          text=True)


def gate(repo: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PY, "code/06_publish_gate.py", ".",
         "--allow-draft-in", "code/", "docs/VERIFY_CHECKLIST.md",
         "docs/BUILD_SPEC.md", "docs/PUBLISH_GUIDE.md"],
        cwd=repo, capture_output=True, text=True)


def check(name: str, ok: bool, detail: str = "") -> None:
    results.append((name, ok, detail))
    log(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if detail:
        log(f"        {detail}")


def regenerate_final(repo: Path) -> None:
    """Simulate a release build in the copy: set the state final and rebuild
    every generated artifact except the PDF (which needs wkhtmltopdf and is not
    what these checks read)."""
    set_state(repo, mode="final", doi=TEST_DOI, release_date=TEST_DATE)
    for stage in ("code/04_figures.py", "code/00_metadata.py",
                  "code/07_release_notes.py", "code/08_render_docs.py",
                  "code/10_cisa_issue.py", "code/05_document.py",
                  "code/03_qa.py"):
        r = run(repo, stage)
        if r.returncode != 0:
            raise RuntimeError(f"{stage} failed in the simulated release: "
                               f"{r.stderr.strip()[:400]}")


def main() -> int:
    # The simulated release in cases D-F regenerates figures and statistics,
    # which read the pinned clones. Without them the tests fail for a reason
    # that has nothing to do with the release state, which is exactly the
    # confusing failure this guard replaces (seen in clean room C, where the
    # tests ran before the pipeline had fetched anything).
    if not (ROOT / "sources").exists():
        print("negative tests: sources/ is missing. Run `python "
              "code/01_fetch.py` (or the full pipeline) first — the simulated "
              "release rebuilds statistics from the pinned clones.",
              file=sys.stderr)
        return 2

    log("=" * 72)
    log("NEGATIVE TESTS — release-state gates (Option B)")
    log("Each case breaks the release state or a generated artifact on purpose")
    log("and asserts the specific failure. Simulated release DOI: "
        f"{TEST_DOI} (fake, temporary copy only).")
    log("=" * 72)
    log()

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)

        # ---- A. the build refuses to run in final mode without the facts ----
        log("A. FINAL MODE REFUSES INCOMPLETE RELEASE STATE")
        cases = [
            ("doi unset", dict(mode="final", doi=None,
                               release_date=TEST_DATE),
             "release.doi is not set"),
            ("doi is a placeholder", dict(mode="final",
                                          doi="10.5281/zenodo.XXXXXXX",
                                          release_date=TEST_DATE),
             "placeholder"),
            ("doi malformed", dict(mode="final", doi="zenodo-9999999",
                                   release_date=TEST_DATE),
             "well-formed DOI"),
            ("release date unset", dict(mode="final", doi=TEST_DOI,
                                        release_date=None),
             "release.release_date is not set"),
            ("release date malformed", dict(mode="final", doi=TEST_DOI,
                                            release_date="2026-9-1"),
             "YYYY-MM-DD"),
            ("release date is a placeholder",
             dict(mode="final", doi=TEST_DOI, release_date="[RELEASE_DATE]"),
             "YYYY-MM-DD"),
        ]
        for label, state, needle in cases:
            repo = make_copy(tmp)
            try:
                set_state(repo, **state)
                r = run(repo, "code/00_metadata.py")
                blocked = r.returncode != 0 and needle in r.stderr
                check(f"A{cases.index((label, state, needle)) + 1}. "
                      f"build refuses: {label}", blocked,
                      "" if blocked else
                      f"rc={r.returncode} stderr={r.stderr.strip()[:200]!r}")
            finally:
                shutil.rmtree(repo)
        log()

        # ---- B. --final cannot override the canonical state ----------------
        log("B. --final IS AN ASSERTION, NOT A SWITCH")
        repo = make_copy(tmp)
        try:
            r = run(repo, "code/04_figures.py", "--final")
            ok = r.returncode != 0 and "release.mode is 'draft'" in r.stderr
            check("B1. --final on a draft state refuses to build", ok,
                  "" if ok else f"rc={r.returncode} stderr={r.stderr[:200]!r}")
            stats = json.loads((repo / "report" / "stats.json").read_text())
            check("B2. stats.json was not switched to final by the flag",
                  stats.get("draft") is True,
                  f"draft={stats.get('draft')}")
        finally:
            shutil.rmtree(repo)
        log()

        # ---- C. a draft build is refused by the gate, and carries no DOI ----
        log("C. DRAFT BUILDS ARE NOT PUBLISHABLE")
        repo = make_copy(tmp)
        try:
            g = gate(repo)
            ok = g.returncode != 0 and "release.mode is 'draft'" in g.stdout
            check("C1. gate blocks a draft build", ok,
                  "" if ok else g.stdout[-200:])
            readme = repo / "README.md"
            readme.write_text(readme.read_text().replace(
                "> Data cutoff", f"> DOI {TEST_DOI}\n> Data cutoff"))
            g = gate(repo)
            ok = "DOI present in a draft build" in g.stdout
            check("C2. gate blocks a DOI that appears in a draft build", ok,
                  "" if ok else g.stdout[-200:])
        finally:
            shutil.rmtree(repo)
        log()

        # ---- D. a correct simulated release clears the gate -----------------
        log("D. A CORRECT RELEASE STATE CLEARS THE GATE")
        repo = make_copy(tmp)
        try:
            regenerate_final(repo)
            g = gate(repo)
            ok = g.returncode == 0 and "gate: clear" in g.stdout
            check("D1. simulated release passes the gate", ok,
                  "" if ok else g.stdout[-400:])
            readme = (repo / "README.md").read_text()
            check("D2. README banner shows released status and the DOI",
                  "STATUS: released" in readme and TEST_DOI in readme)
            check("D3. README carries the Zenodo DOI badge",
                  f"zenodo.org/badge/DOI/{TEST_DOI}.svg" in readme)
            cff = (repo / "CITATION.cff").read_text()
            check("D4. CITATION.cff carries the DOI and the release date",
                  f'doi: "{TEST_DOI}"' in cff
                  and f'date-released: "{TEST_DATE}"' in cff)
            rep = (repo / "report" / "kev_schema_evolution.md").read_text()
            check("D5. report first page carries the DOI",
                  TEST_DOI in rep.split("## Abstract")[0])
            check("D6. report DRAFT banner is gone",
                  "DRAFT — NOT RELEASED" not in rep)
            issue = (repo / "docs" / "CISA_ISSUE.md").read_text()
            check("D7. CISA issue text carries the DOI and no placeholder",
                  TEST_DOI in issue and "[Zenodo DOI]" not in issue
                  and "Not ready to file" not in issue)
        finally:
            shutil.rmtree(repo)
        log()

        # ---- E. tampering with any one artifact is caught -------------------
        log("E. INCONSISTENCY BETWEEN FILES IS CAUGHT")
        tamper = [
            ("E1. hand-edited README status banner", "README.md",
             lambda t: t.replace("STATUS: released", "STATUS: RELEASED"),
             "STATUS banner does not match"),
            ("E2. README left with a DRAFT status", "README.md",
             lambda t: t.replace("**STATUS: released",
                                 "**STATUS: DRAFT released"),
             "README still carries a DRAFT status"),
            ("E3. DOI in CITATION.cff disagrees", "CITATION.cff",
             lambda t: t.replace(TEST_DOI, "10.5281/zenodo.1111111"),
             "DOI missing or does not match"),
            ("E4. release date in CITATION.cff disagrees", "CITATION.cff",
             lambda t: t.replace(TEST_DATE, "2020-01-01"),
             "release date missing or does not match"),
            ("E5. version in CITATION.cff disagrees", "CITATION.cff",
             lambda t: t.replace('version: "0.1.0"', 'version: "0.2.0"'),
             "version missing or does not match"),
            ("E6. a second, different DOI appears in the report",
             "report/kev_schema_evolution.md",
             lambda t: t.replace("## Abstract",
                                 "DOI 10.5281/zenodo.1234567\n\n## Abstract"),
             "disagrees with the release state"),
            ("E7. the DOI is missing from the CISA issue text",
             "docs/CISA_ISSUE.md",
             lambda t: t.replace(TEST_DOI, "see the repository"),
             "release DOI absent"),
        ]
        repo = make_copy(tmp)
        try:
            regenerate_final(repo)
            pristine = {rel: (repo / rel).read_text()
                        for _, rel, _, _ in tamper}
            for label, rel, mutate, needle in tamper:
                (repo / rel).write_text(mutate(pristine[rel]))
                g = gate(repo)
                ok = g.returncode != 0 and needle in g.stdout
                check(label, ok, "" if ok else g.stdout[-300:])
                (repo / rel).write_text(pristine[rel])       # restore
            g = gate(repo)
            check("E8. gate is clear again once every file is restored",
                  g.returncode == 0, "" if g.returncode == 0 else g.stdout[-200:])
        finally:
            shutil.rmtree(repo)
        log()

        # ---- F. the placeholder patterns that used to slip through ----------
        log("F. PLACEHOLDERS THAT PREVIOUSLY EVADED THE GATE")
        repo = make_copy(tmp)
        try:
            regenerate_final(repo)
            probe = repo / "docs" / "PLACEHOLDER_PROBE.md"
            for label, text, needle in [
                ("F1. [RELEASE_DATE] is now caught",
                 'date-released: "[RELEASE_DATE]"\n',
                 "bracketed placeholder (all-caps)"),
                ("F2. [Zenodo DOI] is now caught",
                 "Full timeline and method: [Zenodo DOI]\n",
                 "bracketed DOI placeholder"),
                ("F3. [GITHUB_USERNAME] is now caught",
                 "https://github.com/[GITHUB_USERNAME]/x\n",
                 "bracketed placeholder (all-caps)"),
            ]:
                probe.write_text(text)
                g = gate(repo)
                ok = g.returncode != 0 and needle in g.stdout
                check(label, ok, "" if ok else g.stdout[-300:])
            probe.unlink()
            g = gate(repo)
            check("F4. gate is clear once the probe file is removed",
                  g.returncode == 0, "" if g.returncode == 0 else g.stdout[-200:])
        finally:
            shutil.rmtree(repo)
        log()

        # ---- G. the CSV-exclusion language cannot drift back ---------------
        # The third source's csv/ tree is excluded for two different reasons,
        # and an unconditional "its CSVs are byte-identical" claim had survived
        # in the generated QA report, in the pin description and in a source
        # comment. QA gate Q14 ties that language to the derived manifest
        # statistics; these cases prove it fails when the language drifts.
        log("G. CSV-EXCLUSION LANGUAGE (QA gate Q14)")
        repo = make_copy(tmp)
        try:
            probe = repo / "docs" / "CSV_LANGUAGE_PROBE.md"

            def q14(text_: str | None):
                if text_ is None:
                    probe.unlink(missing_ok=True)
                else:
                    probe.write_text(text_, encoding="utf-8")
                r = run(repo, "code/03_qa.py")
                return r.stdout

            for label, text_, needle in [
                ("G1. unconditional claim is rejected",
                 "Only the json/ tree is used. Its csv/ files are "
                 "byte-identical to hrbrmstr's (back-filled from them).\n",
                 "unscoped claim"),
                ("G2. scoped claim with no derived reference is rejected",
                 "For the dates before the cutover its CSVs are "
                 "byte-identical to the primary archive's.\n",
                 "no derived reference"),
                # The word CSV has to be in the sentence: the gate only
                # inspects claims about the third source's csv/ tree, not
                # every use of "byte-identical" in the project. The first
                # version of this fixture omitted it and the case passed the
                # gate, which is how that scoping rule came to be verified.
                ("G3. a wrong boundary date is rejected",
                 "For all 668 shared dates before 2022-01-01 the repository's "
                 "csv/ files are byte-identical to hrbrmstr's.\n",
                 "date disagrees with the manifest"),
            ]:
                outp = q14(text_)
                ok = needle in outp and "CSV language sound    : NO" in outp
                check(label, ok, "" if ok else outp[-300:])

            outp = q14(None)
            check("G4. gate passes again once the probe is removed",
                  "CSV language sound    : YES" in outp,
                  "" if "CSV language sound    : YES" in outp
                  else outp[-300:])

            # The original defect, reintroduced at its source: a comment in the
            # pipeline, not a document. Comments are scanned too.
            bp = repo / "code" / "02_build.py"
            pristine = bp.read_text()
            bp.write_text(pristine.replace(
                "    Only the json/ directory of this source is read.",
                "    Only the json/ directory of this source is read. Its csv/\n"
                "    directory is byte-identical to the hrbrmstr archive it was\n"
                "    back-filled from.", 1))
            outp = q14(None)
            ok = ("CSV language sound    : NO" in outp
                  and "code/02_build.py" in outp)
            check("G5. the original defect, reintroduced in a source comment, "
                  "is caught", ok, "" if ok else outp[-300:])
            bp.write_text(pristine)
            outp = q14(None)
            check("G6. gate passes again once the comment is restored",
                  "CSV language sound    : YES" in outp,
                  "" if "CSV language sound    : YES" in outp
                  else outp[-300:])
        finally:
            shutil.rmtree(repo)
        log()

    passed = sum(1 for _, ok, _ in results if ok)
    log("=" * 72)
    log(f"NEGATIVE TESTS: {passed}/{len(results)} passed")
    for name, ok, detail in results:
        if not ok:
            log(f"  FAILED: {name} — {detail[:200]}")
    log("=" * 72)

    outp = ROOT / "verification" / "logs" / "negative-release-tests.log"
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text("\n".join(LOG_LINES) + "\n", encoding="utf-8")
    print(f"\nlog written: {outp.relative_to(ROOT)}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
