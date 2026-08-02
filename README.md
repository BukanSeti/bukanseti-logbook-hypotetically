# INTERNATIONAL CORADINE Rev 3 — Lion Air Pilot Logbook

A **Lion Air-only** pipeline for turning pilot-logbook photographs, scans, PDFs,
CSV/JSON, or spreadsheets into:

- `International_Coradine.xlsx`
- `International_Coradine.pdf`

The project preserves readable source data, discloses reconstruction field-by-field,
never fabricates employee IDs, and rejects identified records from other airlines.

> This is a personal analytical reconstruction tool. It is not a company-confirmed,
> regulator-verified, licensing-authority-certified, or officially certified pilot logbook.

## Private reference design

Shared repo users do **not** receive the Lion Air Crew or Airplane workbooks. The normal
configuration calls a private, token-authenticated API controlled by the system owner.

The repo can receive only:

- Crew: `employee_id` and `full_name`
- Aircraft: `registration` and `aircraft_type`

The API has no bulk-list or bank-download endpoint. ATPL, rank, employment status,
operator details, validation status, and other fields are not returned.

Server design is documented in [`docs/PRIVATE_REFERENCE_API.md`](docs/PRIVATE_REFERENCE_API.md).

## Deploy the private API

The root-level [`render.yaml`](render.yaml) defines a Docker web service for Render with a
Singapore region, health check, CI-gated auto-deployment, and secret placeholders. No Google
credential, user token, Crew Bank row, or Aircraft Bank row is committed to the repository.

Follow [`docs/RENDER_DEPLOYMENT.md`](docs/RENDER_DEPLOYMENT.md) to connect the repository,
enter the server-only secrets, issue one token per user, and verify the deployed API.

## Install the logbook client

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

For strict PDF-from-Excel rendering, install LibreOffice or use Docker.

## Configure a user's private API access

```bash
export CORADINE_REFERENCE_API_URL="https://reference.example.com"
export CORADINE_REFERENCE_API_TOKEN="token-issued-to-this-user"
```

The token is user-specific. It is not a Google credential and cannot directly open the
Google Sheets.

## Inventory uploads without processing

```bash
coradine inventory scans/page-001.jpg scans/page-002.jpg --output-dir work
```

## Process the logbook

```bash
export OPENAI_API_KEY="..."       # needed for photographs/PDFs
export OPENAI_MODEL="gpt-5"       # optional override

coradine process \
  scans/page-001.jpg scans/page-002.pdf \
  --owner "FULL NAME OF LION AIR PILOT" \
  --start-processing \
  --output-dir output
```

Structured CSV/JSON/XLSX inputs do not require the OpenAI API. Photo/PDF extraction uses
image/file input and structured JSON output.

## Core safeguards

- Exact logbook-owner name is mandatory.
- Explicit `--start-processing` gate is required.
- Lion Air-only guard rejects identified records from other airlines.
- Multi-airport routes become N−1 sector rows.
- Combined time allocation preserves the exact source-minute total.
- Final route columns use ICAO codes.
- `TOTAL TIME = IFR = ACTUAL IFR` for actual flights.
- `P1 U/S ≤ Copilot Time ≤ Total Time` is validated.
- Simulator rows cannot carry flight-operation time.
- Every non-source decision is recorded in `DATA PROVENANCE`.
- Remark remains blank.
- Strict PDF mode exports from the completed workbook through LibreOffice.

## Output workbook

- `INTERNATIONAL CORADINE`
- `DATA PROVENANCE`
- `VALIDATION REPORT`
- `AIRPORT CODE MAPPING`
- `SOURCE INVENTORY`

## Administrator-only local fallback

Direct reference downloads are disabled. A system administrator may use already exported,
private local workbooks only by changing `allow_local_admin_fallback` in a private config
and setting `CORADINE_ALLOW_LOCAL_REFERENCE_ADMIN=true`. Do not enable this in copies shared
with other users.

## Tests

```bash
pip install -e ".[dev,reference-api]"
ruff check src tests scripts
pytest -q
```

## Pixel-accurate layout

The renderer establishes the Rev 3 semantic structure and print controls. A true
pixel-matching claim still requires authorized reference photographs and manual inspection
of every exported PDF page for clipping, overlap, border displacement, row alignment, and
accidental blank pages.

## License

MIT. Source logbooks, crew directories, aircraft banks, and reference photographs remain
subject to their owners' privacy and distribution rights.
