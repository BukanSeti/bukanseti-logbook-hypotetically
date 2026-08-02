from __future__ import annotations

from dataclasses import dataclass


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
            f"Invalid aircraft input {spec!r}. Use REGISTRATION=TYPE, for example PK-LJF=B739."
        )
    registration_text, aircraft_type_text = spec.split("=", 1)
    registration = normalize_registration(registration_text)
    aircraft_type = standardize_aircraft_type(aircraft_type_text)
    if not registration or not aircraft_type:
        raise ValueError(
            f"Invalid aircraft input {spec!r}. Registration and aircraft type are required."
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
    if not value:
        return ""
    normalized = value.strip().upper().replace("_", "-")
    if normalized in {"B7379", "B739", "737-900ER", "BOEING 737-900ER"}:
        return "B737-900ER"
    if normalized in {
        "B7378",
        "B738",
        "737-800",
        "737-800NG",
        "BOEING 737-800",
        "BOEING 737-800NG",
    }:
        return "B737-800NG"
    if normalized in {
        "B38M",
        "737-8",
        "737 MAX 8",
        "B737 MAX 8",
        "BOEING 737 MAX 8",
    }:
        return "B737 MAX 8"
    return value.strip()
