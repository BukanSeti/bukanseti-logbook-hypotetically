import pytest

from international_coradine.manual_aircraft import (
    ManualAircraftDirectory,
    parse_aircraft_spec,
)


def test_manual_aircraft_normalizes_registration_and_type():
    record = parse_aircraft_spec("ljf=B739")
    assert record.registration == "PK-LJF"
    assert record.aircraft_type == "B737-900ER"


def test_manual_aircraft_supports_max_8():
    directory = ManualAircraftDirectory.from_specs(["PK-LAB=B38M"])
    record = directory.lookup("LAB")
    assert record is not None
    assert record.aircraft_type == "B737 MAX 8"


def test_manual_aircraft_rejects_invalid_format():
    with pytest.raises(ValueError):
        parse_aircraft_spec("PK-LJF")
