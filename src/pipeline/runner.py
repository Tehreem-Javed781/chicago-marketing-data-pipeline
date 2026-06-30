"""
runner.py - Runs the full pipeline from collection to final CSV.

Steps:
  1. Collect from Expertise.com and Chicago Open Data
  2. Save raw data
  3. Clean and normalize
  4. Deduplicate
  5. Score
  6. Save final CSV and rejected records
  7. Return summary stats
"""

import json
import logging
import os
from datetime import date

import pandas as pd

from src.collectors import expertise_collector, chicago_opendata_collector
from src.cleaning.normalizer import clean_records
from src.matching.deduplicator import deduplicate
from src.scoring.scorer import score_records

log = logging.getLogger(__name__)

TODAY = date.today().isoformat()

# Columns included in the final CSV
FINAL_COLUMNS = [
    "business_name", "business_category",
    "website", "phone", "email",
    "address", "city", "state", "zip_code", "country",
    "rating", "review_count",
    "source_name", "source_url", "date_collected",
    "quality_score", "recommended_contact_method",
    "multi_source", "notes",
]


def save_json(data, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    log.info("Saved %d records -> %s", len(data), path)


def save_csv(records, path, columns=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df = pd.DataFrame(records)
    if columns:
        present = [c for c in columns if c in df.columns]
        df = df[present]
    df.to_csv(path, index=False, encoding="utf-8")
    log.info("Saved CSV %d rows -> %s", len(df), path)


def pct(records, field):
    if not records:
        return 0.0
    return round(sum(1 for r in records if r.get(field)) / len(records) * 100, 1)


def run(use_live=True):
    raw_path = f"data/raw/raw_{TODAY}.json"

    # Step 1: Collection
    if use_live or not os.path.exists(raw_path):
        log.info("COLLECTION")
        expertise_records = expertise_collector.collect()
        chicago_records = chicago_opendata_collector.collect()
        raw = expertise_records + chicago_records
        save_json(raw, raw_path)
    else:
        log.info("Loading cached raw data from %s", raw_path)
        with open(raw_path, encoding="utf-8") as f:
            raw = json.load(f)

    log.info("Total raw records: %d", len(raw))

    # Step 2: Clean
    log.info("CLEANING")
    cleaned = clean_records(raw)
    save_json(cleaned, f"data/processed/cleaned_{TODAY}.json")

    # Step 3: Deduplicate
    log.info("DEDUPLICATION")
    unique, duplicates = deduplicate(cleaned)
    save_json(duplicates, f"data/rejected/duplicates_{TODAY}.json")

    # Step 4: Score
    log.info("SCORING")
    scored = score_records(unique)

    # Step 5: Separate valid from low quality
    valid = [r for r in scored if r.get("quality_score", 0) >= 20 and r.get("business_name")]
    low_quality = [r for r in scored if r.get("quality_score", 0) < 20 or not r.get("business_name")]

    for r in low_quality:
        r["rejection_reason"] = "Quality score below 20 or missing business name"

    # Sort by quality score (best first)
    valid.sort(key=lambda r: r.get("quality_score", 0), reverse=True)

    # Step 6: Save outputs
    save_csv(valid, f"data/final/final_{TODAY}.csv", columns=FINAL_COLUMNS)
    save_csv(duplicates + low_quality, f"data/rejected/rejected_{TODAY}.csv")

    # Step 7: Summary stats
    stats = {
        "total_raw": len(raw),
        "total_after_cleaning": len(cleaned),
        "duplicates_removed": len(duplicates),
        "low_quality_removed": len(low_quality),
        "total_valid_final": len(valid),
        "pct_with_website": pct(valid, "website"),
        "pct_with_phone": pct(valid, "phone"),
        "pct_with_email": pct(valid, "email"),
        "pct_multi_source": round(sum(1 for r in valid if r.get("multi_source")) / max(len(valid), 1) * 100, 1),
        "avg_quality_score": round(sum(r.get("quality_score", 0) for r in valid) / max(len(valid), 1), 1),
        "contact_method_distribution": _count(valid, "recommended_contact_method"),
    }

    log.info("PIPELINE COMPLETE")
    return stats


def _count(records, field):
    counts = {}
    for r in records:
        v = r.get(field) or "Unknown"
        counts[v] = counts.get(v, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))
