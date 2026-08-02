# INTERNATIONAL CORADINE Rev 3 — Photo-Only Lion Air Logbook

A **Lion Air-only** pipeline that converts pilot-logbook photographs, scans, PDFs,
CSV/JSON, or spreadsheets into:

- `International_Coradine.xlsx`
- `International_Coradine.pdf`
- `manual_review.json`

The shared repository is deliberately self-contained. It does **not** access or request:

- a Crew Bank;
- an Aircraft Bank;
- a Google Sheet or Google Drive folder;
- a private reference API;
- a service account, server token, or hosting service.

> This is a personal analytical reconstruction tool. It is not a company-confirmed,
> regulator-verified, licensing-authority-certified, or officially certified pilot logbook.

## Privacy and reference policy

Crew names and employee IDs are transcribed only when they are readable in the supplied
photo. Missing or unreadable crew fields remain `UNVERIFIED` or `UNREADABLE`; the software
never searches a crew directory and never fabricates an employee ID.

Aircraft registration and type may come from:

1. readable text in the photo; or
2. an explicit manual value supplied by the user with `--aircraft REGISTRATION=TYPE`.

The repository performs no background aircraft lookup. This keeps the shared workflow free
from private data and external reference access.

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

The `photo` command starts processing immediately. It performs OCR, reconstruction,
validation, and Excel/PDF generation without a separate `START PROCESSING` flag.

When aircraft type must be supplied manually:

```bash
coradine photo \
  scans/page-001.jpg scans/page-002.jpg \
  --owner "FULL NAME OF LOGBOOK OWNER" \
  --aircraft PK-LJF=B739 \
  --aircraft PK-LJU=B738 \
  --output-dir output
```

The flag is repeatable. Both `PK-LJF=B739` and `LJF=B739` are accepted. Common types are
standardized as follows:

- `B738` → `B737-800NG`
- `B739` → `B737-900ER`
- `B38M` → `B737 MAX 8`

## Manual review file

Every run creates `manual_review.json`.

It contains:

- aircraft entries that still need registration or type;
- an exact example of the `--aircraft` argument needed for a rerun;
- crew fields that remain unverified because they were not readable in the source photo;
- a clear statement that no Crew Bank or private directory was accessed.

Missing information is never silently guessed. The Excel/PDF can still be generated with an
em dash while the unresolved field remains visible in the validation and provenance sheets.

## Advanced processing gate

The original gated workflow remains available:

```bash
coradine process \
  scans/page-001.jpg \
  --owner "FULL NAME OF LOGBOOK OWNER" \
  --start-processing \
  --output-dir output
```

Use `coradine inventory` when only a read-only inventory is needed:

```bash
coradine inventory scans/page-001.jpg scans/page-002.jpg --output-dir work
```

## Core safeguards

- Exact logbook-owner name is mandatory.
- Lion Air-only guard rejects identified records from other airlines.
- Multi-airport routes become N−1 sector rows.
- Combined time allocation preserves the exact source-minute total.
- Final route columns use ICAO codes.
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

A friend needs:

1. this repository;
2. their own logbook photo/PDF;
3. the exact logbook-owner name;
4. their own OpenAI API key when running photo OCR locally;
5. optional manual registration/type values for aircraft that are not readable.

They do not need access to any private bank, Google Sheet, Drive folder, token, or server.

## Pixel-accurate layout

The renderer establishes the Rev 3 semantic structure and print controls. A true
pixel-matching claim still requires authorized reference photographs and manual inspection
of every exported PDF page for clipping, overlap, border displacement, row alignment, and
accidental blank pages.

## License

MIT. Source logbooks and reference photographs remain subject to their owners' privacy and
distribution rights.
