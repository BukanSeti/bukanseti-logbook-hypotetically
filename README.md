# INTERNATIONAL CORADINE Rev 3 — Lion Air Pilot Logbook

A **Lion Air-only** pipeline for turning pilot-logbook photographs, scans, PDFs, CSV/JSON, or spreadsheets into:

- `International_Coradine.xlsx`
- `International_Coradine.pdf`

The project is deliberately conservative: readable source data is preserved, reconstruction is disclosed field-by-field, employee IDs are never fabricated, missing approaches are not invented, and records from other airlines are rejected.

> This is a personal analytical reconstruction tool. It is not a company-confirmed, regulator-verified, licensing-authority-certified, or officially certified pilot logbook.

## Core safeguards

- Exact logbook-owner name is mandatory.
- Explicit `--start-processing` gate mirrors the required **START PROCESSING** instruction.
- Lion Air-only guard rejects identified records from other airlines.
- Multi-airport routes become N−1 sector rows.
- Combined time allocation preserves the exact source minute total.
- Final route columns use ICAO codes.
- `TOTAL TIME = IFR = ACTUAL IFR` for actual flights.
- `P1 U/S ≤ Copilot Time ≤ Total Time` is validated.
- Simulator rows cannot carry flight-operation time.
- Every non-source decision is recorded in `DATA PROVENANCE`.
- Remark remains blank.
- Strict PDF mode exports from the completed workbook through LibreOffice.

## Private Lion Air references

The default configuration points to the supplied Google Sheets:

- **Lion Air Crew** — crew name, employee ID, ATPL, role, status, source, and validation status.
- **Lion Air Airplane** — registration, ICAO type, aircraft type/variant, operator, historical usage, source, and validation status.

Downloaded reference caches are local and ignored by Git. The repo does **not** publish crew or aircraft rows.

## Install

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

For strict PDF-from-Excel rendering, install LibreOffice or use Docker.

```bash
docker build -t international-coradine .
```

## 1. Refresh reference banks

The Google Sheets must be viewable by the runtime account. Otherwise, place exported `.xlsx` files at the configured cache paths.

```bash
coradine refresh-references
```

Or configure private local files:

```bash
export LION_AIR_CREW_XLSX=/private/Lion_Air_Crew.xlsx
export LION_AIR_AIRCRAFT_XLSX=/private/Lion_Air_Airplane.xlsx
```

## 2. Inventory uploads without processing

```bash
coradine inventory scans/page-001.jpg scans/page-002.jpg --output-dir work
```

This creates `work/source_inventory.json` only.

## 3. Start processing

```bash
export OPENAI_API_KEY="..."       # needed for photographs/PDFs
export OPENAI_MODEL="gpt-5"       # optional override

coradine process \
  scans/page-001.jpg scans/page-002.pdf \
  --owner "FULL NAME OF LION AIR PILOT" \
  --start-processing \
  --output-dir output
```

Structured CSV/JSON/XLSX inputs do not require the OpenAI API. Photo/PDF extraction uses the OpenAI Responses API with image/file input and structured JSON output.

Use the non-identical fallback renderer only when LibreOffice is unavailable:

```bash
coradine process source.csv \
  --owner "FULL NAME" \
  --start-processing \
  --allow-pdf-fallback
```

## Accepted normalized columns

The structured-file extractor recognizes common aliases for:

`Date`, `Airline`, `Flight Number`, `Route`, `OUT`, `IN`, `Total Time`, `Registration`, `Aircraft Type`, `PIC Name`, `PIC ID`, `P1 U/S`, `Simulator Time`, and `Approach`.

A route such as `CGK SOC CGK SUB` becomes:

1. `WIII – WAHQ`
2. `WAHQ – WIII`
3. `WIII – WARR`

## Output workbook

- `INTERNATIONAL CORADINE`
- `DATA PROVENANCE`
- `VALIDATION REPORT`
- `AIRPORT CODE MAPPING`
- `SOURCE INVENTORY`

The workbook uses formulas, protected formula cells, repeated print headers, manual page breaks, print area, A3 landscape, bordered cells, and explicit totals.

## Pixel-accurate layout

The included renderer establishes the Rev 3 semantic structure and print controls. True pixel matching requires authorized reference photographs/scans in a private working directory and a template-calibration pass. Do not claim pixel accuracy until every exported PDF page has also been manually reviewed for clipping, overlap, border displacement, row alignment, and accidental blank pages.

## Tests

```bash
pytest -q
ruff check src tests
```

## License

MIT. Source logbooks, crew directories, aircraft banks, and reference photographs remain subject to their owners' privacy and distribution rights.
