from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

from .references import AircraftRecord, CrewRecord


class ReferenceApiError(RuntimeError):
    pass


@dataclass
class ReferenceApiClient:
    base_url: str
    token: str
    timeout_seconds: float = 15.0
    session: Any | None = None

    def __post_init__(self) -> None:
        self.base_url = self.base_url.rstrip("/")
        self.session = self.session or requests.Session()

    def _post(self, path: str, payload: dict[str, str]) -> dict[str, str] | None:
        response = self.session.post(
            f"{self.base_url}{path}",
            json=payload,
            headers={"Authorization": f"Bearer {self.token}"},
            timeout=self.timeout_seconds,
        )
        if response.status_code == 404:
            return None
        if response.status_code >= 400:
            raise ReferenceApiError(
                f"Reference API request failed with HTTP {response.status_code}"
            )
        data = response.json()
        if not isinstance(data, dict):
            raise ReferenceApiError("Reference API returned an invalid response")
        return {str(key): str(value) for key, value in data.items() if value is not None}

    def lookup_crew(
        self,
        name: str | None = None,
        employee_id: str | None = None,
    ) -> CrewRecord | None:
        payload: dict[str, str] = {}
        if employee_id:
            payload["employee_id"] = employee_id
        elif name:
            payload["full_name"] = name
        else:
            return None
        data = self._post("/v1/crew/lookup", payload)
        if data is None:
            return None
        allowed = {"employee_id", "full_name"}
        if set(data) - allowed:
            raise ReferenceApiError("Reference API returned disallowed crew fields")
        return CrewRecord(
            airline="Lion Air",
            name=data.get("full_name", ""),
            employee_id=data.get("employee_id"),
            atpl_number=None,
            rank_or_role=None,
            employment_status=None,
            validation_status=None,
        )

    def lookup_aircraft(self, registration: str | None) -> AircraftRecord | None:
        if not registration:
            return None
        data = self._post("/v1/aircraft/lookup", {"registration": registration})
        if data is None:
            return None
        allowed = {"registration", "aircraft_type"}
        if set(data) - allowed:
            raise ReferenceApiError("Reference API returned disallowed aircraft fields")
        return AircraftRecord(
            registration=data.get("registration", ""),
            icao_type=None,
            type_of_aircraft=data.get("aircraft_type"),
            variant=None,
            operator="Lion Air",
            validation_status=None,
        )


class RemoteCrewBank:
    def __init__(self, client: ReferenceApiClient):
        self.client = client

    def lookup(
        self,
        name: str | None = None,
        employee_id: str | None = None,
    ) -> CrewRecord | None:
        return self.client.lookup_crew(name=name, employee_id=employee_id)


class RemoteAircraftBank:
    def __init__(self, client: ReferenceApiClient):
        self.client = client

    def lookup(self, registration: str | None) -> AircraftRecord | None:
        return self.client.lookup_aircraft(registration)
