# Public Business Data Acquisition and Quality Pipeline

**Category:** Digital Marketing Agencies
**Location:** Chicago, Illinois, United States

---

## What This Project Does

This pipeline collects publicly available business information about digital
marketing agencies in Chicago, cleans and organizes it, removes duplicates,
scores each record by quality, and produces a final dataset that an operations
team can use to reach out to businesses directly.

---

## Data Sources

I evaluated 7 possible sources and selected 2. The full evaluation is in
`data/source_assessment.csv`.

| Source | Selected | Reason |
|---|---|---|
| Expertise.com | Yes | Static HTML, publicly accessible, has phone and website data |
| Chicago Open Data API | Yes | Official government API, no scraping concerns |
| YellowPages | No | Returns 403 Forbidden to scrapers (tested during development) |
| Yelp | No | Terms of service explicitly prohibit scraping |
| Google Maps/Places API | No | Requires a paid API key for more than a handful of results |
| LinkedIn | No | Requires login, automated access violates their terms |

---

## Tech Stack

- **Python 3.12**
- **requests** - making HTTP requests
- **BeautifulSoup4** - parsing HTML pages
- **pandas** - cleaning data and exporting CSVs
- **phonenumbers** - validating and formatting phone numbers
- **fuzzywuzzy** - fuzzy name matching for duplicate detection
- **pytest** - running automated tests

---

## Project Structure

```
project/
├── data/
│   ├── raw/                          # Raw JSON saved after collection
│   ├── processed/                    # Cleaned JSON
│   ├── rejected/                     # Duplicates and low quality records
│   ├── final/                        # Final CSV ready for the operations team
│   └── source_assessment.csv         # Source evaluation table (Task 1)
├── src/
│   ├── collectors/
│   │   ├── base.py                   # Shared session, delays, error handling
│   │   ├── expertise_collector.py    # Scrapes Expertise.com listings
│   │   └── chicago_opendata_collector.py  # Pulls from Chicago Open Data API
│   ├── cleaning/
│   │   └── normalizer.py             # Cleans names, URLs, phones, emails, locations
│   ├── matching/
│   │   └── deduplicator.py           # Finds and merges duplicate records
│   ├── scoring/
│   │   └── scorer.py                 # Scores each record and assigns contact method
│   └── pipeline/
│       ├── runner.py                 # Runs all steps in order and saves outputs
│       └── health_monitor.py         # Checks sources are working before collection
├── tests/
│   └── test_pipeline.py              # 39 automated tests
├── reports/
│   └── summary_analysis.md           # Summary of results and data quality
├── main.py                           # Run this to start the pipeline
└── requirements.txt
```

---

## Setup

```bash
cd project
pip install -r requirements.txt
```

---

## How to Run

```bash
# Normal run - scrapes live data from both sources
python main.py

# Skip the health check and go straight to collecting
python main.py --no-health

# Reuse raw data from a previous run without scraping again
python main.py --cached
```

### Run the tests
```bash
python -m pytest tests/test_pipeline.py -v
```

---

## Data Cleaning Rules

| Field | What was done |
|---|---|
| Business name | Removed extra spaces; converted ALL-CAPS names to Title Case |
| Website | Added https:// where missing; stripped tracking params like utm_source, fbclid; removed trailing slashes; lowercased the domain |
| Phone | Parsed and formatted to E.164 standard (e.g. +13125550100); flagged invalid numbers |
| Email | Converted to lowercase; removed spaces; validated format; flagged generic addresses like info@ and contact@ |
| City / State | Removed extra spaces; applied Title Case |

---

## How Duplicates Were Detected

Matching was done using multiple fields, applied in this order:

1. Same website domain (after stripping www.)
2. Same phone number (after formatting to E.164)
3. Same email address
4. Business name similarity 90% or higher and same city (fuzzy matching)

When duplicates were found, the record with the most complete information
was kept as the primary. Any missing fields were filled in from the duplicate.
All removed duplicates are saved to `data/rejected/rejected_<date>.csv` with
a `duplicate_of` column explaining which record they matched.

---

## Quality Scoring (0-100)

| Criterion | Points |
|---|---|
| Business name present | 10 |
| Valid website | 20 |
| Valid phone number | 20 |
| Valid email address | 20 |
| City and state both present | 10 |
| Confirmed by more than one source | 10 |
| Rating available | 5 |
| Review count available | 5 |
| **Maximum** | **100** |

---

## Recommended Contact Method

Each record gets a `recommended_contact_method` value based on what
contact information is available:

| Condition | Value |
|---|---|
| Has both phone and email | Multiple Methods |
| Phone only | Phone |
| Email only | Email |
| Website but no phone or email | Website Contact Form |
| Nothing available | No Reliable Contact Method |

---

## Source Health Monitor

Before every collection run, the pipeline checks that each source is
reachable and returning the expected data. If a site changes its HTML
structure and the scraper stops finding records, the health monitor
catches it early and logs a warning before any bad data gets through.

Results are saved to `reports/source_health.json` after every run.

---

## Problem-Solving Scenario

**If a source changes its page structure and phone numbers stop being collected:**

1. **Identify the cause** - the health monitor checks selector counts before
   every run, so a drop to 0 matches is flagged immediately.
2. **Prevent pipeline failure** - `safe_get()` returns `None` on any request
   error instead of raising, so one broken page does not crash the run.
3. **Detect quality drop** - the pipeline reports `pct_with_phone` in its
   summary stats; a sudden drop is an obvious signal.
4. **Update the scraper safely** - inspect the live page, update the CSS
   selector in the collector file, re-run with `--cached` to test against
   saved data first.
5. **Prevent bad data reaching operations** - the `phone_valid` flag is
   always set, so records with missing or invalid phones still export
   correctly and the contact method falls back to email or website.

---

## Why Phone and Email Coverage Is Low

After running the pipeline live, phone number coverage came out to 1.5% and
email coverage to 0%. This is expected, not a bug:

- **Expertise.com** lists agency names and short descriptions. It does not
  publish direct phone numbers or emails for most agencies on the listing
  page itself — that information sits behind each agency's own website,
  which is one click away but outside the scope of what this scraper reads.
  A handful of phone numbers do appear (8 out of 506 raw records), but on
  inspection some of these came from Expertise.com's own contact footer
  rather than the individual agency, so they were treated as unreliable.
- **Chicago Open Data** is a government license registry. It records legal
  name, address, and license status — it was never designed to hold contact
  information, so it has no phone, email, or website field at all.

In short: phone numbers and email addresses are personal/business contact
details that most public directories do not expose directly in their HTML.
Getting them reliably would require visiting each agency's own website and
parsing its contact page individually, which is listed under "What I Would
Build Next" below.

Website coverage (21.9%) is the most complete and reliable contactability
signal this dataset can offer, which is why `recommended_contact_method`
falls back to "Website Contact Form" for most valid records.

---

## Challenges Faced

1. **Expertise.com changed its URL structure.** The original URLs
   (`/il/chicago/digital-marketing`) returned 404. The working URLs follow
   the pattern `/business/<category>/illinois/chicago`. This was found by
   searching for the live page and confirming the correct path.

2. **Chicago Open Data has no contact fields.** An early version of the
   collector assumed a `contact_phone` field existed and silently returned
   `None` for every record. Inspecting the dataset's actual schema showed
   the field does not exist in this dataset at all, so the collector was
   rewritten to use only the fields that are genuinely present (name,
   address, city, state, zip, license status).

- Expertise.com listing pages mostly contain agency names and descriptions; phone numbers and direct websites are not always present in the page text, so a meaningful share of records only have a name and city.
- Chicago Open Data has no phone, website, or email fields at all - it only confirms business name, address, and license status. It is used as a second source to cross-check and add address detail, not for direct contact info.
- Fuzzy matching at 90% similarity catches most duplicates but may miss heavily abbreviated or reordered names.

---

## Responsible Data Collection

- Only publicly available business information was collected.
- All scrapers use a 2-second delay between requests.
- No logins, CAPTCHAs, or paywalls were bypassed.
- The Chicago Open Data API is used under the City of Chicago open data license.
- No personal consumer data was collected at any point.

---

## What I Would Build Next

- A contact page crawler to find emails directly from each agency's website
- Incremental updates so only stale records get re-collected
- An alert system (email or Slack) when the health monitor finds a broken source
- A simple dashboard to visualize quality scores and source coverage

---

## Time Breakdown

| Task | Time |
|---|---|
| Source research and evaluation | 1 hr |
| Writing the two collectors | 1.5 hr |
| Cleaning and normalization | 1 hr |
| Duplicate detection | 1 hr |
| Scoring and contact method logic | 30 min |
| Pipeline orchestrator and CLI | 30 min |
| Tests | 1 hr |
| README and summary report | 1.5 hr |
| **Total** | **8 hr** |
