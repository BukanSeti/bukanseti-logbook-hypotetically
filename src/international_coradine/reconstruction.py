from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from .airport_codes import AirportDirectory
from .lion_air_guard import assert_lion_air
from .models import (
    EM_DASH,
    AirportMapping,
    FlightSector,
    ProvenanceClass,
    ProvenanceRecord,
    RawEntry,
)
from .references import AircraftBank, CrewBank
from .time_utils import add_minutes, format_duration, parse_duration_minutes, subtract_minutes


@dataclass
class ReconstructionResult:
    sectors: list[FlightSector] = field(default_factory=list)
    provenance: list[ProvenanceRecord] = field(default_factory=list)
    airport_mappings: list[AirportMapping] = field(default_factory=list)
    split_source_entries: int = 0


class Reconstructor:
    def __init__(
        self,
        owner_name: str,
        airports: AirportDirectory,
        crew_bank: CrewBank | None = None,
        aircraft_bank: AircraftBank | None = None,
        turnaround_minutes: int = 45,
    ):
        self.owner_name = owner_name.strip()
        self.airports = airports
        self.crew_bank = crew_bank
        self.aircraft_bank = aircraft_bank
        self.turnaround_minutes = turnaround_minutes
        if not self.owner_name or self.owner_name == "[INSERT FULL NAME]":
            raise ValueError("Exact LOGBOOK OWNER NAME is required")

    def reconstruct(self, entries: list[RawEntry]) -> ReconstructionResult:
        result = ReconstructionResult()
        next_entry_number = 1
        for source_index, raw in enumerate(entries, start=1):
            assert_lion_air(raw.airline, raw.flight_number)
            source_entry = raw.source_entry_number or f"SRC-{source_index:04d}"
            route, mappings = self._convert_route(raw)
            result.airport_mappings.extend(mappings)
            if raw.simulator_time and len(route) < 2:
                sector = self._simulator_sector(raw, source_entry, next_entry_number)
                result.sectors.append(sector)
                result.provenance.extend(self._provenance_for_sector(sector, raw, route, 0, 1))
                next_entry_number += 1
                continue
            if len(route) < 2:
                route = [EM_DASH, EM_DASH]
            sector_pairs = list(zip(route, route[1:], strict=False))
            if not sector_pairs:
                sector_pairs = [(EM_DASH, EM_DASH)]
            if len(sector_pairs) > 1:
                result.split_source_entries += 1
            allocations = self._allocate_minutes(raw.total_time, sector_pairs)
            clock = raw.out_time
            for pair_index, ((departure, arrival), minutes) in enumerate(
                zip(sector_pairs, allocations, strict=False)
            ):
                sector = self._flight_sector(
                    raw=raw,
                    source_entry=source_entry,
                    entry_number=next_entry_number,
                    departure=departure,
                    arrival=arrival,
                    minutes=minutes,
                    pair_index=pair_index,
                    pair_count=len(sector_pairs),
                    clock=clock,
                )
                result.sectors.append(sector)
                result.provenance.extend(
                    self._provenance_for_sector(sector, raw, route, pair_index, len(sector_pairs))
                )
                if sector.in_time != EM_DASH:
                    clock = add_minutes(sector.in_time, self.turnaround_minutes)
                next_entry_number += 1
        result.airport_mappings = _dedupe_mappings(result.airport_mappings)
        return result

    def _convert_route(self, raw: RawEntry) -> tuple[list[str], list[AirportMapping]]:
        converted: list[str] = []
        mappings: list[AirportMapping] = []
        for code in raw.route_sequence:
            try:
                icao, mapping = self.airports.to_icao(code)
                converted.append(icao)
                mappings.append(mapping)
            except KeyError:
                converted.append(EM_DASH)
        return converted, mappings

    def _allocate_minutes(self, total_time: str | None, pairs: list[tuple[str, str]]) -> list[int | None]:
        total = parse_duration_minutes(total_time)
        if total is None:
            return [None] * len(pairs)
        if len(pairs) == 1:
            return [total]
        weights = []
        for departure, arrival in pairs:
            distance = self.airports.distance_km(departure, arrival)
            weights.append((distance if distance is not None else 500.0) + 150.0)
        exact = [total * weight / sum(weights) for weight in weights]
        floors = [max(1, int(value)) for value in exact]
        difference = total - sum(floors)
        remainders = sorted(
            range(len(exact)), key=lambda idx: exact[idx] - int(exact[idx]), reverse=True
        )
        cursor = 0
        while difference > 0:
            floors[remainders[cursor % len(remainders)]] += 1
            difference -= 1
            cursor += 1
        while difference < 0:
            candidates = [idx for idx, value in enumerate(floors) if value > 1]
            if not candidates:
                raise ValueError("Combined time is too short for the number of operated sectors")
            floors[candidates[cursor % len(candidates)]] -= 1
            difference += 1
            cursor += 1
        return floors

    def _flight_sector(
        self,
        raw: RawEntry,
        source_entry: str,
        entry_number: int,
        departure: str,
        arrival: str,
        minutes: int | None,
        pair_index: int,
        pair_count: int,
        clock: str | None,
    ) -> FlightSector:
        duration = format_duration(minutes)
        if pair_count == 1:
            out_time = raw.out_time or (subtract_minutes(raw.in_time, minutes) if minutes is not None else EM_DASH)
            in_time = raw.in_time or (add_minutes(out_time, minutes) if minutes is not None else EM_DASH)
        else:
            out_time = clock or EM_DASH
            in_time = add_minutes(out_time, minutes) if minutes is not None else EM_DASH

        registration = (raw.registration or EM_DASH).upper()
        aircraft_type = _standardize_type(raw.aircraft_type)
        if self.aircraft_bank and registration != EM_DASH:
            aircraft = self.aircraft_bank.lookup(registration)
            if aircraft:
                registration = aircraft.registration
                aircraft_type = _standardize_type(aircraft.type_of_aircraft or aircraft.icao_type)

        pic_name = _clean_pic_name(raw.pic_name) if raw.pic_name else EM_DASH
        pic_id = raw.pic_employee_id or EM_DASH
        if self.crew_bank and (raw.pic_name or raw.pic_employee_id):
            crew = self.crew_bank.lookup(raw.pic_name, raw.pic_employee_id)
            if crew:
                pic_name = crew.name
                pic_id = crew.employee_id or EM_DASH

        owner_is_pic = pic_name != EM_DASH and pic_name.casefold() == self.owner_name.casefold()
        sic_name = EM_DASH if owner_is_pic or pic_name == EM_DASH else self.owner_name
        copilot = duration if sic_name != EM_DASH and duration != EM_DASH else EM_DASH
        p1_us = raw.p1_us or EM_DASH

        return FlightSector(
            entry_number=entry_number,
            source_entry_number=source_entry,
            source_file=raw.source_file,
            source_page=raw.source_page or EM_DASH,
            source_row=raw.source_row or EM_DASH,
            date=raw.date,
            aircraft_type=aircraft_type,
            registration=registration,
            flight_number=raw.flight_number or EM_DASH,
            departure=departure,
            arrival=arrival,
            out_time=out_time or EM_DASH,
            in_time=in_time or EM_DASH,
            total_time=duration,
            pic_name=pic_name,
            pic_employee_id=pic_id,
            sic_name=sic_name,
            p1_us=p1_us,
            copilot_time=copilot,
            ifr=duration,
            actual_ifr=duration,
            simulator_time=EM_DASH,
            approach=raw.approach or EM_DASH,
            remark="",
        )

    def _simulator_sector(self, raw: RawEntry, source_entry: str, entry_number: int) -> FlightSector:
        return FlightSector(
            entry_number=entry_number,
            source_entry_number=source_entry,
            source_file=raw.source_file,
            source_page=raw.source_page or EM_DASH,
            source_row=raw.source_row or EM_DASH,
            date=raw.date,
            aircraft_type=_standardize_type(raw.aircraft_type),
            registration=EM_DASH,
            flight_number=EM_DASH,
            departure=EM_DASH,
            arrival=EM_DASH,
            out_time=EM_DASH,
            in_time=EM_DASH,
            total_time=EM_DASH,
            pic_name=EM_DASH,
            pic_employee_id=EM_DASH,
            sic_name=EM_DASH,
            p1_us=EM_DASH,
            copilot_time=EM_DASH,
            ifr=EM_DASH,
            actual_ifr=EM_DASH,
            simulator_time=raw.simulator_time or EM_DASH,
            approach=EM_DASH,
            remark="",
        )

    def _provenance_for_sector(
        self,
        sector: FlightSector,
        raw: RawEntry,
        route: list[str],
        pair_index: int,
        pair_count: int,
    ) -> list[ProvenanceRecord]:
        route_text = f"{sector.departure} – {sector.arrival}"
        records: list[ProvenanceRecord] = []

        def add(field: str, value: str, classification: ProvenanceClass, reason: str = "", issue: str = ""):
            records.append(
                ProvenanceRecord(
                    entry_number=sector.entry_number,
                    date=sector.date,
                    route=route_text,
                    field_name=field,
                    final_value=value,
                    classification=classification,
                    source_used=f"{raw.source_file} page {raw.source_page or EM_DASH} row {raw.source_row or EM_DASH}",
                    reasoning_or_calculation=reason,
                    confidence_level=f"{raw.confidence:.0%}",
                    unresolved_issue=issue,
                )
            )

        for field, value, present in (
            ("Date", str(sector.date or EM_DASH), raw.date is not None),
            ("Flight Number", sector.flight_number, raw.flight_number is not None),
            ("Registration", sector.registration, raw.registration is not None),
            ("PIC Name", sector.pic_name, raw.pic_name is not None),
            ("PIC Employee ID", sector.pic_employee_id, raw.pic_employee_id is not None),
            ("Approach", sector.approach, raw.approach is not None),
        ):
            if field.casefold().replace(" ", "_") in raw.unreadable_fields:
                add(field, value, ProvenanceClass.UNREADABLE, issue="Source field is not reliably readable")
            else:
                add(
                    field,
                    value,
                    ProvenanceClass.SOURCE if present else ProvenanceClass.UNVERIFIED,
                    issue="Missing and not defensibly reconstructed" if not present else "",
                )

        route_class = ProvenanceClass.DERIVED if any(len(code) == 3 for code in raw.route_sequence) else ProvenanceClass.SOURCE
        add("Route", route_text, route_class, "IATA converted to ICAO; multi-airport sequence split into sectors")

        time_class = ProvenanceClass.SOURCE if pair_count == 1 and raw.total_time else ProvenanceClass.ESTIMATED
        time_reason = "Preserved source total" if time_class == ProvenanceClass.SOURCE else (
            f"Allocated combined {raw.total_time or EM_DASH} across {pair_count} sectors using distance plus short-sector overhead; exact minute sum preserved"
        )
        add("Total Time", sector.total_time, time_class, time_reason)
        add("IFR", sector.ifr, ProvenanceClass.DERIVED, "IFR equals Total Time by project rule")
        add("ACTUAL IFR", sector.actual_ifr, ProvenanceClass.DERIVED, "ACTUAL IFR equals Total Time by project rule")
        add(
            "OUT",
            sector.out_time,
            ProvenanceClass.SOURCE if pair_count == 1 and raw.out_time else ProvenanceClass.ESTIMATED,
            "Reconstructed from source clock, sector duration, and turnaround sequencing" if not (pair_count == 1 and raw.out_time) else "",
        )
        add(
            "IN",
            sector.in_time,
            ProvenanceClass.SOURCE if pair_count == 1 and raw.in_time else ProvenanceClass.ESTIMATED,
            "Reconstructed from OUT plus sector duration" if not (pair_count == 1 and raw.in_time) else "",
        )
        add(
            "Aircraft Type",
            sector.aircraft_type,
            ProvenanceClass.SOURCE if raw.aircraft_type else (ProvenanceClass.LOOKED_UP if sector.aircraft_type != EM_DASH else ProvenanceClass.UNVERIFIED),
            "Matched against Lion Air Airplane reference bank" if not raw.aircraft_type and sector.aircraft_type != EM_DASH else "",
        )
        add(
            "SIC Name",
            sector.sic_name,
            ProvenanceClass.DERIVED if sector.sic_name != EM_DASH else ProvenanceClass.UNVERIFIED,
            "Logbook owner entered as SIC because another PIC is recorded" if sector.sic_name != EM_DASH else "Role cannot be confirmed",
        )
        add(
            "Copilot Time",
            sector.copilot_time,
            ProvenanceClass.DERIVED if sector.copilot_time != EM_DASH else ProvenanceClass.UNVERIFIED,
            "Copilot Time equals Total Time when owner is SIC" if sector.copilot_time != EM_DASH else "",
        )
        add(
            "P1 U/S",
            sector.p1_us,
            ProvenanceClass.SOURCE if raw.p1_us else ProvenanceClass.UNVERIFIED,
            issue="Not reconstructed without explicit authorization" if not raw.p1_us else "",
        )
        return records


def _standardize_type(value: str | None) -> str:
    if not value:
        return EM_DASH
    normalized = value.strip().upper().replace("_", "-")
    if normalized in {"B7379", "B739", "737-900ER", "BOEING 737-900ER"}:
        return "B737-900ER"
    if normalized in {"B7378", "B738", "737-800", "737-800NG", "BOEING 737-800", "BOEING 737-800NG"}:
        return "B737-800NG"
    return value.strip()


def _clean_pic_name(name: str | None) -> str:
    if not name:
        return EM_DASH
    cleaned = name.strip()
    upper = cleaned.upper()
    for prefix in ("CAPTAIN ", "CAPT ", "CPT "):
        if upper.startswith(prefix):
            return cleaned[len(prefix) :].strip()
    return cleaned


def _dedupe_mappings(mappings: list[AirportMapping]) -> list[AirportMapping]:
    seen = set()
    output = []
    for mapping in mappings:
        key = (mapping.original_airport_code, mapping.final_icao_code)
        if key not in seen:
            seen.add(key)
            output.append(mapping)
    return output
