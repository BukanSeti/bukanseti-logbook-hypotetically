from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import yaml

from .airport_codes import AirportDirectory
from .extractors import extractor_for
from .inventory import build_source_inventory
from .manual_aircraft import ManualAircraftDirectory
from .models import EM_DASH, FlightSector
from .pdf_export import export_pdf_from_workbook
from .reconstruction import Reconstructor
from .validation import validate
from .workbook import WorkbookWriter


@dataclass
class PipelineOutputs:
    workbook: Path
    pdf: Path
    manual_review: Path
    summary: dict[str, object]


class CoradinePipeline:
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.repo_root = config_path.parent.parent
        self.config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    def inventory_only(self, inputs: list[Path], output_dir: Path) -> Path:
        inventory = build_source_inventory(inputs)
        output_dir.mkdir(parents=True, exist_ok=True)
        destination = output_dir / "source_inventory.json"
        destination.write_text(
            json.dumps(
                [item.model_dump(mode="json") for item in inventory],
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )
        return destination

    def process(
        self,
        owner_name: str,
        inputs: list[Path],
        output_dir: Path,
        start_processing: bool,
        allow_pdf_fallback: bool = False,
        aircraft_overrides: list[str] | None = None,
    ) -> PipelineOutputs:
        if (
            self.config["processing"].get("require_start_processing_flag", True)
            and not start_processing
        ):
            inventory_path = self.inventory_only(inputs, output_dir)
            raise RuntimeError(
                f"Source inventory created at {inventory_path}. "
                "Re-run with --start-processing after review."
            )
        if not owner_name.strip() or owner_name.strip() == "[INSERT FULL NAME]":
            raise ValueError("Exact logbook owner full name is required")

        inventory = build_source_inventory(inputs)
        raw_entries = []
        for item, path in zip(inventory, inputs, strict=True):
            batch = extractor_for(path).extract(path)
            raw_entries.extend(batch.entries)
            item.used = True
            item.readability_status = "Extracted"
            item.apparent_date_range = _date_range(batch.entries)

        manual_aircraft = ManualAircraftDirectory.from_specs(aircraft_overrides)
        airports = AirportDirectory(self.repo_root / "data" / "airport_seed.csv")
        reconstructor = Reconstructor(
            owner_name=owner_name,
            airports=airports,
            manual_aircraft=manual_aircraft,
            turnaround_minutes=int(
                self.config["processing"].get("default_turnaround_minutes", 45)
            ),
        )
        reconstruction = reconstructor.reconstruct(raw_entries)
        validation = validate(
            reconstruction.sectors,
            reconstruction.provenance,
            original_source_entries=len(raw_entries),
            split_source_entries=reconstruction.split_source_entries,
        )

        output_dir.mkdir(parents=True, exist_ok=True)
        workbook_path = output_dir / self.config["output"]["workbook_name"]
        pdf_path = output_dir / self.config["output"]["pdf_name"]
        review_path = output_dir / self.config["output"].get(
            "manual_review_name",
            "manual_review.json",
        )

        WorkbookWriter(
            owner_name=owner_name,
            rows_per_page=int(
                self.config["processing"].get("rows_per_print_page", 24)
            ),
        ).write(
            workbook_path,
            reconstruction.sectors,
            reconstruction.provenance,
            validation,
            reconstruction.airport_mappings,
            inventory,
        )
        export_pdf_from_workbook(
            workbook_path,
            pdf_path,
            reconstruction.sectors,
            owner_name,
            allow_fallback=allow_pdf_fallback,
        )

        review = _write_manual_review(review_path, reconstruction.sectors)
        summary = dict(validation.summary)
        summary["aircraft_questions"] = len(review["aircraft_questions"])
        summary["unverified_crew_fields"] = len(review["unverified_crew_fields"])
        return PipelineOutputs(
            workbook=workbook_path,
            pdf=pdf_path,
            manual_review=review_path,
            summary=summary,
        )


def _write_manual_review(
    destination: Path,
    sectors: list[FlightSector],
) -> dict[str, object]:
    aircraft_questions: list[dict[str, object]] = []
    crew_unverified: list[dict[str, object]] = []
    seen_aircraft: set[tuple[str, str, str]] = set()
    seen_crew: set[tuple[str, str]] = set()

    for sector in sectors:
        date_text = sector.date.isoformat() if sector.date else "Unknown"
        route = f"{sector.departure}-{sector.arrival}"
        if sector.registration == EM_DASH:
            key = (sector.source_entry_number, "registration", route)
            if key not in seen_aircraft:
                seen_aircraft.add(key)
                aircraft_questions.append(
                    {
                        "entry_number": sector.entry_number,
                        "source_entry": sector.source_entry_number,
                        "date": date_text,
                        "route": route,
                        "missing": ["registration", "aircraft_type"],
                        "question": (
                            "Provide the aircraft registration and type from a reliable public "
                            "source or your own record."
                        ),
                        "rerun_example": "--aircraft PK-LJF=B739",
                    }
                )
        elif sector.aircraft_type == EM_DASH:
            key = (sector.registration, "aircraft_type", route)
            if key not in seen_aircraft:
                seen_aircraft.add(key)
                aircraft_questions.append(
                    {
                        "entry_number": sector.entry_number,
                        "source_entry": sector.source_entry_number,
                        "date": date_text,
                        "route": route,
                        "registration": sector.registration,
                        "missing": ["aircraft_type"],
                        "question": f"Provide the aircraft type for {sector.registration}.",
                        "rerun_example": f"--aircraft {sector.registration}=B739",
                    }
                )

        missing_crew_fields = []
        if sector.pic_name == EM_DASH:
            missing_crew_fields.append("pic_name")
        if sector.pic_employee_id == EM_DASH:
            missing_crew_fields.append("pic_employee_id")
        if missing_crew_fields:
            key = (sector.source_entry_number, ",".join(missing_crew_fields))
            if key not in seen_crew:
                seen_crew.add(key)
                crew_unverified.append(
                    {
                        "entry_number": sector.entry_number,
                        "source_entry": sector.source_entry_number,
                        "date": date_text,
                        "route": route,
                        "fields": missing_crew_fields,
                        "policy": (
                            "Left unverified because this repository does not use, request, "
                            "or access any Crew Bank."
                        ),
                    }
                )

    if aircraft_questions:
        status = "needs_aircraft_input"
    elif crew_unverified:
        status = "complete_with_unverified_crew_fields"
    else:
        status = "complete"

    document: dict[str, object] = {
        "status": status,
        "privacy_policy": (
            "Crew names and employee IDs are transcribed only from the supplied photo. "
            "No Crew Bank, private API, Google Sheet, or directory is accessed."
        ),
        "aircraft_input_format": "Repeat --aircraft REGISTRATION=TYPE as needed.",
        "aircraft_questions": aircraft_questions,
        "unverified_crew_fields": crew_unverified,
    }
    destination.write_text(
        json.dumps(document, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    return document


def _date_range(entries) -> str:
    dates = sorted(entry.date for entry in entries if entry.date)
    if not dates:
        return "Unknown"
    return f"{dates[0].isoformat()} to {dates[-1].isoformat()}"
