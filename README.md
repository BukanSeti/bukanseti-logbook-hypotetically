# INTERNATIONAL CORADINE Rev 3 — Photo-Only Lion Air Logbook

A **Lion Air-only** pipeline that converts pilot-logbook photographs, scans, PDFs,
CSV/JSON, or spreadsheets into:

- `International_Coradine.xlsx`
- `International_Coradine.pdf`
- `manual_review.json`

The shared repository is self-contained. It does **not** access or request a Crew Bank,
Aircraft Bank, Google Sheet, Google Drive folder, private API, service account, server token,
or hosting service.

> This is a personal analytical reconstruction tool. It is not a company-confirmed,
> regulator-verified, licensing-authority-certified, or officially certified pilot logbook.

## Mandatory ICAO output standard

All final aircraft and airport fields use ICAO designators only.

### Aircraft Type

Common source or manual values are normalized to ICAO aircraft type designators:

- `B737-800`, `B737-800NG`, or `B738` → `B738`
- `B737-900ER` or `B739` → `B739`
- `B737 MAX 8`, `737-8`, or `B38M` → `B38M`

Other valid ICAO aircraft type designators, such as `A320`, remain unchanged. Expanded model
names are never written to the final Aircraft Type column.

### Airports

All final departure and arrival fields use four-letter ICAO airport codes. Known IATA codes
from the source are converted automatically, for example:

- `SUB` → `WARR`
- `CGK` → `WIII`
- `SOC` → `WAHQ`

A route written as `SUB–CGK` in the source is therefore stored as `WARR–WIII`. Unknown or
unverified airport codes remain an em dash rather than being guessed.

The validation report marks any final non-ICAO aircraft type or airport code as an error.

## Privacy and reference policy

Crew names and employee IDs are transcribed only when readable in the supplied source.
Missing or unreadable crew fields remain `UNVERIFIED` or `UNREADABLE`; the software never
searches a crew directory and never fabricates an employee ID.

Aircraft registration and type may come from readable text in the source or an explicit
manual value supplied with `--aircraft REGISTRATION=ICAO_TYPE`. No background aircraft lookup
is performed.

## Install

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Photo/PDF OCR in the standalone repository requires an OpenAI API key:

```bash
export OPENAI_API_KEY="..."
export OPENAI_MODEL="gpt-5"      # optional override
```

A ChatGPT subscription and OpenAI API billing are separate. Structured CSV/JSON/XLSX input
does not require the OpenAI API.

For strict PDF-from-Excel rendering, install LibreOffice. The optional ReportLab fallback can
be enabled when LibreOffice is unavailable.

## Simple workflow for friends

Place the logbook photos in a folder, then run:

```bash
coradine photo \
  scans/page-001.jpg scans/page-002.jpg \
  --owner "FULL NAME OF LOGBOOK OWNER" \
  --output-dir output
```

The `photo` command starts processing immediately and performs OCR, reconstruction,
validation, and Excel/PDF generation.

When aircraft type must be supplied manually, use an ICAO designator:

```bash
coradine photo \
  scans/page-001.jpg scans/page-002.jpg \
  --owner "FULL NAME OF LOGBOOK OWNER" \
  --aircraft PK-LJF=B739 \
  --aircraft PK-LJU=B738 \
  --output-dir output
```

The flag is repeatable. Both `PK-LJF=B739` and `LJF=B739` are accepted. A recognized expanded
model such as `PK-LJF=B737-900ER` is accepted as input but normalized to `B739` in the output.

## Manual review file

Every run creates `manual_review.json`. It contains:

- aircraft entries that still need registration or ICAO type;
- an exact `--aircraft` example for a rerun;
- crew fields that remain unverified because they were not readable;
- confirmation that no Crew Bank or private directory was accessed.

Missing information is never silently guessed. Excel/PDF generation can continue with an em
dash while unresolved fields remain visible in validation and provenance sheets.

## Advanced processing gate

```bash
coradine process \
  scans/page-001.jpg \
  --owner "FULL NAME OF LOGBOOK OWNER" \
  --start-processing \
  --output-dir output
```

Use `coradine inventory` for a read-only source inventory:

```bash
coradine inventory scans/page-001.jpg scans/page-002.jpg --output-dir work
```

## Core safeguards

- Exact logbook-owner name is mandatory.
- Lion Air-only guard rejects identified records from other airlines.
- Final Aircraft Type uses an ICAO aircraft type designator.
- Final Departure and Arrival use four-letter ICAO airport codes.
- Multi-airport routes become N−1 sector rows.
- Combined time allocation preserves the exact source-minute total.
- `TOTAL TIME = IFR = ACTUAL IFR` for actual flights.
- `P1 U/S ≤ Copilot Time ≤ Total Time` is validated.
- Missing runways, approaches, flight numbers, crew IDs, or aircraft types are not invented.
- Every non-source decision is recorded in `DATA PROVENANCE`.
- Remark remains blank.
- Strict PDF mode exports from the completed workbook through LibreOffice.

## Output workbook

- `INTERNATIONAL CORADINE`
- `DATA PROVENANCE`
- `VALIDATION REPORT`
- `AIRPORT CODE MAPPING`
- `SOURCE INVENTORY`

## Tests

```bash
pip install -e ".[dev]"
ruff check src tests
pytest -q
```

## Sharing the repository

A friend needs this repository, their logbook photo/PDF, the exact owner name, their own
OpenAI API key for local photo OCR, and optional manual registration/ICAO type values.
They do not need access to a private bank, Google Sheet, Drive folder, token, or server.

## Pixel-accurate layout

The renderer establishes the Rev 3 semantic structure and print controls. A true
pixel-matching claim still requires authorized reference photographs and manual inspection
of every exported PDF page.

## License

MIT. Source logbooks and reference photographs remain subject to their owners' privacy and
distribution rights.
