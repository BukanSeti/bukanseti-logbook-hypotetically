# International Coradine Rev 3 — Implementation Requirements

This repository implements a **Lion Air pilot-only** personal analytical logbook reconstruction workflow.

## Mandatory scope

- Accept only Lion Air records. Reject entries that identify Batik Air, Wings Air, Super Air Jet, Garuda Indonesia, Citilink, AirAsia, Sriwijaya, NAM Air, or another operator.
- Require the exact full name of the logbook owner before final processing.
- Final filenames are `International_Coradine.xlsx` and `International_Coradine.pdf`.
- Treat outputs as personal calculation, historical comparison, review, organization, scenario analysis, and incomplete historical viewing—not company, regulator, or licensing-authority certification.
- Never silently fabricate source information, crew employee IDs, PIC assignments, runways, approaches, flight numbers, or aircraft types.

## Source priority

1. Original logbook photographs/scans.
2. Original uploaded PDF logbooks.
3. Original spreadsheets/documents.
4. `Logbook Present True` supplied by the user.
5. `PIC Lion Air` supplied by the user.
6. Other supplied reference books.
7. Reliable registration databases or aviation sites.
8. Route/distance/schedule/operational logic.
9. Explicitly classified reconstruction.

Conflicts preserve the highest-priority source and are disclosed in `DATA PROVENANCE` and `VALIDATION REPORT`.

## Processing gate

Uploads may arrive over multiple messages. The repository mirrors the required `START PROCESSING` gate with the CLI flag `--start-processing`. Without it, the tool creates only a read-only source inventory.

## Provenance classifications

`SOURCE`, `DERIVED`, `LOOKED UP`, `ESTIMATED`, `UNVERIFIED`, and `UNREADABLE` are recorded per field. Non-source values include the reason, reference, access date where relevant, confidence, and unresolved issue.

## Transcription and reconstruction

- Preserve readable source values exactly.
- Unreadable fields are not silently guessed.
- Convert IATA routes to current configured ICAO codes and record mappings.
- Split a route sequence of N airports into N−1 sectors.
- Allocate a combined source time across sectors using distance plus short-sector overhead, while preserving the exact combined minute total.
- Preserve source flight numbers. Missing flight numbers remain unverified unless a defensible external/source lookup is implemented.
- Preserve registrations. Look up missing type only in the Lion Air aircraft reference bank or a documented reliable source.
- Standardize `B7379`/`B739` to `B737-900ER` and `B7378`/`B738` to `B737-800NG`.
- Preserve source approaches. A missing exact runway/approach remains an em dash rather than an invented procedure.
- Reconstruct OUT/IN only when an anchor time and duration support the calculation. Split sectors use chronological turnaround sequencing.
- For actual flights, `TOTAL TIME = IFR = ACTUAL IFR`.
- Simulator entries carry no route flight time, takeoff, landing, approach, Actual IFR, Copilot Time, or P1 U/S.
- Remove `Capt`, `Captain`, or `CPT` from PIC names.
- Use the owner as SIC only when another PIC is recorded. Copilot Time then equals Total Time.
- Never create P1 U/S without explicit source or separate authorization. Enforce `P1 U/S ≤ Copilot Time ≤ Total Time`.
- Use a true em dash for unavailable ordinary fields. Keep the Remark column completely blank.

## Workbook sheets

1. `INTERNATIONAL CORADINE`
2. `DATA PROVENANCE`
3. `VALIDATION REPORT`
4. `AIRPORT CODE MAPPING`
5. `SOURCE INVENTORY`

The main sheet includes grouped headers, formulas, protected formula cells, freeze panes, print area, repeated header rows, manual page breaks, borders, centered crew/approach fields, A3 landscape page setup, and no content in Remark.

## PDF

Strict mode exports the completed workbook through LibreOffice/Calc so Excel and PDF share values and page setup. A ReportLab renderer exists only as an explicitly enabled fallback and is not claimed to be pixel-identical. The PDF inspector rejects blank pages and text blocks outside page bounds. Human visual review remains required for a final claim of pixel accuracy.

## Reference privacy

The configured Google Sheets are used as private runtime references:

- Lion Air Crew: `1gpPtVN9LYdg9EptvudA87CH67c6SP7IDE7bQUmYi7yc`
- Lion Air Airplane: `1TzgCM3_SwgyrcDdfN_K4Asm0oxBj7oATRyEaXcBTH60`

The repository does not publish the downloaded crew or aircraft rows. Cached `.xlsx` files are excluded by `.gitignore`.
