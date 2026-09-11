<!-- GENERATED FILE — do not edit by hand.
     Written by code/09_snapshot_links.py from the pinned commit in
     data/raw/source_pins.json and the events in
     data/processed/schema_timeline.csv. -->

# Snapshot links for hand-verification

Each link addresses an **immutable commit**, not a branch, so it shows the
exact bytes this build read and will keep doing so.

Repository: `hrbrmstr/cisa-known-exploited-vulns`  
Pinned commit: `3e428ceaa1e18ce466db17c8b4c23f5a23e53c92`

> The `main` branch does not exist in this repository — its default branch
> is `batman`. Links built on a branch name are both wrong here and mutable
> in general, which is why every link below is pinned to the commit.

Open the link and read **the first line only**: it lists the column names.

## What NOT to count, and why

These checks are about the **header**, not the number of rows. Do not try
to establish a record count from the browser:

- Searching the page for `CVE-` does not give a row count. That string
  also occurs inside `shortDescription` and `notes` text, so the match
  count exceeds the number of records.
- A rendered line count is not a record count either. A quoted CSV field
  may contain an embedded newline, so one record can span several lines.

Record counts in this project come from parsing the CSV with a real CSV
reader in `code/02_build.py`, and are reported as machine-verified rather
than author-verified. Verifying a header by eye is reliable; counting rows
by eye is not, and the two should not be recorded as the same kind of
evidence.

## Check 1 — 2021-11-12: first snapshot in the archive

- [ ] header in human-readable labels, beginning `CVE,Vendor/Project`  
      https://github.com/hrbrmstr/cisa-known-exploited-vulns/blob/3e428ceaa1e18ce466db17c8b4c23f5a23e53c92/docs/2021-11-12-cisa-kev.csv

## Check 2 — 2021-12-01: naming/canonicalization event

- [ ] header now begins `cveID,vendorProject` — the same fields, renamed  
      https://github.com/hrbrmstr/cisa-known-exploited-vulns/blob/3e428ceaa1e18ce466db17c8b4c23f5a23e53c92/docs/2021-12-01-cisa-kev.csv

## Check 3 — 2021-12-11: `notes` removed

- [ ] **2021-12-11** — `notes` is NOT in the header  
      https://github.com/hrbrmstr/cisa-known-exploited-vulns/blob/3e428ceaa1e18ce466db17c8b4c23f5a23e53c92/docs/2021-12-11-cisa-kev.csv
- [ ] **2021-12-10** (the preceding snapshot) — `notes` IS in the header  
      https://github.com/hrbrmstr/cisa-known-exploited-vulns/blob/3e428ceaa1e18ce466db17c8b4c23f5a23e53c92/docs/2021-12-10-cisa-kev.csv

## Check 4 — 2022-05-24: `notes` restored after removal

- [ ] **2022-05-24** — `notes` IS in the header  
      https://github.com/hrbrmstr/cisa-known-exploited-vulns/blob/3e428ceaa1e18ce466db17c8b4c23f5a23e53c92/docs/2022-05-24-cisa-kev.csv
- [ ] **2022-05-23** (the preceding snapshot) — `notes` is NOT in the header  
      https://github.com/hrbrmstr/cisa-known-exploited-vulns/blob/3e428ceaa1e18ce466db17c8b4c23f5a23e53c92/docs/2022-05-23-cisa-kev.csv

## Check 5 — 2023-10-12: `knownRansomwareCampaignUse` first present

- [ ] **2023-10-12** — `knownRansomwareCampaignUse` IS in the header  
      https://github.com/hrbrmstr/cisa-known-exploited-vulns/blob/3e428ceaa1e18ce466db17c8b4c23f5a23e53c92/docs/2023-10-12-cisa-kev.csv
- [ ] **2023-10-11** (the preceding snapshot) — `knownRansomwareCampaignUse` is NOT in the header  
      https://github.com/hrbrmstr/cisa-known-exploited-vulns/blob/3e428ceaa1e18ce466db17c8b4c23f5a23e53c92/docs/2023-10-11-cisa-kev.csv

## Check 6 — 2024-06-26: `cwes` first present

- [ ] **2024-06-26** — `cwes` IS in the header  
      https://github.com/hrbrmstr/cisa-known-exploited-vulns/blob/3e428ceaa1e18ce466db17c8b4c23f5a23e53c92/docs/2024-06-26-cisa-kev.csv
- [ ] **2024-06-25** (the preceding snapshot) — `cwes` is NOT in the header  
      https://github.com/hrbrmstr/cisa-known-exploited-vulns/blob/3e428ceaa1e18ce466db17c8b4c23f5a23e53c92/docs/2024-06-25-cisa-kev.csv

## Check 7 — 2026-09-01: `forensicTriage` first present

- [ ] **2026-09-01** — `forensicTriage` IS in the header  
      https://github.com/hrbrmstr/cisa-known-exploited-vulns/blob/3e428ceaa1e18ce466db17c8b4c23f5a23e53c92/docs/2026-09-01-cisa-kev.csv
- [ ] **2026-08-31** (the preceding snapshot) — `forensicTriage` is NOT in the header  
      https://github.com/hrbrmstr/cisa-known-exploited-vulns/blob/3e428ceaa1e18ce466db17c8b4c23f5a23e53c92/docs/2026-08-31-cisa-kev.csv

## Check 8 — a date of your own choosing

- [ ] Pick any date in range not listed above. Open
      `https://github.com/hrbrmstr/cisa-known-exploited-vulns/blob/3e428ceaa1e18ce466db17c8b4c23f5a23e53c92/docs/YYYY-MM-DD-cisa-kev.csv`
      with your date substituted, read the header, then find that date's row
      in `data/processed/field_presence_matrix.csv` and confirm the columns
      marked `1` match the header you just read.

## If a link does not load

GitHub's file view occasionally rate-limits. The same bytes are served
without the web interface at:

`https://raw.githubusercontent.com/hrbrmstr/cisa-known-exploited-vulns/3e428ceaa1e18ce466db17c8b4c23f5a23e53c92/docs/YYYY-MM-DD-cisa-kev.csv`

## Link verification

Checked automatically before this file was written. Each snapshot
was confirmed twice: the object exists in the pinned commit, and a
live fetch returned HTTP 200. A deliberately invalid date was used
as a control and correctly returned 404.

| Date | Object in pinned commit | HTTP |
|---|---|---|
| 2021-11-12 | present | 200 |
| 2021-12-01 | present | 200 |
| 2021-12-10 | present | 200 |
| 2021-12-11 | present | 200 |
| 2022-05-23 | present | 200 |
| 2022-05-24 | present | 200 |
| 2023-10-11 | present | 200 |
| 2023-10-12 | present | 200 |
| 2024-06-25 | present | 200 |
| 2024-06-26 | present | 200 |
| 2026-08-31 | present | 200 |
| 2026-09-01 | present | 200 |
