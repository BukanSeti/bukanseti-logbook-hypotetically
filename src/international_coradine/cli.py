from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .pipeline import CoradinePipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="coradine",
        description="Lion Air-only International Coradine Rev 3 reconstruction pipeline",
    )
    parser.add_argument("--config", type=Path, default=Path("config/default.yaml"))
    subparsers = parser.add_subparsers(dest="command", required=True)

    refresh = subparsers.add_parser("refresh-references", help="Download Lion Air Crew/Airplane reference caches")
    refresh.set_defaults(action="refresh")

    inventory = subparsers.add_parser("inventory", help="Create a read-only source inventory")
    inventory.add_argument("inputs", nargs="+", type=Path)
    inventory.add_argument("--output-dir", type=Path, default=Path("work"))
    inventory.set_defaults(action="inventory")

    process = subparsers.add_parser("process", help="Extract, reconstruct, validate, and export Excel/PDF")
    process.add_argument("inputs", nargs="+", type=Path)
    process.add_argument("--owner", required=True, help="Exact full name of the logbook owner")
    process.add_argument("--output-dir", type=Path, default=Path("output"))
    process.add_argument("--start-processing", action="store_true", help="Required explicit processing gate")
    process.add_argument("--refresh-references", action="store_true")
    process.add_argument("--allow-pdf-fallback", action="store_true")
    process.set_defaults(action="process")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    pipeline = CoradinePipeline(args.config)
    try:
        if args.action == "refresh":
            crew, aircraft = pipeline.refresh_references()
            print(json.dumps({"crew_reference": str(crew), "aircraft_reference": str(aircraft)}, indent=2))
            return 0
        if args.action == "inventory":
            output = pipeline.inventory_only(args.inputs, args.output_dir)
            print(output)
            return 0
        outputs = pipeline.process(
            owner_name=args.owner,
            inputs=args.inputs,
            output_dir=args.output_dir,
            start_processing=args.start_processing,
            allow_pdf_fallback=args.allow_pdf_fallback,
            refresh_references=args.refresh_references,
        )
        print(json.dumps({
            "workbook": str(outputs.workbook),
            "pdf": str(outputs.pdf),
            "summary": outputs.summary,
        }, indent=2, default=str))
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
