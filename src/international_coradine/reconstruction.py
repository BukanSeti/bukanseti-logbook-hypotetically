from __future__ import annotations

from dataclasses import dataclass, field

from .airport_codes import AirportDirectory
from .lion_air_guard import assert_lion_air
from .manual_aircraft import (
    ManualAircraftDirectory,
    normalize_registration,
    standardize_aircraft_type,
)
from .models import (
    EM_DASH,
    AirportMapping,
    FlightSector,
    ProvenanceClass,
    ProvenanceRecord,
    RawEntry,
)
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
        manual_aircraft: ManualAircraftDirectory | None = None,
        turnaround_minutes: int = 45,
    ):
        self.owner_name = owner_name.strip()
        self.airports = airports
        self.manual_aircraft = manual_aircraft or ManualAircraftDirectory()
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
                result.provenance.extend(self._provenance_for_sector(sector, raw, 1))
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
            for (departure, arrival), minutes in zip(sector_pairs, allocations, strict=False):
                sector = self._flight_sector(
                    raw=raw,
                    source_entry=source_entry,
                    entry_number=next_entry_number,
                    departure=departure,
                    arrival=arrival,
                    minutes=minutes,
                    pair_count=len(sector_pairs),
                    clock=clock,
                )
                result.sectors.append(sector)
                result.provenance.extend(
                    self._provenance_for_sector(sector, raw, len(sector_pairs))
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

    def _allocate_minutes(
        self,
        total_time: str | None,
        pairs: list[tuple[str, str]],
    ) -> list[int | None]:
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
            range(len(exact)),
            key=lambda index: exact[index] - int(exact[index]),
            reverse=True,
        )
        cursor = 0
        while difference > 0:
            floors[remainders[cursor % len(remainders)]] += 1
            difference -= 1
            cursor += 1
        while difference < 0:
            candidates = [index for index, value in enumerate(floors) if value > 1]
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
        pair_count: int,
        clock: str | None,
    ) -> FlightSector:
        duration = format_duration(minutes)
        if pair_count == 1:
            out_time = raw.out_time or (
                subtract_minutes(raw.in_time, minutes)
                if minutes is not None
                else EM_DASH
            )
            in_time = raw.in_time or (
                add_minutes(out_time, minutes)
                if minutes is not None
                else EM_DASH
            )
        else:
            out_time = clock or EM_DASH
            in_time = add_minutes(out_time, minutes) if minutes is not None else EM_DASH

        registration = normalize_registration(raw.registration) if raw.registration else EM_DASH
        aircraft_type = standardize_aircraft_type(raw.aircraft_type) or EM_DASH
        manual_record = self.manual_aircraft.lookup(raw.registration)
        if manual_record:
            registration = manual_record.registration
            aircraft_type = manual_record.aircraft_type

        # Crew data is source-only. This repository never accesses a Crew Bank or directory.
        pic_name = _clean_pic_name(raw.pic_name) if raw.pic_name else EM_DASH
        pic_id = raw.pic_employee_id or EM_DASH

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

    def _simulator_sector(
        self,
        raw: RawEntry,
        source_entry: str,
        entry_number: int,
    ) -> FlightSector:
        return FlightSector(
            entry_number=entry_number,
            source_entry_number=source_entry,
            source_file=raw.source_file,
            source_page=raw.source_page or EM_DASH,
            source_row=raw.source_row or EM_DASH,
            date=raw.date,
            aircraft_type=standardize_aircraft_type(raw.aircraft_type) or EM_DASH,
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
        pair_count: int,
    ) -> list[ProvenanceRecord]:
        route_text = f"{sector.departure} – {sector.arrival}"
        records: list[ProvenanceRecord] = []
        photo_source = (
            f"{raw.source_file} page {raw.source_page or EM_DASH} "
            f"row {raw.source_row or EM_DASH}"
        )

        def add(
            field_name: str,
            value: str,
            classification: ProvenanceClass,
            reason: str = "",
            issue: str = "",
            source_used: str | None = None,
        ) -> None:
            records.append(
                ProvenanceRecord(
                    entry_number=sector.entry_number,
                    date=sector.date,
                    route=route_text,
                    field_name=field_name,
                    final_value=value,
                    classification=classification,
                    source_used=source_used or photo_source,
                    reasoning_or_calculation=reason,
                    confidence_level=f"{raw.confidence:.0%}",
                    unresolved_issue=issue,
                )
            )

        for field_name, value, present in (
            ("Date", str(sector.date or EM_DASH), raw.date is not None),
            ("Flight Number", sector.flight_number, raw.flight_number is not None),
            ("Registration", sector.registration, raw.registration is not None),
            ("PIC Name", sector.pic_name, raw.pic_name is not None),
            ("PIC Employee ID", sector.pic_employee_id, raw.pic_employee_id is not None),
            ("Approach", sector.approach, raw.approach is not None),
        ):
            normalized_field = field_name.casefold().replace(" ", "_")
            if normalized_field in raw.unreadable_fields:
                add(
                    field_name,
                    value,
                    ProvenanceClass.UNREADABLE,
                    issue="Source field is not reliably readable",
                )
            else:
                missing_issue = ""
                if not present:
                    missing_issue = "Missing and not defensibly reconstructed"
                    if field_name in {"PIC Name", "PIC Employee ID"}:
                        missing_issue = (
                            "Missing in the photo; no Crew Bank or external crew lookup is used"
                        )
                add(
                    field_name,
                    value,
                    ProvenanceClass.SOURCE if present else ProvenanceClass.UNVERIFIED,
                    issue=missing_issue,
                )

        route_class = (
            ProvenanceClass.DERIVED
            if any(len(code) == 3 for code in raw.route_sequence)
            else ProvenanceClass.SOURCE
        )
        add(
            "Route",
            route_text,
            route_class,
            "IATA converted to ICAO; multi-airport sequence split into sectors",
        )

        time_class = (
            ProvenanceClass.SOURCE
            if pair_count == 1 and raw.total_time
            else ProvenanceClass.ESTIMATED
        )
        time_reason = (
            "Preserved source total"
            if time_class == ProvenanceClass.SOURCE
            else (
                f"Allocated combined {raw.total_time or EM_DASH} across {pair_count} sectors "
                "using distance plus short-sector overhead; exact minute sum preserved"
            )
        )
        add("Total Time", sector.total_time, time_class, time_reason)
        add("IFR", sector.ifr, ProvenanceClass.DERIVED, "IFR equals Total Time by project rule")
        add(
            "ACTUAL IFR",
            sector.actual_ifr,
            ProvenanceClass.DERIVED,
            "ACTUAL IFR equals Total Time by project rule",
        )
        add(
            "OUT",
            sector.out_time,
            ProvenanceClass.SOURCE
            if pair_count == 1 and raw.out_time
            else ProvenanceClass.ESTIMATED,
            "Reconstructed from source clock, sector duration, and turnaround sequencing"
            if not (pair_count == 1 and raw.out_time)
            else "",
        )
        add(
            "IN",
            sector.in_time,
            ProvenanceClass.SOURCE
            if pair_count == 1 and raw.in_time
            else ProvenanceClass.ESTIMATED,
            "Reconstructed from OUT plus sector duration"
            if not (pair_count == 1 and raw.in_time)
            else "",
        )

        manual_record = self.manual_aircraft.lookup(raw.registration)
        if manual_record:
            add(
                "Aircraft Type",
                sector.aircraft_type,
                ProvenanceClass.MANUAL,
                "Aircraft type supplied explicitly by the user; no Aircraft Bank or API used",
                source_used="Command-line --aircraft override",
            )
        elif raw.aircraft_type:
            add("Aircraft Type", sector.aircraft_type, ProvenanceClass.SOURCE)
        else:
            add(
                "Aircraft Type",
                sector.aircraft_type,
                ProvenanceClass.UNVERIFIED,
                issue="Provide registration and aircraft type manually when available",
            )

        add(
            "SIC Name",
            sector.sic_name,
            ProvenanceClass.DERIVED
            if sector.sic_name != EM_DASH
            else ProvenanceClass.UNVERIFIED,
            "Logbook owner entered as SIC because another PIC is recorded"
            if sector.sic_name != EM_DASH
            else "Role cannot be confirmed from the photo",
        )
        add(
            "Copilot Time",
            sector.copilot_time,
            ProvenanceClass.DERIVED
            if sector.copilot_time != EM_DASH
            else ProvenanceClass.UNVERIFIED,
            "Copilot Time equals Total Time when owner is SIC"
            if sector.copilot_time != EM_DASH
            else "",
        )
        add(
            "P1 U/S",
            sector.p1_us,
            ProvenanceClass.SOURCE if raw.p1_us else ProvenanceClass.UNVERIFIED,
            issue="Not reconstructed without explicit source or authorization"
            if not raw.p1_us
            else "",
        )
        return records


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
