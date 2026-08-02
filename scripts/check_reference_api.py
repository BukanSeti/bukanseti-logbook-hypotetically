from __future__ import annotations

import argparse
import json
import sys

import requests


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Test a deployed Coradine reference API")
    parser.add_argument("--url", required=True, help="API base URL, for example https://name.onrender.com")
    parser.add_argument("--token", required=True, help="User-specific bearer token")
    lookup = parser.add_mutually_exclusive_group(required=True)
    lookup.add_argument("--crew-id")
    lookup.add_argument("--crew-name")
    lookup.add_argument("--registration")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    base_url = args.url.rstrip("/")
    headers = {"Authorization": f"Bearer {args.token}"}

    health = requests.get(f"{base_url}/health", timeout=30)
    health.raise_for_status()

    if args.registration:
        endpoint = "/v1/aircraft/lookup"
        payload = {"registration": args.registration}
        allowed = {"registration", "aircraft_type"}
    else:
        endpoint = "/v1/crew/lookup"
        payload = {"employee_id": args.crew_id} if args.crew_id else {"full_name": args.crew_name}
        allowed = {"employee_id", "full_name"}

    response = requests.post(
        f"{base_url}{endpoint}",
        headers=headers,
        json=payload,
        timeout=60,
    )
    response.raise_for_status()
    body = response.json()
    if set(body) != allowed:
        raise RuntimeError(f"Unexpected response fields: {sorted(body)}")
    print(json.dumps(body, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except requests.RequestException as exc:
        print(f"API check failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
