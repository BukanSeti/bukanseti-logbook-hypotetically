from international_coradine.models import FlightSector
from international_coradine.validation import validate


def _validate_sector(sector: FlightSector):
    return validate(
        [sector],
        provenance=[],
        original_source_entries=1,
        split_source_entries=0,
    )


def test_valid_icao_aircraft_and_airport_codes_pass():
    sector = FlightSector(
        entry_number=1,
        source_entry_number="SRC-0001",
        source_file="photo.jpg",
        aircraft_type="B739",
        departure="WARR",
        arrival="WIII",
    )

    result = _validate_sector(sector)

    assert not any(
        issue.code in {"INVALID_ICAO_AIRCRAFT_TYPE", "INVALID_ICAO_AIRPORT"}
        for issue in result.issues
    )


def test_expanded_aircraft_model_is_rejected_in_final_output():
    sector = FlightSector(
        entry_number=1,
        source_entry_number="SRC-0001",
        source_file="photo.jpg",
        aircraft_type="B737-900ER",
        departure="WARR",
        arrival="WIII",
    )

    result = _validate_sector(sector)

    assert any(
        issue.code == "INVALID_ICAO_AIRCRAFT_TYPE"
        for issue in result.issues
    )


def test_iata_airport_code_is_rejected_in_final_output():
    sector = FlightSector(
        entry_number=1,
        source_entry_number="SRC-0001",
        source_file="photo.jpg",
        aircraft_type="B738",
        departure="SUB",
        arrival="CGK",
    )

    result = _validate_sector(sector)

    assert sum(
        issue.code == "INVALID_ICAO_AIRPORT"
        for issue in result.issues
    ) == 2
