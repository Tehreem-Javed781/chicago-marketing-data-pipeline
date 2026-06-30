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



