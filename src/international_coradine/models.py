from __future__ import annotations

from datetime import date as Date
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

EM_DASH = "—"


class ProvenanceClass(StrEnum):
    SOURCE = "SOURCE"
    MANUAL = "MANUAL"
    DERIVED = "DERIVED"
    LOOKED_UP = "LOOKED UP"
    ESTIMATED = "ESTIMATED"
    UNVERIFIED = "UNVERIFIED"
    UNREADABLE = "UNREADABLE"


class RawEntry(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    source_file: str
    source_page: str | None = None
    source_row: str | None = None
    source_entry_number: str | None = None
    date: Date | None = None
    airline: str | None = None
    flight_number: str | None = None
    route_sequence: list[str] = Field(default_factory=list)
    out_time: str | None = None
    in_time: str | None = None
    total_time: str | None = None
    registration: str | None = None
    aircraft_type: str | None = None
    pic_name: str | None = None
    pic_employee_id: str | None = None
    p1_us: str | None = None
    simulator_time: str | None = None
    approach: str | None = None
    visible_remark: str | None = None
    unreadable_fields: list[str] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)

    @field_validator("route_sequence", mode="before")
    @classmethod
    def normalize_route(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            cleaned = value.replace("–", " ").replace("—", " ").replace("-", " ")
            return [part.upper() for part in cleaned.split() if part]
        return [str(part).strip().upper() for part in value if str(part).strip()]


class ExtractionBatch(BaseModel):
    entries: list[RawEntry] = Field(default_factory=list)


class FlightSector(BaseModel):
    entry_number: int
    source_entry_number: str
    source_file: str
    source_page: str = EM_DASH
    source_row: str = EM_DASH
    date: Date | None = None
    aircraft_type: str = EM_DASH
    registration: str = EM_DASH
    flight_number: str = EM_DASH
    departure: str = EM_DASH
    arrival: str = EM_DASH
    out_time: str = EM_DASH
    in_time: str = EM_DASH
    total_time: str = EM_DASH
    pic_name: str = EM_DASH
    pic_employee_id: str = EM_DASH
    sic_name: str = EM_DASH
    p1_us: str = EM_DASH
    copilot_time: str = EM_DASH
    ifr: str = EM_DASH
    actual_ifr: str = EM_DASH
    simulator_time: str = EM_DASH
    approach: str = EM_DASH
    remark: str = ""


class ProvenanceRecord(BaseModel):
    entry_number: int
    date: Date | None = None
    route: str
    field_name: str
    final_value: str
    classification: ProvenanceClass
    source_used: str
    reasoning_or_calculation: str = ""
    website_or_document_reference: str = ""
    access_date: Date | None = None
    confidence_level: str = ""
    unresolved_issue: str = ""


class ValidationIssue(BaseModel):
    severity: str
    entry_number: int | None = None
    code: str
    message: str


class SourceInventoryItem(BaseModel):
    source_number: int
    filename: str
    file_type: str
    pages_or_sheets: str
    apparent_date_range: str
    source_priority: int
    description: str
    readability_status: str
    used: bool
    notes: str = ""
    sha256: str = ""


class AirportMapping(BaseModel):
    original_airport_code: str
    original_code_type: str
    final_icao_code: str
    airport_name: str
    country: str
    historical_code: str = ""
    current_code: str
    source: str
    access_date: Date | None = None
    notes: str = ""
