from datetime import date
from pathlib import Path

from international_coradine.airport_codes import AirportDirectory
from international_coradine.manual_aircraft import ManualAircraftDirectory
from international_coradine.models import ProvenanceClass, RawEntry
from international_coradine.reconstruction import Reconstructor
from international_coradine.time_utils import parse_duration_minutes


ROOT = Path(__file__).resolve().parents[1]


def test_split_three_sectors_preserves_exact_total_and_uses_icao_airports():
    entry = RawEntry(
        source_file="sample.jpg",
        date=date(2017, 1, 1),
        airline="Lion Air",
        route_sequence=["CGK", "SOC", "CGK", "SUB"],
        total_time="05:20",
        out_time="06:00",
        pic_name="Captain Example Pilot",
    )
    result = Reconstructor(
        owner_name="Adi Satria",
        airports=AirportDirectory(ROOT / "data" / "airport_seed.csv"),
    ).reconstruct([entry])
    assert len(result.sectors) == 3
    assert sum(
        parse_duration_minutes(sector.total_time) or 0
        for sector in result.sectors
    ) == 320
    assert [sector.departure for sector in result.sectors] == [
        "WIII",
        "WAHQ",
        "WIII",
    ]
    assert [sector.arrival for sector in result.sectors] == [
        "WAHQ",
        "WIII",
        "WARR",
    ]
    assert all(len(sector.departure) == 4 for sector in result.sectors)
    assert all(len(sector.arrival) == 4 for sector in result.sectors)
    assert all(sector.remark == "" for sector in result.sectors)


def test_manual_aircraft_type_overrides_photo_with_icao_designator():
    entry = RawEntry(
        source_file="sample.jpg",
        date=date(2026, 8, 2),
        airline="Lion Air",
        route_sequence=["SUB", "CGK"],
        total_time="01:20",
        registration="LJF",
        pic_name="Example Pilot",
    )
    result = Reconstructor(
        owner_name="Logbook Owner",
        airports=AirportDirectory(ROOT / "data" / "airport_seed.csv"),
        manual_aircraft=ManualAircraftDirectory.from_specs(
            ["PK-LJF=B737-900ER"]
        ),
    ).reconstruct([entry])

    sector = result.sectors[0]
    assert sector.registration == "PK-LJF"
    assert sector.aircraft_type == "B739"
    assert sector.departure == "WARR"
    assert sector.arrival == "WIII"
    aircraft_provenance = next(
        item for item in result.provenance if item.field_name == "Aircraft Type"
    )
    assert aircraft_provenance.classification == ProvenanceClass.MANUAL
    assert "--aircraft" in aircraft_provenance.source_used


def test_source_aircraft_model_is_normalized_to_icao_designator():
    entry = RawEntry(
        source_file="sample.jpg",
        date=date(2026, 8, 2),
        airline="Lion Air",
        route_sequence=["WARR", "WIII"],
        total_time="01:20",
        registration="PK-LJU",
        aircraft_type="B737-800NG",
        pic_name="Example Pilot",
    )
    result = Reconstructor(
        owner_name="Logbook Owner",
        airports=AirportDirectory(ROOT / "data" / "airport_seed.csv"),
    ).reconstruct([entry])

    assert result.sectors[0].aircraft_type == "B738"
    assert result.sectors[0].departure == "WARR"
    assert result.sectors[0].arrival == "WIII"


def test_missing_crew_id_is_not_looked_up_or_fabricated():
    entry = RawEntry(
        source_file="sample.jpg",
        date=date(2026, 8, 2),
        airline="Lion Air",
        route_sequence=["SUB", "CGK"],
        total_time="01:20",
        registration="LJF",
        pic_name="Example Pilot",
        pic_employee_id=None,
    )
    result = Reconstructor(
        owner_name="Logbook Owner",
        airports=AirportDirectory(ROOT / "data" / "airport_seed.csv"),
    ).reconstruct([entry])

    sector = result.sectors[0]
    assert sector.pic_name == "Example Pilot"
    assert sector.pic_employee_id == "—"
    crew_id_provenance = next(
        item for item in result.provenance if item.field_name == "PIC Employee ID"
    )
    assert crew_id_provenance.classification == ProvenanceClass.UNVERIFIED
    assert "no Crew Bank" in crew_id_provenance.unresolved_issue
