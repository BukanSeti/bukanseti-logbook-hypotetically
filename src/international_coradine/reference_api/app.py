from __future__ import annotations

import os

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, model_validator

from .security import InMemoryRateLimiter, TokenAuthenticator, authorization_dependency
from .store import GoogleSheetReferenceStore, ReferenceStore


class CrewLookupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    employee_id: str | None = Field(default=None, min_length=1, max_length=32)
    full_name: str | None = Field(default=None, min_length=2, max_length=160)

    @model_validator(mode="after")
    def exactly_one_identifier(self):
        if bool(self.employee_id) == bool(self.full_name):
            raise ValueError("Provide exactly one of employee_id or full_name")
        return self


class CrewLookupResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    employee_id: str
    full_name: str


class AircraftLookupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    registration: str = Field(min_length=3, max_length=12)


class AircraftLookupResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    registration: str
    aircraft_type: str


def create_app(
    store: ReferenceStore | None = None,
    authenticator: TokenAuthenticator | None = None,
    limiter: InMemoryRateLimiter | None = None,
) -> FastAPI:
    docs_enabled = os.getenv("CORADINE_API_DOCS", "false").lower() == "true"
    app = FastAPI(
        title="International Coradine Private Reference API",
        version="1.0.0",
        docs_url="/docs" if docs_enabled else None,
        redoc_url=None,
        openapi_url="/openapi.json" if docs_enabled else None,
    )
    reference_store = store or GoogleSheetReferenceStore.from_environment()
    token_authenticator = authenticator or TokenAuthenticator.from_environment()
    rate_limiter = limiter or InMemoryRateLimiter(
        requests_per_minute=int(os.getenv("CORADINE_API_RATE_LIMIT_PER_MINUTE", "120"))
    )
    require_token = authorization_dependency(token_authenticator, rate_limiter)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/v1/crew/lookup", response_model=CrewLookupResponse)
    def crew_lookup(
        request: CrewLookupRequest,
        _identity: str = Depends(require_token),
    ):
        result = reference_store.lookup_crew(request.employee_id, request.full_name)
        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        return CrewLookupResponse(employee_id=result.employee_id, full_name=result.full_name)

    @app.post("/v1/aircraft/lookup", response_model=AircraftLookupResponse)
    def aircraft_lookup(
        request: AircraftLookupRequest,
        _identity: str = Depends(require_token),
    ):
        result = reference_store.lookup_aircraft(request.registration)
        if result is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        return AircraftLookupResponse(
            registration=result.registration,
            aircraft_type=result.aircraft_type,
        )

    return app


def app_factory() -> FastAPI:
    return create_app()
