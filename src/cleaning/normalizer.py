"""
normalizer.py - Cleans and normalizes raw business record fields.

Handles:
- Business names (whitespace, casing)
- Websites (scheme, tracking params, trailing slash, validation)
- Phone numbers (E.164 formatting, validation)
- Emails (lowercase, format validation, generic detection)
- City/State (whitespace, casing)
"""

import re
import logging
from urllib.parse import urlparse, urlunparse, urlencode, parse_qs

try:
    import phonenumbers
    HAS_PHONENUMBERS = True
except ImportError:
    HAS_PHONENUMBERS = False

log = logging.getLogger(__name__)

# URL tracking parameters to remove
TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "mc_cid", "mc_eid", "ref", "source",
}

# Generic email prefixes that are low value for outreach
GENERIC_EMAIL_PREFIXES = {
    "info", "contact", "hello", "support", "admin", "sales",
    "office", "team", "inquiry", "enquiry", "mail", "noreply",
}

EMAIL_RE = re.compile(r"^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$")


def normalize_name(name):
    """Remove extra spaces. Convert ALL-CAPS names to Title Case."""
    if not name:
        return None
    name = " ".join(name.split())
    if name.isupper():
        name = name.title()
    return name or None


def normalize_website(url):
    """
    Clean and validate a website URL.
    - Adds https:// if scheme is missing
    - Removes tracking parameters (utm_*, fbclid, etc.)
    - Removes trailing slash
    - Returns (cleaned_url, is_valid)
    """
    if not url:
        return None, False

    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        parsed = urlparse(url)
    except Exception:
        return url, False

    # Remove tracking params
    qs = parse_qs(parsed.query, keep_blank_values=False)
    clean_qs = {k: v for k, v in qs.items() if k.lower() not in TRACKING_PARAMS}
    clean_query = urlencode(clean_qs, doseq=True)

    # Strip trailing slash from path
    path = parsed.path.rstrip("/") or ""

    cleaned = urlunparse(("https", parsed.netloc.lower(), path, parsed.params, clean_query, ""))

    # A valid URL must have a dot in the host and no spaces
    is_valid = "." in parsed.netloc and " " not in parsed.netloc

    return cleaned, is_valid


def normalize_phone(phone, default_region="US"):
    """
    Validate and format a phone number to E.164 standard (e.g. +13125550100).
    Falls back to digit-count check if phonenumbers library is unavailable.
    Returns (formatted_phone, is_valid).
    """
    if not phone:
        return None, False

    phone = phone.strip()

    if not HAS_PHONENUMBERS:
        digits = re.sub(r"\D", "", phone)
        return phone, len(digits) >= 7

    try:
        parsed = phonenumbers.parse(phone, default_region)
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164), True
        return phone, False
    except phonenumbers.NumberParseException:
        return phone, False


def normalize_email(email):
    """
    Lowercase and validate an email address.
    Also flags generic addresses like info@, contact@, support@ etc.
    Returns (cleaned_email, is_valid, is_generic).
    """
    if not email:
        return None, False, False

    email = email.strip().lower()
    is_valid = bool(EMAIL_RE.match(email))
    prefix = email.split("@")[0] if "@" in email else ""
    is_generic = prefix in GENERIC_EMAIL_PREFIXES

    return email, is_valid, is_generic


def normalize_location(city, state):
    """Strip whitespace and apply Title Case to city and state."""
    def clean(value):
        if not value:
            return None
        return " ".join(value.strip().split()).title()
    return clean(city), clean(state)


def clean_record(record):
    """Apply all normalizers to a single record. Returns a cleaned copy."""
    r = dict(record)

    r["business_name"] = normalize_name(r.get("business_name"))
    r["website"], r["website_valid"] = normalize_website(r.get("website"))
    r["phone"], r["phone_valid"] = normalize_phone(r.get("phone"))
    r["email"], r["email_valid"], r["email_generic"] = normalize_email(r.get("email"))
    r["city"], r["state"] = normalize_location(r.get("city"), r.get("state"))

    return r


def clean_records(records):
    """Clean a list of records. Skips any record that throws an error."""
    cleaned = []
    for rec in records:
        try:
            cleaned.append(clean_record(rec))
        except Exception as e:
            log.warning("Skipping record '%s' due to error: %s", rec.get("business_name"), e)
    return cleaned
