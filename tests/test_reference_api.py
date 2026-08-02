from fastapi.testclient import TestClient

from international_coradine.reference_api.app import create_app
from international_coradine.reference_api.security import (
    InMemoryRateLimiter,
    TokenAuthenticator,
    hash_token,
)
from international_coradine.reference_api.store import AircraftLookupResult, CrewLookupResult


class FakeStore:
    def lookup_crew(self, employee_id, full_name):
        if employee_id == "23133" or full_name == "Adriansyah Yusuf":
            return CrewLookupResult(employee_id="23133", full_name="Adriansyah Yusuf")
        return None

    def lookup_aircraft(self, registration):
        if registration.upper().replace("PK-", "") == "LJF":
            return AircraftLookupResult(registration="PK-LJF", aircraft_type="B737-900ER")
        return None


def client():
    app = create_app(
        store=FakeStore(),
        authenticator=TokenAuthenticator({"friend": hash_token("secret-token")}),
        limiter=InMemoryRateLimiter(10),
    )
    return TestClient(app)


def test_crew_response_is_minimal():
    response = client().post(
        "/v1/crew/lookup",
        headers={"Authorization": "Bearer secret-token"},
        json={"employee_id": "23133"},
    )
    assert response.status_code == 200
    assert response.json() == {"employee_id": "23133", "full_name": "Adriansyah Yusuf"}


def test_aircraft_response_is_minimal():
    response = client().post(
        "/v1/aircraft/lookup",
        headers={"Authorization": "Bearer secret-token"},
        json={"registration": "LJF"},
    )
    assert response.status_code == 200
    assert response.json() == {"registration": "PK-LJF", "aircraft_type": "B737-900ER"}


def test_authentication_required():
    response = client().post("/v1/crew/lookup", json={"employee_id": "23133"})
    assert response.status_code == 401


def test_bulk_endpoint_does_not_exist():
    response = client().get("/v1/crew/all", headers={"Authorization": "Bearer secret-token"})
    assert response.status_code == 404


def test_extra_request_fields_are_rejected():
    response = client().post(
        "/v1/crew/lookup",
        headers={"Authorization": "Bearer secret-token"},
        json={"employee_id": "23133", "atpl": "should-not-be-accepted"},
    )
    assert response.status_code == 422
