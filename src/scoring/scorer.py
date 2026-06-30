"""
scorer.py - Scores each business record from 0 to 100.

Scoring rubric:
  Valid business name        : 10 pts
  Valid website              : 20 pts
  Valid phone number         : 20 pts
  Valid email address        : 20 pts
  Complete location          : 10 pts
  Confirmed by 2+ sources    : 10 pts
  Rating present             :  5 pts
  Review count present       :  5 pts
  Maximum                    : 100 pts

Also assigns a recommended_contact_method based on available contact info.
"""

import logging

log = logging.getLogger(__name__)


def score_record(record):
    """Score a single record and assign a recommended contact method."""
    r = dict(record)
    score = 0

    if r.get("business_name"):
        score += 10

    if r.get("website") and r.get("website_valid"):
        score += 20

    has_phone = r.get("phone") and r.get("phone_valid")
    if has_phone:
        score += 20

    has_email = r.get("email") and r.get("email_valid")
    if has_email:
        score += 20

    if r.get("city") and r.get("state"):
        score += 10

    if r.get("multi_source") or "|" in (r.get("source_name") or ""):
        score += 10

    if r.get("rating") is not None:
        score += 5

    if r.get("review_count") is not None:
        score += 5

    r["quality_score"] = min(score, 100)

    # Recommended contact method
    if has_phone and has_email:
        r["recommended_contact_method"] = "Multiple Methods"
    elif has_phone:
        r["recommended_contact_method"] = "Phone"
    elif has_email:
        r["recommended_contact_method"] = "Email"
    elif r.get("website") and r.get("website_valid"):
        r["recommended_contact_method"] = "Website Contact Form"
    else:
        r["recommended_contact_method"] = "No Reliable Contact Method"

    return r


def score_records(records):
    return [score_record(r) for r in records]
