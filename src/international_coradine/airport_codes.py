from __future__ import annotations

import csv
import math
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .models import AirportMapping


ICAO_AIRPORT_PATTERN = re.compile(r"^[A-Z]{4}$")


@dataclass(frozen=True)
class Airport:
    iata: str
    icao: str
    name: str
    country: str
    latitude: float
    longitude: float
    historical_code: str = ""


class AirportDirectory:
    def __init__(self, seed_path: Path):
        self.by_iata: dict[str, Airport] = {}
        self.by_icao: dict[str, Airport] = {}
        with seed_path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                airport = Airport(
                    iata=row["iata"].upper(),
                    icao=row["icao"].upper(),
                    name=row["name"],
                    country=row["country"],
                    latitude=float(row["latitude"]),
                    longitude=float(row["longitude"]),
                    historical_code=row.get("historical_code", ""),
                )
                if not is_icao_airport_code(airport.icao):
                    raise ValueError(
                        f"Airport seed contains invalid ICAO code: {airport.icao!r}"
                    )
                self.by_iata[airport.iata] = airport
                self.by_icao[airport.icao] = airport

    def to_icao(self, code: str) -> tuple[str, AirportMapping]:
        normalized = code.strip().upper()
        if normalized in self.by_icao:
            airport = self.by_icao[normalized]
            code_type = "ICAO"
        elif normalized in self.by_iata:
            airport = self.by_iata[normalized]
            code_type = "IATA"
        else:
            raise KeyError(f"Unknown airport code: {normalized}")
        mapping = AirportMapping(
            original_airport_code=normalized,
            original_code_type=code_type,
            final_icao_code=airport.icao,
            airport_name=airport.name,
            country=airport.country,
            historical_code=airport.historical_code,
            current_code=airport.icao,
            source="Repository airport seed; verify against current AIP before official use",
            access_date=date.today(),
            notes="Public reference only; not regulator certification.",
        )
        return airport.icao, mapping

    def distance_km(self, code_a: str, code_b: str) -> float | None:
        a = self.by_icao.get(code_a) or self.by_iata.get(code_a)
        b = self.by_icao.get(code_b) or self.by_iata.get(code_b)
        if not a or not b:
            return None
        radius = 6371.0088
        lat1, lon1 = math.radians(a.latitude), math.radians(a.longitude)
        lat2, lon2 = math.radians(b.latitude), math.radians(b.longitude)
        dlat, dlon = lat2 - lat1, lon2 - lon1
        h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        return 2 * radius * math.asin(math.sqrt(h))


def is_icao_airport_code(value: str) -> bool:
    return bool(ICAO_AIRPORT_PATTERN.fullmatch(value.strip().upper()))
