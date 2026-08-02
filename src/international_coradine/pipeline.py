from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import yaml

from .airport_codes import AirportDirectory
from .extractors import extractor_for
from .inventory import build_source_inventory
from .pdf_export import export_pdf_from_workbook
from .reconstruction import Reconstructor
from .references import AircraftBank, CrewBank, download_sheet_xlsx, resolve_reference_path
from .validation import validate
from .workbook import WorkbookWriter


@dataclass
class PipelineOutputs:
    workbook: Path
    pdf: Path
    summary: dict[str, object]


class CoradinePipeline:
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.repo_root = config_path.parent.parent
        self.config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    def refresh_references(self) -> tuple[Path, Path]:
        references = self.config["references"]
        crew_path = resolve_reference_path(references["crew_cache"], "LION_AIR_CREW_XLSX")
        aircraft_path = resolve_reference_path(references["aircraft_cache"], "LION_AIR_AIRCRAFT_XLSX")
        download_sheet_xlsx(references["crew_sheet_url"], crew_path)
        download_sheet_xlsx(references["aircraft_sheet_url"], aircraft_path)
        return crew_path, aircraft_path

    def inventory_only(self, inputs: list[Path], output_dir: Path) -> Path:
        inventory = build_source_inventory(inputs)
        output_dir.mkdir(parents=True, exist_ok=True)
        destination = output_dir / "source_inventory.json"
        destination.write_text(
            json.dumps([item.model_dump(mode="json") for item in inventory], indent=2),
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
        refresh_references: bool = False,
    ) -> PipelineOutputs:
        if self.config["processing"].get("require_start_processing_flag", True) and not start_processing:
            inventory_path = self.inventory_only(inputs, output_dir)
            raise RuntimeError(
                f"Source inventory created at {inventory_path}. Re-run with --start-processing after review."
            )
        if not owner_name.strip() or owner_name.strip() == "[INSERT FULL NAME]":
            raise ValueError("Exact logbook owner full name is required")

        inventory = build_source_inventory(inputs)
        if refresh_references:
            self.refresh_references()
        crew_bank, aircraft_bank = self._load_reference_banks()

        raw_entries = []
        for item, path in zip(inventory, inputs, strict=True):
            batch = extractor_for(path).extract(path)
            raw_entries.extend(batch.entries)
            item.used = True
            item.readability_status = "Extracted"
            item.apparent_date_range = _date_range(batch.entries)

        airports = AirportDirectory(self.repo_root / "data" / "airport_seed.csv")
        reconstructor = Reconstructor(
            owner_name=owner_name,
            airports=airports,
            crew_bank=crew_bank,
            aircraft_bank=aircraft_bank,
            turnaround_minutes=int(self.config["processing"].get("default_turnaround_minutes", 45)),
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
        WorkbookWriter(
            owner_name=owner_name,
            rows_per_page=int(self.config["processing"].get("rows_per_print_page", 24)),
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
        return PipelineOutputs(workbook=workbook_path, pdf=pdf_path, summary=validation.summary)

    def _load_reference_banks(self) -> tuple[CrewBank | None, AircraftBank | None]:
        references = self.config["references"]
        crew_path = resolve_reference_path(references["crew_cache"], "LION_AIR_CREW_XLSX")
        aircraft_path = resolve_reference_path(references["aircraft_cache"], "LION_AIR_AIRCRAFT_XLSX")
        crew = CrewBank.from_xlsx(crew_path) if crew_path.exists() else None
        aircraft = AircraftBank.from_xlsx(aircraft_path) if aircraft_path.exists() else None
        return crew, aircraft


def _date_range(entries) -> str:
    dates = sorted(entry.date for entry in entries if entry.date)
    if not dates:
        return "Unknown"
    return f"{dates[0].isoformat()} to {dates[-1].isoformat()}"
