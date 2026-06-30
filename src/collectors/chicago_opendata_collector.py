"""
Collector: City of Chicago Open Data - Business Licenses API.

This is an official government API that requires no authentication
and has no scraping concerns. We filter for marketing and advertising
related business licenses in Chicago.

Note: this dataset does not include phone or email - it only has
business name, address, and license details. It is used to confirm
business existence and address, and to cross-check duplicates against
the Expertise.com source.

API docs: https://data.cityofchicago.org/resource/r5kz-chrr.json
"""

import logging
from src.collectors.base import get_session, safe_get, TODAY

log = logging.getLogger(__name__)

SOURCE_NAME = "City of Chicago Open Data"
API_URL = "https://data.cityofchicago.org/resource/r5kz-chrr.json"
PAGE_SIZE = 1000
MAX_RECORDS = 300


def collect():
    session = get_session()
    all_records = []
    offset = 0

    while len(all_records) < MAX_RECORDS:
        params = {
            "$where": "upper(business_activity) LIKE '%MARKETING%' OR upper(business_activity) LIKE '%ADVERTISING%'",
            "$limit": PAGE_SIZE,
            "$offset": offset,
            "$order": "legal_name ASC",
        }

        log.info("Chicago Open Data - fetching offset %d", offset)
        response = safe_get(session, API_URL, params=params)

        if response is None:
            break

        batch = response.json()
        if not batch:
            break

        for item in batch:
            if item.get("license_status", "").upper() not in ("AAI", ""):
                continue

            name = item.get("legal_name") or item.get("doing_business_as_name")
            if not name:
                continue

            record = {
                "business_name": name,
                "business_category": "Digital Marketing Agency",
                "website": None,
                "phone": None,
                "email": None,
                "address": item.get("address"),
                "city": item.get("city", "Chicago"),
                "state": item.get("state", "IL"),
                "zip_code": item.get("zip_code"),
                "country": "United States",
                "rating": None,
                "review_count": None,
                "source_name": SOURCE_NAME,
                "source_url": API_URL,
                "date_collected": TODAY,
                "notes": item.get("business_activity"),
            }

            all_records.append(record)

        offset += PAGE_SIZE
        if len(batch) < PAGE_SIZE:
            break

    log.info("Chicago Open Data - done. Total: %d records.", len(all_records))
    return all_records[:MAX_RECORDS]
