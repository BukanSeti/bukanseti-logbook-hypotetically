from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from threading import Lock

from fastapi import Header, HTTPException, status


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@dataclass
class TokenAuthenticator:
    token_hashes: dict[str, str]

    @classmethod
    def from_environment(cls) -> "TokenAuthenticator":
        raw = os.getenv("CORADINE_API_TOKEN_HASHES", "{}")
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError("CORADINE_API_TOKEN_HASHES must be valid JSON") from exc
        if not isinstance(parsed, dict) or not parsed:
            raise RuntimeError("At least one API token hash must be configured")
        token_hashes = {str(label): str(value).lower() for label, value in parsed.items()}
        for digest in token_hashes.values():
            if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
                raise RuntimeError("Each API token must be stored as a SHA-256 hex digest")
        return cls(token_hashes)

    def authenticate(self, authorization: str | None) -> str:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
        supplied = hash_token(authorization[7:].strip())
        for label, expected in self.token_hashes.items():
            if hmac.compare_digest(supplied, expected):
                return label
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")


@dataclass
class InMemoryRateLimiter:
    requests_per_minute: int = 120
    _events: dict[str, deque[float]] = field(default_factory=lambda: defaultdict(deque))
    _lock: Lock = field(default_factory=Lock)

    def check(self, identity: str) -> None:
        now = time.monotonic()
        cutoff = now - 60.0
        with self._lock:
            events = self._events[identity]
            while events and events[0] < cutoff:
                events.popleft()
            if len(events) >= self.requests_per_minute:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded",
                )
            events.append(now)


def authorization_dependency(
    authenticator: TokenAuthenticator,
    limiter: InMemoryRateLimiter,
):
    def dependency(authorization: str | None = Header(default=None)) -> str:
        identity = authenticator.authenticate(authorization)
        limiter.check(identity)
        return identity

    return dependency
