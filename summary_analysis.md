# Summary Analysis Report

**Category:** Digital Marketing Agencies
**Location:** Chicago, Illinois, United States
**Date:** 2026-06-30

---

## 1. Collection Overview

| Metric | Value |
|---|---|
| Total raw records collected | 506 |
| Sources used | Expertise.com, City of Chicago Open Data |
| Records after cleaning | 506 |
| Duplicates removed | 305 |
| Low-quality records removed | 0 |
| **Total valid final records** | **201** |

Source breakdown of raw collection:

| Source | Records |
|---|---|
| Expertise.com | 206 |
| City of Chicago Open Data | 300 |

---

## 2. Data Completeness

| Field | Coverage |
|---|---|
| Website present | 21.9% |
| Phone number present | 1.5% |
| Email address present | 0.0% |
| Confirmed by 2 sources | 42.3% |

---

## 3. Quality Score Distribution

- **Average quality score:** 28.9 / 100

Scores are low overall because neither source publishes phone or email
directly, which together account for 40 of the 100 possible points. Most
records score in the 10-40 range, earning points mainly for a valid
business name, complete location, and (where available) a valid website
or multi-source confirmation.

---

## 4. Recommended Contact Method Distribution

| Method | Records | % |
|---|---|---|
| No Reliable Contact Method | 156 | 77.6% |
| Website Contact Form | 42 | 20.9% |
| Phone | 3 | 1.5% |
| Email / Multiple Methods | 0 | 0.0% |

This distribution directly reflects the limitation of the two sources used:
neither publishes email addresses, and only a handful of phone numbers
appear in the raw Expertise.com listings (and on inspection, some of those
came from the directory's own contact footer rather than an individual
agency).

---

## 5. Duplicate Detection Results

- **305 duplicates removed** out of 506 raw records (60.3%)
- The high duplicate rate comes mainly from the City of Chicago Open Data
  source, where the same business can appear multiple times under
  different license records (renewals, amendments, multiple license types
  for the same address).
- Detection methods used, in order: same website domain, same phone
  number, same email, then fuzzy business name + city match (90%+
  similarity).
- All removed duplicates are saved in `data/rejected/rejected_<date>.csv`
  with a `duplicate_of` column showing which record they matched.

---

## 6. Main Data Quality Problems Identified

1. **No phone or email coverage from either source.** Both Expertise.com
   and Chicago Open Data are directory/registry-style sources that do not
   expose direct contact details on the page being scraped. See the
   "Why Phone and Email Coverage Is Low" section in the README for the
   full explanation.
2. **High duplicate rate from Chicago Open Data (60%+).** The same legal
   business entity can hold multiple license records over time (renewals,
   amendments), which inflates the raw record count before deduplication.
3. **A small number of false-positive business names from Expertise.com.**
   Because the parser scans heading tags, a handful of footer/navigation
   text occasionally gets picked up as a fake "agency." These records score
   very low (10-20 points) and sort to the bottom of the final CSV, so
   their impact on the usable dataset is minimal but not zero.
4. **Website-only contactability for most valid records.** With phone and
   email largely unavailable, "Website Contact Form" is the most common
   recommended method after "No Reliable Contact Method" - meaning the
   operations team will need to manually visit the website to find a
   direct contact in many cases.

---

## 7. Problem-Solving Scenario: Source Structure Change

> *Scenario: A source changes its HTML structure and the scraper stops
> finding expected fields.*

**1. Identify the cause** - The health monitor checks expected selectors
on the first page before every run and logs a warning if the selector
count drops to zero or below the expected minimum.

**2. Prevent the entire pipeline from failing** - Each collector uses
`safe_get()`, which returns `None` on any request error instead of raising.
A failure on one page (as happened twice with Expertise.com 404s during
development) does not stop the rest of the collection.

**3. Detect that data quality has dropped** - The pipeline reports
`pct_with_website`, `pct_with_phone`, and `pct_with_email` in its summary
stats. A sudden unexplained drop in any of these is an immediate signal,
as seen in this run where phone/email coverage was already near zero and
clearly tied to source limitations rather than a scraper bug.

**4. Update the scraper safely** - Inspect the live page structure, update
the relevant selector or URL in the collector file, then re-run with
`--cached` against previously saved raw data to confirm the cleaning and
scoring logic still behaves correctly before doing a fresh live run.

**5. Prevent incorrect empty data from reaching operations** - The
`website_valid`, `phone_valid` flags are always set explicitly. Records
with missing contact info still export with a clear
`recommended_contact_method` of "No Reliable Contact Method" rather than
silently appearing as if they had no data at all - so operations always
knows which records are and are not actionable.

---

## 8. Challenges Faced (see also README)

- YellowPages blocked all automated requests (403), forcing a source swap
  to Expertise.com mid-development.
- Expertise.com's URL structure changed from what was initially assumed,
  requiring a search for the live page and a URL correction.
- Chicago Open Data does not have a phone field at all; an early version
  of the collector incorrectly assumed one existed.
- Heading-based HTML parsing on Expertise.com occasionally captures
  non-agency text as a false record; this is a known and documented
  limitation rather than a silent failure, since these records score very
  low and are visibly separated by quality score in the final CSV.

---


