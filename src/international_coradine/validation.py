from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from .models import EM_DASH, FlightSector, ProvenanceRecord, ValidationIssue
from .time_utils import elapsed_minutes, parse_duration_minutes


@dataclass
class ValidationResult:
    summary: dict[str, object] = field(default_factory=dict)
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(issue.severity == "ERROR" for issue in self.issues)


def validate(
    sectors: list[FlightSector],
    provenance: list[ProvenanceRecord],
    original_source_entries: int,
    split_source_entries: int,
) -> ValidationResult:
    result = ValidationResult()
    source_total = _sum_unique_source_totals(provenance)
    final_total = sum(parse_duration_minutes(s.total_time) or 0 for s in sectors)
    fingerprints = Counter(
        (s.date, s.flight_number, s.departure, s.arrival, s.out_time, s.registration) for s in sectors
    )

    for sector in sectors:
        _validate_sector(sector, result)
    for fingerprint, count in fingerprints.items():
        if count > 1:
            result.issues.append(
                ValidationIssue(
                    severity="WARNING",
                    code="DUPLICATE_ENTRY",
                    message=f"Possible duplicate appears {count} times: {fingerprint}",
                )
            )

    class_counts = Counter(record.classification.value for record in provenance)
    unresolved = sum(bool(record.unresolved_issue) for record in provenance)
    result.summary = {
        "Number of original source entries": original_source_entries,
        "Number of final sector rows": len(sectors),
        "Number of split multi-sector entries": split_source_entries,
        "Total source flight time": _format_minutes(source_total),
        "Total final flight time": _format_minutes(final_total),
        "Difference between source and final totals": _format_signed(final_total - source_total),
        "Number of unreadable fields": class_counts.get("UNREADABLE", 0),
        "Number of estimated fields": class_counts.get("ESTIMATED", 0),
        "Number of looked-up fields": class_counts.get("LOOKED UP", 0),
        "Number of unverified fields": class_counts.get("UNVERIFIED", 0),
        "Number of unresolved items": unresolved,
        "Formula errors": 0,
        "Chronological errors": sum(issue.code == "TIME_MISMATCH" for issue in result.issues),
        "Duplicate entries": sum(issue.code == "DUPLICATE_ENTRY" for issue in result.issues),
        "Validation errors": sum(issue.severity == "ERROR" for issue in result.issues),
        "Validation warnings": sum(issue.severity == "WARNING" for issue in result.issues),
    }
    return result


def _validate_sector(sector: FlightSector, result: ValidationResult) -> None:
    if sector.remark:
        result.issues.append(
            ValidationIssue(severity="ERROR", entry_number=sector.entry_number, code="REMARK_NOT_BLANK", message="Remark must remain blank")
        )
    if sector.simulator_time != EM_DASH:
        forbidden = [sector.total_time, sector.ifr, sector.actual_ifr, sector.copilot_time, sector.p1_us]
        if any(value != EM_DASH for value in forbidden):
            result.issues.append(
                ValidationIssue(
                    severity="ERROR",
                    entry_number=sector.entry_number,
                    code="SIMULATOR_FLIGHT_TIME",
                    message="Simulator entry carries prohibited flight-operation time",
                )
            )
        return

    total = parse_duration_minutes(sector.total_time)
    ifr = parse_duration_minutes(sector.ifr)
    actual = parse_duration_minutes(sector.actual_ifr)
    copilot = parse_duration_minutes(sector.copilot_time)
    p1us = parse_duration_minutes(sector.p1_us)

    if total is not None and (ifr != total or actual != total):
        result.issues.append(
            ValidationIssue(
                severity="ERROR",
                entry_number=sector.entry_number,
                code="IFR_EQUALITY",
                message="TOTAL TIME, IFR, and ACTUAL IFR must be equal",
            )
        )
    elapsed = elapsed_minutes(sector.out_time, sector.in_time)
    if total is not None and elapsed is not None and elapsed != total:
        result.issues.append(
            ValidationIssue(
                severity="ERROR",
                entry_number=sector.entry_number,
                code="TIME_MISMATCH",
                message=f"IN minus OUT is {elapsed} minutes but Total Time is {total} minutes",
            )
        )
    if p1us is not None and copilot is None:
        result.issues.append(
            ValidationIssue(severity="ERROR", entry_number=sector.entry_number, code="P1US_WITHOUT_COPILOT", message="P1 U/S exists without Copilot Time")
        )
    if p1us is not None and copilot is not None and p1us > copilot:
        result.issues.append(
            ValidationIssue(severity="ERROR", entry_number=sector.entry_number, code="P1US_EXCEEDS_COPILOT", message="P1 U/S exceeds Copilot Time")
        )
    if copilot is not None and total is not None and copilot > total:
        result.issues.append(
            ValidationIssue(severity="ERROR", entry_number=sector.entry_number, code="COPILOT_EXCEEDS_TOTAL", message="Copilot Time exceeds Total Time")
        )
    if sector.departure != EM_DASH and sector.arrival != EM_DASH and sector.departure == sector.arrival:
        result.issues.append(
            ValidationIssue(severity="WARNING", entry_number=sector.entry_number, code="SAME_AIRPORT", message="Departure and arrival are identical")
        )
    if len(sector.departure) not in {1, 4} or len(sector.arrival) not in {1, 4}:
        result.issues.append(
            ValidationIssue(severity="ERROR", entry_number=sector.entry_number, code="INVALID_ICAO", message="Route contains a non-ICAO code")
        )


def _sum_unique_source_totals(provenance: list[ProvenanceRecord]) -> int:
    totals_by_source: dict[str, int] = {}
    for record in provenance:
        if record.field_name != "Total Time":
            continue
        source_key = record.source_used
        value = parse_duration_minutes(record.final_value)
        if value is None:
            continue
        if record.classification.value == "SOURCE":
            totals_by_source[source_key] = value
        else:
            totals_by_source[source_key] = totals_by_source.get(source_key, 0) + value
    return sum(totals_by_source.values())


def _format_minutes(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def _format_signed(minutes: int) -> str:
    sign = "-" if minutes < 0 else ""
    value = abs(minutes)
    return f"{sign}{value // 60:02d}:{value % 60:02d}"
