from __future__ import annotations

import re


class NonLionAirDataError(ValueError):
    pass


_ALLOWED_AIRLINE_NAMES = {"LION AIR", "LIONAIR"}
_REJECTED_HINTS = {
    "BATIK",
    "WINGS",
    "SUPER AIR JET",
    "GARUDA",
    "CITILINK",
    "AIRASIA",
    "SRIWIJAYA",
    "NAM AIR",
}


def normalize_airline(value: str | None) -> str:
    if not value:
        return "LION AIR"
    return re.sub(r"\s+", " ", value.strip().upper())


def assert_lion_air(airline: str | None, flight_number: str | None = None) -> None:
    normalized = normalize_airline(airline)
    if normalized in _ALLOWED_AIRLINE_NAMES:
        return
    if any(hint in normalized for hint in _REJECTED_HINTS):
        raise NonLionAirDataError(f"Rejected non-Lion Air airline: {airline}")
    number = (flight_number or "").strip().upper()
    if number.startswith("JT") or number.startswith("LNI"):
        return
    raise NonLionAirDataError(
        f"Airline cannot be confirmed as Lion Air: airline={airline!r}, flight_number={flight_number!r}"
    )


def assert_lion_air_operator(operator: str | None) -> None:
    if normalize_airline(operator) not in _ALLOWED_AIRLINE_NAMES:
        raise NonLionAirDataError(f"Aircraft operator is not Lion Air: {operator!r}")
