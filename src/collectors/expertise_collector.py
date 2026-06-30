"""
Collector: Expertise.com - Chicago Digital Marketing Agencies.

Expertise.com publishes curated lists of local agencies with names and
short descriptions. Pages are static HTML and publicly accessible.
We scrape three category pages to get a wider range of agencies.

Note: phone numbers and direct websites are rarely shown on these listing
pages - agency descriptions are the main content. Records with no phone or
email still get exported; the operations team can use the listing page URL
to look up contact details manually if needed.
"""

import re
import logging
from bs4 import BeautifulSoup
from src.collectors.base import get_session, safe_get, TODAY

log = logging.getLogger(__name__)

SOURCE_NAME = "Expertise.com"

PAGES = [
    "https://www.expertise.com/business/digital-marketing-agencies/illinois/chicago",
    "https://www.expertise.com/business/social-media-marketing/illinois/chicago",
    "https://www.expertise.com/business/marketing-consultants/illinois/chicago",
]


def parse_page(html, page_url):
    soup = BeautifulSoup(html, "html.parser")
    records = []

    # Agency entries are typically headed by an h2 or h3 tag with the
    # company name, followed by a description paragraph.
    headings = soup.select("h2, h3")

    for heading in headings:
        name = heading.get_text(strip=True)

        # Skip generic page headings that are not business names
        if not name or len(name) < 3 or len(name) > 80:
            continue
        skip_words = ("best", "faq", "resources", "how we", "methodology", "more")
        if any(word in name.lower() for word in skip_words):
            continue

        record = {
            "business_name": name,
            "business_category": "Digital Marketing Agency",
            "website": None,
            "phone": None,
            "email": None,
            "address": None,
            "city": "Chicago",
            "state": "Illinois",
            "zip_code": None,
            "country": "United States",
            "rating": None,
            "review_count": None,
            "source_name": SOURCE_NAME,
            "source_url": page_url,
            "date_collected": TODAY,
            "notes": None,
        }

        # Look for a website link near this heading (in the same parent block)
        parent = heading.find_parent()
        if parent:
            for a in parent.find_all("a", href=True):
                href = a["href"]
                if href.startswith("http") and "expertise.com" not in href:
                    record["website"] = href
                    break

            # Look for a phone number in the surrounding text
            text = parent.get_text()
            match = re.search(r"\(?\d{3}\)?[\s.\-]\d{3}[\s.\-]\d{4}", text)
            if match:
                record["phone"] = match.group()

        records.append(record)

    return records


def collect():
    session = get_session()
    all_records = []

    for url in PAGES:
        log.info("Expertise.com - fetching %s", url)
        response = safe_get(session, url)

        if response is None:
            log.warning("Expertise.com - skipping %s (no response)", url)
            continue

        records = parse_page(response.text, url)
        log.info("Expertise.com - got %d records from %s", len(records), url)
        all_records.extend(records)

    log.info("Expertise.com - done. Total: %d records.", len(all_records))
    return all_records
