"""
test_pipeline.py - Automated tests for cleaning, deduplication, and scoring.

Run with: python -m pytest tests/test_pipeline.py -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.cleaning.normalizer import (
    normalize_name, normalize_website, normalize_phone,
    normalize_email, normalize_location, clean_record,
)
from src.matching.deduplicator import deduplicate, get_domain
from src.scoring.scorer import score_record


# ── normalize_name ──────────────────────────────────────────────────────────

class TestNormalizeName:
    def test_strips_extra_whitespace(self):
        assert normalize_name("  Acme   Corp  ") == "Acme Corp"

    def test_all_caps_becomes_title_case(self):
        assert normalize_name("ACME DIGITAL") == "Acme Digital"

    def test_mixed_case_preserved(self):
        assert normalize_name("McKinsey & Co") == "McKinsey & Co"

    def test_none_returns_none(self):
        assert normalize_name(None) is None

    def test_empty_string_returns_none(self):
        assert normalize_name("   ") is None


# ── normalize_website ────────────────────────────────────────────────────────

class TestNormalizeWebsite:
    def test_adds_https_scheme(self):
        url, valid = normalize_website("example.com")
        assert url.startswith("https://")
        assert valid is True

    def test_strips_utm_params(self):
        url, _ = normalize_website("https://example.com/?utm_source=google&utm_medium=cpc")
        assert "utm_source" not in url
        assert "utm_medium" not in url

    def test_strips_trailing_slash(self):
        url, _ = normalize_website("https://example.com/about/")
        assert not url.endswith("/")

    def test_lowercases_host(self):
        url, _ = normalize_website("https://EXAMPLE.COM/path")
        assert "example.com" in url

    def test_invalid_url_no_dot(self):
        _, valid = normalize_website("https://localhost")
        assert valid is False

    def test_none_returns_none(self):
        url, valid = normalize_website(None)
        assert url is None
        assert valid is False


# ── normalize_phone ──────────────────────────────────────────────────────────

class TestNormalizePhone:
    def test_valid_us_number(self):
        phone, valid = normalize_phone("(312) 555-0100")
        assert valid is True
        assert phone.startswith("+1")

    def test_invalid_too_short(self):
        _, valid = normalize_phone("123")
        assert valid is False

    def test_none_returns_none(self):
        phone, valid = normalize_phone(None)
        assert phone is None
        assert valid is False

    def test_number_with_dashes(self):
        _, valid = normalize_phone("312-555-0199")
        assert valid is True


# ── normalize_email ──────────────────────────────────────────────────────────

class TestNormalizeEmail:
    def test_lowercases_email(self):
        email, _, _ = normalize_email("Info@COMPANY.COM")
        assert email == "info@company.com"

    def test_strips_whitespace(self):
        email, valid, _ = normalize_email("  hello@example.com  ")
        assert email == "hello@example.com"
        assert valid is True

    def test_detects_generic_info(self):
        _, _, generic = normalize_email("info@agency.com")
        assert generic is True

    def test_specific_email_not_generic(self):
        _, _, generic = normalize_email("john.doe@agency.com")
        assert generic is False

    def test_invalid_email_no_at(self):
        _, valid, _ = normalize_email("notanemail")
        assert valid is False

    def test_none_returns_defaults(self):
        email, valid, generic = normalize_email(None)
        assert email is None
        assert valid is False
        assert generic is False


# ── normalize_location ───────────────────────────────────────────────────────

class TestNormalizeLocation:
    def test_title_cases_city(self):
        city, _ = normalize_location("chicago", "IL")
        assert city == "Chicago"

    def test_strips_whitespace(self):
        city, state = normalize_location("  Chicago  ", "  Illinois  ")
        assert city == "Chicago"
        assert state == "Illinois"

    def test_none_city(self):
        city, state = normalize_location(None, "Illinois")
        assert city is None
        assert state == "Illinois"


# ── deduplicate ──────────────────────────────────────────────────────────────

class TestDeduplicate:
    def make(self, name, website=None, phone=None, email=None, city="Chicago"):
        return {
            "business_name": name,
            "website": website,
            "phone": phone,
            "email": email,
            "city": city,
            "state": "Illinois",
            "source_name": "TestSource",
            "website_valid": bool(website),
            "phone_valid": bool(phone),
            "email_valid": bool(email),
        }

    def test_exact_domain_match(self):
        records = [
            self.make("Acme Digital", website="https://acme.com"),
            self.make("Acme Digital Agency", website="https://www.acme.com"),
        ]
        final, rejected = deduplicate(records)
        assert len(final) == 1
        assert len(rejected) == 1

    def test_exact_phone_match(self):
        records = [
            self.make("Agency A", phone="+13125550100"),
            self.make("Agency A LLC", phone="+13125550100"),
        ]
        final, _ = deduplicate(records)
        assert len(final) == 1

    def test_no_false_positives(self):
        records = [
            self.make("Alpha Marketing", website="https://alpha.com"),
            self.make("Beta Marketing", website="https://beta.com"),
        ]
        final, rejected = deduplicate(records)
        assert len(final) == 2
        assert len(rejected) == 0

    def test_empty_input(self):
        final, rejected = deduplicate([])
        assert final == []
        assert rejected == []


# ── score_record ─────────────────────────────────────────────────────────────

class TestScoreRecord:
    def base(self, **kwargs):
        rec = {
            "business_name": "Test Agency",
            "website": "https://testagency.com",
            "phone": "+13125550100",
            "email": "hello@testagency.com",
            "city": "Chicago",
            "state": "Illinois",
            "multi_source": False,
            "website_valid": True,
            "phone_valid": True,
            "email_valid": True,
        }
        rec.update(kwargs)
        return rec

    def test_full_record_scores_high(self):
        scored = score_record(self.base())
        assert scored["quality_score"] >= 80

    def test_no_contact_info_scores_low(self):
        rec = self.base(phone=None, phone_valid=False, email=None, email_valid=False, website=None, website_valid=False)
        scored = score_record(rec)
        assert scored["quality_score"] <= 20

    def test_multi_source_adds_points(self):
        s1 = score_record(self.base(multi_source=False))
        s2 = score_record(self.base(multi_source=True))
        assert s2["quality_score"] == s1["quality_score"] + 10

    def test_recommended_method_multiple(self):
        assert score_record(self.base())["recommended_contact_method"] == "Multiple Methods"

    def test_recommended_method_phone_only(self):
        rec = self.base(email=None, email_valid=False)
        assert score_record(rec)["recommended_contact_method"] == "Phone"

    def test_recommended_method_email_only(self):
        rec = self.base(phone=None, phone_valid=False)
        assert score_record(rec)["recommended_contact_method"] == "Email"

    def test_recommended_method_no_contact(self):
        rec = self.base(phone=None, phone_valid=False, email=None, email_valid=False, website=None, website_valid=False)
        assert score_record(rec)["recommended_contact_method"] == "No Reliable Contact Method"

    def test_score_capped_at_100(self):
        rec = self.base(multi_source=True, rating=4.5, review_count=50)
        assert score_record(rec)["quality_score"] <= 100


# ── get_domain helper ────────────────────────────────────────────────────────

class TestGetDomain:
    def test_strips_www(self):
        assert get_domain("https://www.acme.com") == "acme.com"

    def test_handles_no_www(self):
        assert get_domain("https://acme.com") == "acme.com"

    def test_none_returns_none(self):
        assert get_domain(None) is None


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
