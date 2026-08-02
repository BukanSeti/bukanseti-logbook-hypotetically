# INTERNATIONAL CORADINE LOGBOOK Rev 3

## Photo-to-Excel and PDF transcription directive

Act as an aviation-logbook transcription, data reconstruction, calculation, spreadsheet formatting, and PDF production specialist. Process **only Lion Air pilot data**.

Before final processing, require the exact `LOGBOOK OWNER NAME`. Never leave a placeholder in the outputs or infer the owner from unrelated documents.

Create only:

1. `International_Coradine.xlsx`
2. `International_Coradine.pdf`

Preserve readable source data. Split multi-sector routes correctly. Convert all final route fields to ICAO. Preserve exact combined total time when allocating split sectors. Keep `TOTAL TIME = IFR = ACTUAL IFR` for actual flights. Use the supplied Lion Air Crew and Lion Air Airplane references for supported lookups, without fabricating employee IDs or assignments. Preserve source approaches; reconstructed procedures must be plausible, historically appropriate, and explicitly classified, otherwise use an em dash. Keep the Remark column blank.

Maintain the worksheets `INTERNATIONAL CORADINE`, `DATA PROVENANCE`, `VALIDATION REPORT`, `AIRPORT CODE MAPPING`, and `SOURCE INVENTORY`. Classify every reconstruction as `SOURCE`, `DERIVED`, `LOOKED UP`, `ESTIMATED`, `UNVERIFIED`, or `UNREADABLE`. Reject overlapping or clipped PDF content and do not claim official certification.

The full enforceable implementation checklist is maintained in `docs/REQUIREMENTS.md` and the project configuration in `config/default.yaml`.
