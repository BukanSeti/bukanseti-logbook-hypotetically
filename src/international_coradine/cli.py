from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .pipeline import CoradinePipeline


def _add_output_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--owner", required=True, help="Exact full name of the logbook owner")
    parser.add_argument("--output-dir", type=Path, default=Path("output"))
    parser.add_argument(
        "--aircraft",
        action="append",
        default=[],
        metavar="REGISTRATION=TYPE",
        help=(
            "Optional manual aircraft mapping. Repeat as needed, for example "
            "--aircraft PK-LJF=B739."
        ),
    )
    parser.add_argument("--allow-pdf-fallback", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="coradine",
        description=(
            "Lion Air-only photo-to-Excel/PDF logbook pipeline with no Crew Bank "
            "or private reference API"
        ),
    )
    parser.add_argument("--config", type=Path, default=Path("config/default.yaml"))
    subparsers = parser.add_subparsers(dest="command", required=True)

    photo = subparsers.add_parser(
        "photo",
        help="Process logbook photos/PDFs directly using the simple shared-user workflow",
    )
    photo.add_argument("inputs", nargs="+", type=Path)
    _add_output_arguments(photo)
    photo.set_defaults(action="photo")

    inventory = subparsers.add_parser(
        "inventory",
        help="Create a read-only source inventory without OCR or reconstruction",
    )
    inventory.add_argument("inputs", nargs="+", type=Path)
    inventory.add_argument("--output-dir", type=Path, default=Path("work"))
    inventory.set_defaults(action="inventory")

    process = subparsers.add_parser(
        "process",
        help="Advanced extract, reconstruct, validate, and export workflow",
    )
    process.add_argument("inputs", nargs="+", type=Path)
    _add_output_arguments(process)
    process.add_argument(
        "--start-processing",
        action="store_true",
        help="Required explicit processing gate for the advanced workflow",
    )
    process.set_defaults(action="process")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    pipeline = CoradinePipeline(args.config)
    try:
        if args.action == "inventory":
            output = pipeline.inventory_only(args.inputs, args.output_dir)
            print(output)
            return 0

        outputs = pipeline.process(
            owner_name=args.owner,
            inputs=args.inputs,
            output_dir=args.output_dir,
            start_processing=args.action == "photo" or args.start_processing,
            allow_pdf_fallback=args.allow_pdf_fallback,
            aircraft_overrides=args.aircraft,
        )
        print(
            json.dumps(
                {
                    "workbook": str(outputs.workbook),
                    "pdf": str(outputs.pdf),
                    "manual_review": str(outputs.manual_review),
                    "summary": outputs.summary,
                },
                indent=2,
                default=str,
            )
        )
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
