import pytest

from international_coradine.manual_aircraft import (
    ManualAircraftDirectory,
    parse_aircraft_spec,
    standardize_aircraft_type,
)


def test_manual_aircraft_normalizes_registration_and_type_to_icao():
    record = parse_aircraft_spec("ljf=B737-900ER")
    assert record.registration == "PK-LJF"
    assert record.aircraft_type == "B739"


def test_manual_aircraft_supports_max_8_icao_designator():
    directory = ManualAircraftDirectory.from_specs(["PK-LAB=B737 MAX 8"])
    record = directory.lookup("LAB")
    assert record is not None
    assert record.aircraft_type == "B38M"


def test_common_boeing_737_names_map_to_icao_designators():
    assert standardize_aircraft_type("B737-800NG") == "B738"
    assert standardize_aircraft_type("B737-900ER") == "B739"
    assert standardize_aircraft_type("737-8") == "B38M"


def test_other_valid_icao_aircraft_type_is_preserved():
    assert standardize_aircraft_type("A320") == "A320"


def test_manual_aircraft_rejects_invalid_format():
    with pytest.raises(ValueError):
        parse_aircraft_spec("PK-LJF")


def test_expanded_unknown_aircraft_name_is_rejected():
    with pytest.raises(ValueError):
        standardize_aircraft_type("UNKNOWN AIRCRAFT MODEL")
