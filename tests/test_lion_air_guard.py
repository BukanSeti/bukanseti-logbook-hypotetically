import pytest

from international_coradine.lion_air_guard import NonLionAirDataError, assert_lion_air


def test_accepts_lion_air_name():
    assert_lion_air("Lion Air", "123")


def test_accepts_lion_air_prefix_when_airline_unknown():
    assert_lion_air(None, "JT610")
    assert_lion_air("Unknown", "LNI123")


def test_rejects_other_airline():
    with pytest.raises(NonLionAirDataError):
        assert_lion_air("Batik Air", "ID123")
