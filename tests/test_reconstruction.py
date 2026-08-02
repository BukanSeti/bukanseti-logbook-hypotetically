from datetime import date
from pathlib import Path

from international_coradine.airport_codes import AirportDirectory
from international_coradine.models import RawEntry
from international_coradine.reconstruction import Reconstructor
from international_coradine.time_utils import parse_duration_minutes


ROOT = Path(__file__).resolve().parents[1]


def test_split_three_sectors_preserves_exact_total():
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
    assert sum(parse_duration_minutes(s.total_time) or 0 for s in result.sectors) == 320
    assert [s.departure for s in result.sectors] == ["WIII", "WAHQ", "WIII"]
    assert [s.arrival for s in result.sectors] == ["WAHQ", "WIII", "WARR"]
    assert all(s.remark == "" for s in result.sectors)
