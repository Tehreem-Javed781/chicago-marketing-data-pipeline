"""
deduplicator.py - Finds and removes duplicate business records.

A duplicate is identified by matching on any of these (in order):
  1. Same website domain (www. stripped)
  2. Same phone number (after normalization)
  3. Same email address
  4. Business name similarity >= 90% in the same city (fuzzy match)

When duplicates are found, the most complete record is kept as primary.
Any useful fields missing from the primary are filled in from the duplicate.
All removed duplicates are saved separately with a note on why they matched.
"""

import re
import logging
from urllib.parse import urlparse

try:
    from fuzzywuzzy import fuzz
    HAS_FUZZY = True
except ImportError:
    HAS_FUZZY = False

log = logging.getLogger(__name__)


def get_domain(url):
    """Extract bare domain from a URL, stripping www."""
    if not url:
        return None
    try:
        host = urlparse(url).netloc.lower()
        return re.sub(r"^www\.", "", host) or None
    except Exception:
        return None


def completeness(record):
    """Count how many key fields are filled in. Used to pick the best primary record."""
    score = 0
    for field in ("business_name", "website", "phone", "email", "city", "state"):
        if record.get(field):
            score += 1
    return score


def merge(primary, secondary):
    """Fill any empty fields in primary using values from secondary."""
    result = dict(primary)
    for field in ("website", "phone", "email", "rating", "review_count"):
        if not result.get(field) and secondary.get(field):
            result[field] = secondary[field]

    # Track that this record came from multiple sources
    sources = set((result.get("source_name") or "").split(" | "))
    new_source = secondary.get("source_name") or ""
    if new_source and new_source not in sources:
        sources.add(new_source)
    result["source_name"] = " | ".join(sorted(filter(None, sources)))

    return result


def get_match_reason(primary, secondary):
    """Explain why two records were considered duplicates."""
    if get_domain(primary.get("website")) and get_domain(primary.get("website")) == get_domain(secondary.get("website")):
        return "same website domain"
    if primary.get("phone") and primary.get("phone") == secondary.get("phone"):
        return "same phone number"
    if primary.get("email") and primary.get("email") == secondary.get("email"):
        return "same email address"
    return "similar name and same city"


def deduplicate(records):
    """
    Find and group duplicate records.
    Returns (final_records, rejected_records).
    """
    groups = []       # list of lists of record indices
    assigned = {}     # record index -> group index

    domain_index = {}
    phone_index = {}
    email_index = {}

    for i, rec in enumerate(records):
        matched_group = None

        # Check domain
        domain = get_domain(rec.get("website"))
        if domain and domain in domain_index:
            matched_group = domain_index[domain]

        # Check phone
        if matched_group is None:
            phone = rec.get("phone")
            if phone and phone in phone_index:
                matched_group = phone_index[phone]

        # Check email
        if matched_group is None:
            email = rec.get("email")
            if email and email in email_index:
                matched_group = email_index[email]

        # Fuzzy name + city match
        if matched_group is None and HAS_FUZZY:
            name = (rec.get("business_name") or "").lower()
            city = (rec.get("city") or "").lower()
            for g_idx, group in enumerate(groups):
                rep = records[group[0]]
                rep_name = (rep.get("business_name") or "").lower()
                rep_city = (rep.get("city") or "").lower()
                if city == rep_city and fuzz.token_sort_ratio(name, rep_name) >= 90:
                    matched_group = g_idx
                    break

        if matched_group is not None:
            groups[matched_group].append(i)
            assigned[i] = matched_group
        else:
            new_group = len(groups)
            groups.append([i])
            assigned[i] = new_group

        # Add to indexes
        if domain:
            domain_index.setdefault(domain, assigned[i])
        if rec.get("phone"):
            phone_index.setdefault(rec["phone"], assigned[i])
        if rec.get("email"):
            email_index.setdefault(rec["email"], assigned[i])

    final = []
    rejected = []

    for group in groups:
        if len(group) == 1:
            rec = dict(records[group[0]])
            rec["multi_source"] = False
            final.append(rec)
            continue

        # Pick the most complete record as primary
        sorted_group = sorted(group, key=lambda i: completeness(records[i]), reverse=True)
        primary = dict(records[sorted_group[0]])
        primary["multi_source"] = True

        for idx in sorted_group[1:]:
            secondary = records[idx]
            primary = merge(primary, secondary)

            dup = dict(secondary)
            dup["duplicate_of"] = primary.get("business_name")
            dup["duplicate_reason"] = get_match_reason(primary, secondary)
            rejected.append(dup)

        final.append(primary)

    log.info("Deduplication: %d input -> %d unique, %d duplicates removed.", len(records), len(final), len(rejected))
    return final, rejected
