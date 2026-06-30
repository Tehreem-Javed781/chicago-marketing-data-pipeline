"""
main.py - Entry point for the data pipeline.

Usage:
    python main.py              # collect live data
    python main.py --cached     # reuse previously collected raw data
    python main.py --no-health  # skip source health check
"""

import argparse
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Business Data Pipeline")
    parser.add_argument("--cached", action="store_true", help="Use saved raw data instead of scraping.")
    parser.add_argument("--no-health", action="store_true", help="Skip health check.")
    args = parser.parse_args()

    # Step 1: Health check
    if not args.no_health:
        log.info("Checking source health...")
        from src.pipeline.health_monitor import run_health_check
        results = run_health_check()
        for r in results:
            if not r["healthy"]:
                log.warning("Source '%s' may be degraded: %s", r["name"], r["issues"])

    # Step 2: Run pipeline
    log.info("Starting pipeline...")
    from src.pipeline.runner import run
    stats = run(use_live=not args.cached)

    # Step 3: Print summary
    print("\nPIPELINE SUMMARY")
    print(json.dumps(stats, indent=2))

    total = stats["total_valid_final"]
    if total >= 100:
        log.info("Done. %d valid records collected.", total)
    else:
        log.warning("Only %d records collected. Target is 100+.", total)


if __name__ == "__main__":
    main()
