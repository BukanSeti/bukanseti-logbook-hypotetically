# International Coradine Rev 3 — Implementation Requirements

This repository implements a **Lion Air pilot-only**, photo-first personal analytical
logbook reconstruction workflow.

## Mandatory scope

- Accept only Lion Air records and reject entries that clearly identify another operator.
- Require the exact full name of the logbook owner before final processing.
- Final filenames are `International_Coradine.xlsx` and `International_Coradine.pdf`.
- Always create `manual_review.json` for unresolved source fields.
- Treat outputs as personal calculation, historical comparison, review, and organization—not
  company, regulator, or licensing-authority certification.
- Never silently fabricate crew employee IDs, PIC assignments, runways, approaches, flight
  numbers, registrations, aircraft types, or source information.

## Privacy boundary

The repository must not access, request, download, embed, or distribute:

- a Crew Bank or crew directory;
- an Aircraft Bank;
- a private Google Sheet or Drive reference;
- a reference API, hosted service, service-account credential, or shared lookup token.

Crew name and employee ID are source-only fields. They may be populated only when readable in
the supplied photograph, PDF, or structured source. Missing crew data remains unverified.

Aircraft registration and type may be transcribed from the source or supplied manually by the
user with `--aircraft REGISTRATION=TYPE`. Manual aircraft values must be classified as
`MANUAL` in data provenance.

## Source priority

1. Original logbook photographs/scans.
2. Original uploaded PDF logbooks.
3. Original spreadsheets/documents.
4. Explicit user-provided aircraft registration/type overrides.
5. Route, distance, schedule, and operational logic for clearly disclosed reconstruction.

Conflicts preserve the higher-priority source and are disclosed in `DATA PROVENANCE` and
`VALIDATION REPORT`.

## Processing modes

- `coradine photo` is the simple shared-user workflow and starts processing immediately.
- `coradine process` retains the explicit `--start-processing` gate.
- `coradine inventory` creates a read-only source inventory without reconstruction.

## Provenance classifications

`SOURCE`, `MANUAL`, `DERIVED`, `LOOKED UP`, `ESTIMATED`, `UNVERIFIED`, and `UNREADABLE` are
available. The photo-only workflow normally uses `SOURCE`, `MANUAL`, `DERIVED`, `ESTIMATED`,
`UNVERIFIED`, and `UNREADABLE`; it does not perform crew or aircraft-bank lookup.

## Transcription and reconstruction

- Preserve readable source values exactly.
- Unreadable fields are not silently guessed.
- Convert IATA routes to configured ICAO codes and record mappings.
- Split a route sequence of N airports into N−1 sectors.
- Allocate combined source time across sectors while preserving the exact minute total.
- Preserve source flight numbers; missing flight numbers remain unverified.
- Preserve source registrations and normalize three-letter values to the `PK-XXX` form.
- Accept repeatable manual aircraft mappings using `--aircraft REGISTRATION=TYPE`.
- Standardize `B739` to `B737-900ER`, `B738` to `B737-800NG`, and `B38M` to `B737 MAX 8`.
- Preserve source approaches; missing runway/approach remains an em dash.
- Reconstruct OUT/IN only when an anchor time and duration support the calculation.
- For actual flights, `TOTAL TIME = IFR = ACTUAL IFR`.
- Simulator entries carry no actual flight-operation time.
- Remove `Capt`, `Captain`, or `CPT` prefixes from source PIC names.
- Use the owner as SIC only when another PIC is recorded in the source.
- Never create P1 U/S without explicit source or separate authorization.
- Use a true em dash for unavailable ordinary fields and keep Remark blank.

## Manual review

`manual_review.json` must identify:

- entries missing aircraft registration or type;
- a rerun example using `--aircraft`;
- missing crew fields that remain unresolved under the source-only privacy policy.

The review file does not block Excel/PDF generation; unresolved workbook fields remain visibly
unverified.

## Workbook sheets

1. `INTERNATIONAL CORADINE`
2. `DATA PROVENANCE`
3. `VALIDATION REPORT`
4. `AIRPORT CODE MAPPING`
5. `SOURCE INVENTORY`

The main sheet includes grouped headers, formulas, protected formula cells, freeze panes,
print area, repeated header rows, manual page breaks, borders, centered crew/approach fields,
A3 landscape page setup, and no content in Remark.

## PDF

Strict mode exports the completed workbook through LibreOffice/Calc. A ReportLab renderer is
available only as an explicitly enabled fallback and is not claimed to be pixel-identical.
Human visual review remains required before claiming final pixel accuracy.
