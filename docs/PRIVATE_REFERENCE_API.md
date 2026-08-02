# Private Lion Air Reference API

This service keeps the Lion Air Crew and Airplane banks on a server controlled by the
system owner. Shared copies of the logbook repository never receive either workbook.

## Strict response contract

The server exposes only two authenticated lookup operations:

- `POST /v1/crew/lookup` returns exactly `employee_id` and `full_name`.
- `POST /v1/aircraft/lookup` returns exactly `registration` and `aircraft_type`.

There is no crew-list, aircraft-list, export, download, search-all, ATPL, rank, employment
status, operator-detail, or validation-status endpoint. Request models reject extra fields.
The client also rejects responses containing fields outside the approved contract.

## Server preparation

1. Create a Google Cloud service account with read-only Drive access.
2. Share only the two private Google Sheets with the service-account email as Viewer.
3. Copy `.env.reference-api.example` to a private server environment.
4. Set the two spreadsheet file IDs and the service-account credential.
5. Generate a separate user token:

```bash
python scripts/generate_reference_token.py friend-name
```

Send the plaintext token privately to that user. Store only its SHA-256 hash in
`CORADINE_API_TOKEN_HASHES` on the server.

## Run with Docker

```bash
docker build -f Dockerfile.reference-api -t coradine-reference-api .
docker run --rm -p 8080:8080 --env-file .env.reference-api \
  -v /private/google-service-account.json:/run/secrets/google-service-account.json:ro \
  coradine-reference-api
```

Use HTTPS through the hosting platform or a reverse proxy. Do not expose this service over
plain HTTP on the public internet.

## Client configuration

Each user receives only the API URL and their own token:

```bash
export CORADINE_REFERENCE_API_URL="https://reference.example.com"
export CORADINE_REFERENCE_API_TOKEN="user-specific-secret"
```

The normal `coradine process` command then performs narrow lookups automatically.

## Security properties and limits

- Google credentials remain only on the server.
- POST bodies keep names and IDs out of normal URL access logs.
- Tokens are compared using SHA-256 digests and constant-time comparison.
- Each token has an in-memory per-minute rate limit.
- Spreadsheet data is cached server-side to reduce Google API traffic.
- API documentation is disabled by default.
- A determined authorized user could still enumerate values through repeated exact lookups.
  Keep rate limits conservative, issue one token per user, review access logs, and revoke a
  single token immediately if misuse is suspected.
