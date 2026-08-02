from __future__ import annotations

import hashlib
import json
import secrets
import sys


def main() -> int:
    label = sys.argv[1] if len(sys.argv) > 1 else "user"
    token = secrets.token_urlsafe(32)
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    print(f"User token (send privately to {label}):\n{token}\n")
    print("Server configuration entry:")
    print(json.dumps({label: digest}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
