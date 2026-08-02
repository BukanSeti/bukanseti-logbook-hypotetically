from __future__ import annotations

import re
from dataclasses import dataclass


ICAO_AIRCRAFT_TYPE_PATTERN = re.compile(r"^[A-Z0-9]{2,4}$")


@dataclass(frozen=True)
class ManualAircraftRecord:
    registration: str
    aircraft_type: str


class ManualAircraftDirectory:
    """Small in-memory directory built only from explicit user input."""

    def __init__(self, records: list[ManualAircraftRecord] | None = None):
        self._records = {
            record.registration: record
            for record in (records or [])
        }

    @classmethod
    def from_specs(cls, specs: list[str] | None) -> ManualAircraftDirectory:
        records = [parse_aircraft_spec(spec) for spec in (specs or [])]
        return cls(records)

    def lookup(self, registration: str | None) -> ManualAircraftRecord | None:
        if not registration:
            return None
        return self._records.get(normalize_registration(registration))


def parse_aircraft_spec(spec: str) -> ManualAircraftRecord:
    if "=" not in spec:
        raise ValueError(
            f"Invalid aircraft input {spec!r}. Use REGISTRATION=ICAO_TYPE, "
            "for example PK-LJF=B739."
        )
    registration_text, aircraft_type_text = spec.split("=", 1)
    registration = normalize_registration(registration_text)
    aircraft_type = standardize_aircraft_type(aircraft_type_text)
    if not registration or not aircraft_type:
        raise ValueError(
            f"Invalid aircraft input {spec!r}. Registration and ICAO aircraft type "
            "are required."
        )
    return ManualAircraftRecord(
        registration=registration,
        aircraft_type=aircraft_type,
    )


def normalize_registration(value: str) -> str:
    text = value.strip().upper().replace(" ", "")
    if text and not text.startswith("PK-") and len(text) == 3:
        text = f"PK-{text}"
    return text


def standardize_aircraft_type(value: str | None) -> str:
    """Return only an ICAO aircraft type designator.

    Common Boeing 737 marketing/model names are accepted as input, but the stored
    value is always the corresponding ICAO designator.
    """
    if not value:
        return ""

    original = " ".join(value.strip().upper().replace("_", "-").split())

    # The hyphenated Boeing model name 737-8 means MAX 8. Keep this check
    # before compact alias matching so it is not confused with the old B7378
    # shorthand used for a 737-800.
    if original in {
        "737-8",
        "B737-8",
        "BOEING 737-8",
        "737 8",
        "B737 8",
        "BOEING 737 8",
    }:
        return "B38M"

    alias_key = re.sub(r"[^A-Z0-9]", "", original)
    aliases = {
        # Boeing 737-900ER
        "B739": "B739",
        "B7379": "B739",
        "737900ER": "B739",
        "B737900ER": "B739",
        "BOEING737900ER": "B739",
        # Boeing 737-800 / 800NG
        "B738": "B738",
        "B7378": "B738",
        "737800": "B738",
        "737800NG": "B738",
        "B737800": "B738",
        "B737800NG": "B738",
        "BOEING737800": "B738",
        "BOEING737800NG": "B738",
        # Boeing 737 MAX 8
        "B38M": "B38M",
        "737MAX8": "B38M",
        "B737MAX8": "B38M",
        "BOEING737MAX8": "B38M",
    }
    if alias_key in aliases:
        return aliases[alias_key]

    if is_icao_aircraft_type(original):
        return original

    raise ValueError(
        f"Aircraft type {value!r} is not a recognized ICAO aircraft type designator. "
        "Use a code such as B738, B739, or B38M."
    )


def is_icao_aircraft_type(value: str) -> bool:
    return bool(ICAO_AIRCRAFT_TYPE_PATTERN.fullmatch(value.strip().upper()))
