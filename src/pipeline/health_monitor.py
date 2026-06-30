"""
health_monitor.py - Checks that each data source is reachable and working
before the pipeline runs.

This prevents the pipeline from silently collecting 0 records because a
site changed its HTML structure or went offline. Results are saved to
reports/source_health.json so the issue can be investigated.
"""

import json
import logging
import os
from datetime import date

from bs4 import BeautifulSoup
from src.collectors.base import get_session, safe_get

log = logging.getLogger(__name__)

SOURCES = [
    {
        "name": "Expertise.com",
        "url": "https://www.expertise.com/business/digital-marketing-agencies/illinois/chicago",
        "required_selectors": ["h2", "h3"],
        "min_cards": 3,
        "is_json": False,
    },
    {
        "name": "Chicago Open Data API",
        "url": "https://data.cityofchicago.org/resource/r5kz-chrr.json?$limit=1&$where=upper(business_activity) LIKE '%25MARKETING%25'",
        "required_selectors": [],
        "min_cards": 1,
        "is_json": True,
    },
]


def check_source(session, source):
    result = {
        "name": source["name"],
        "url": source["url"],
        "date_checked": date.today().isoformat(),
        "reachable": False,
        "card_count": 0,
        "healthy": False,
        "issues": [],
    }

    response = safe_get(session, source["url"])

    if response is None:
        result["issues"].append("Source unreachable or request failed.")
        return result

    result["reachable"] = True

    if source["is_json"]:
        try:
            data = response.json()
            result["card_count"] = len(data) if isinstance(data, list) else 0
            if result["card_count"] < source["min_cards"]:
                result["issues"].append(f"API returned {result['card_count']} records, expected at least {source['min_cards']}.")
            else:
                result["healthy"] = True
        except Exception as e:
            result["issues"].append(f"Failed to parse JSON response: {e}")
        return result

    soup = BeautifulSoup(response.text, "html.parser")
    for selector in source["required_selectors"]:
        count = len(soup.select(selector))
        if count == 0:
            result["issues"].append(f"Selector '{selector}' found no matches - page structure may have changed.")

    if source["required_selectors"]:
        result["card_count"] = len(soup.select(source["required_selectors"][0]))

    if result["card_count"] < source["min_cards"]:
        result["issues"].append(f"Only {result['card_count']} cards found, expected at least {source['min_cards']}.")

    result["healthy"] = len(result["issues"]) == 0
    return result


def run_health_check():
    session = get_session()
    results = []

    for source in SOURCES:
        log.info("Health check: %s", source["name"])
        result = check_source(session, source)
        results.append(result)

        if result["healthy"]:
            log.info("  OK - %s (%d records found)", source["name"], result["card_count"])
        else:
            log.warning("  FAILED - %s: %s", source["name"], result["issues"])

    os.makedirs("reports", exist_ok=True)
    with open("reports/source_health.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    log.info("Health report saved -> reports/source_health.json")
    return results
