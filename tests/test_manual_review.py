import json
from pathlib import Path

from international_coradine.models import FlightSector
from international_coradine.pipeline import _write_manual_review


def test_manual_review_requests_aircraft_and_preserves_crew_privacy(tmp_path: Path):
    destination = tmp_path / "manual_review.json"
    sector = FlightSector(
        entry_number=1,
        source_entry_number="SRC-0001",
        source_file="photo.jpg",
        registration="PK-LJF",
        aircraft_type="—",
        departure="WARR",
        arrival="WIII",
        pic_name="—",
        pic_employee_id="—",
    )

    document = _write_manual_review(destination, [sector])

    assert document["status"] == "needs_aircraft_input"
    assert document["aircraft_questions"][0]["rerun_example"] == "--aircraft PK-LJF=B739"
    assert document["unverified_crew_fields"][0]["fields"] == [
        "pic_name",
        "pic_employee_id",
    ]
    saved = json.loads(destination.read_text(encoding="utf-8"))
    assert "No Crew Bank" in saved["privacy_policy"]
