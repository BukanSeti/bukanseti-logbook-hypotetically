import pytest

from international_coradine.reference_client import ReferenceApiClient, ReferenceApiError


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.last = None

    def post(self, url, json, headers, timeout):
        self.last = (url, json, headers, timeout)
        return self.response


def test_client_maps_minimal_crew_response():
    session = FakeSession(
        FakeResponse(
            200,
            {"employee_id": "23133", "full_name": "Adriansyah Yusuf"},
        )
    )
    client = ReferenceApiClient("https://api.example", "token", session=session)
    record = client.lookup_crew(employee_id="23133")
    assert record.employee_id == "23133"
    assert record.name == "Adriansyah Yusuf"
    assert set(session.last[1]) == {"employee_id"}


def test_client_rejects_extra_crew_fields():
    session = FakeSession(
        FakeResponse(
            200,
            {"employee_id": "1", "full_name": "A", "atpl": "x"},
        )
    )
    client = ReferenceApiClient("https://api.example", "token", session=session)
    with pytest.raises(ReferenceApiError):
        client.lookup_crew(employee_id="1")


def test_client_maps_minimal_aircraft_response():
    session = FakeSession(
        FakeResponse(
            200,
            {"registration": "PK-LJF", "aircraft_type": "B737-900ER"},
        )
    )
    client = ReferenceApiClient("https://api.example", "token", session=session)
    record = client.lookup_aircraft("LJF")
    assert record.registration == "PK-LJF"
    assert record.type_of_aircraft == "B737-900ER"
