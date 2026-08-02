from international_coradine.models import FlightSector
from international_coradine.validation import validate


def test_validation_detects_time_mismatch():
    sector = FlightSector(
        entry_number=1,
        source_entry_number="SRC-1",
        source_file="sample",
        departure="WIII",
        arrival="WARR",
        out_time="10:00",
        in_time="11:00",
        total_time="01:10",
        ifr="01:10",
        actual_ifr="01:10",
    )
    result = validate([sector], [], 1, 0)
    assert any(issue.code == "TIME_MISMATCH" for issue in result.issues)
