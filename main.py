#!/usr/bin/env python3
"""ScanSmart command-line interface.

Examples
--------
    python main.py --input data/samples --output outputs --mode scan
    python main.py --input photo.jpg --output outputs --mode color --pdf out.pdf
    python main.py --input data/samples --output outputs --overlay --comparison -v
"""

import argparse
import os
import sys
from typing import List

from scansmart import ScanSmartError, ScanConfig, __version__
from scansmart.config import MODES
from scansmart.exporter import (
    export_pdf, summarise, write_csv_report, write_json_report,
)
from scansmart.logger import get_logger, setup_logging
from scansmart.pipeline import process_batch

log = get_logger("scansmart.cli")


def build_parser() -> argparse.ArgumentParser:
    """Define every command-line option."""
    parser = argparse.ArgumentParser(
        prog="scansmart",
        description="Automatic document scanner built with OpenCV.",
    )
    parser.add_argument("-i", "--input", required=True,
                        help="image file or folder of images")
    parser.add_argument("-o", "--output", default="outputs",
                        help="folder for processed pages (default: outputs)")
    parser.add_argument("-m", "--mode", default="scan", choices=MODES,
                        help="output style (default: scan)")
    parser.add_argument("--pdf", metavar="FILE",
                        help="also bundle all pages into this PDF")
    parser.add_argument("--overlay", action="store_true",
                        help="save the detected-corners debug image")
    parser.add_argument("--comparison", action="store_true",
                        help="save a before/after side-by-side image")
    parser.add_argument("--working-height", type=int, default=600,
                        help="detection resolution in px (default: 600)")
    parser.add_argument("--min-confidence", type=float, default=0.25,
                        help="confidence below which a page is flagged")
    parser.add_argument("--no-report", action="store_true",
                        help="skip the JSON/CSV batch reports")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="enable debug logging")
    parser.add_argument("--version", action="version",
                        version=f"ScanSmart {__version__}")
    return parser


def print_summary(records: List[dict]) -> None:
    """Pretty-print the batch table and the aggregate statistics."""
    header = f"{'FILE':<26}{'STATUS':<9}{'METHOD':<15}{'CONF':>6}{'GRADE':>7}{'ms':>8}"
    print("\n" + header)
    print("-" * len(header))
    for record in records:
        print(
            f"{record['source'][:25]:<26}"
            f"{record['status']:<9}"
            f"{str(record.get('method', '-')):<15}"
            f"{record.get('confidence', 0):>6.2f}"
            f"{str(record.get('grade', '-')):>7}"
            f"{record.get('elapsed_ms', 0):>8.0f}"
        )
    stats = summarise(records)
    print("-" * len(header))
    print(
        f"Processed {stats['processed']}/{stats['total_images']} "
        f"(success {stats['success_rate'] * 100:.0f}%) | "
        f"mean confidence {stats['mean_confidence']:.2f} | "
        f"mean time {stats['mean_time_ms']:.0f} ms"
    )
    print(f"Grades: {stats['grades']}\n")


def main(argv=None) -> int:
    """Entry point. Returns a shell exit code."""
    args = build_parser().parse_args(argv)
    setup_logging(args.verbose)

    try:
        config = ScanConfig(
            mode=args.mode,
            working_height=args.working_height,
            min_confidence=args.min_confidence,
        )
        results = process_batch(
            args.input, args.output, config,
            save_overlay=args.overlay, save_comparison=args.comparison,
        )
        records = [result.to_record() for result in results]

        if args.pdf:
            pages = [r.image for r in results if r.status == "ok" and r.image is not None]
            export_pdf(pages, args.pdf)

        if not args.no_report:
            write_json_report(records, config.to_dict(),
                              os.path.join(args.output, "report.json"))
            write_csv_report(records, os.path.join(args.output, "report.csv"))

        print_summary(records)
        return 0 if all(r.status == "ok" for r in results) else 1

    except ScanSmartError as exc:
        log.error("ScanSmart error: %s", exc)
        return 2
    except KeyboardInterrupt:                 # pragma: no cover
        log.warning("Interrupted by user")
        return 130


if __name__ == "__main__":
    sys.exit(main())
