# Deploy the Private Reference API on Render

The repository includes `render.yaml`, which defines one Docker web service in the Singapore
region. The Blueprint contains secret *names* only. It never contains the Google credential,
user tokens, or reference-bank rows.

## Required private values

Prepare these values before activating the Blueprint:

| Render environment variable | Value |
|---|---|
| `LION_AIR_CREW_SHEET_ID` | `1gpPtVN9LYdg9EptvudA87CH67c6SP7IDE7bQUmYi7yc` |
| `LION_AIR_AIRCRAFT_SHEET_ID` | `1TzgCM3_SwgyrcDdfN_K4Asm0oxBj7oATRyEaXcBTH60` |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Complete JSON credential for the server-side Google service account |
| `CORADINE_API_TOKEN_HASHES` | JSON map of user label to SHA-256 token hash |

Do not commit the service-account JSON or plaintext user tokens to GitHub.

## Google preparation

1. Create a Google Cloud service account intended only for this API.
2. Download its JSON credential once and store it securely.
3. Share only the `Lion Air Crew` and `Lion Air Airplane` Google Sheets with the service-account
   email as **Viewer**.
4. Do not grant the service account access to unrelated Drive files or folders.

## Create the first user token

Run locally from the repository:

```bash
python scripts/generate_reference_token.py adi
```

The script prints:

- one plaintext token to place in the user's private client configuration; and
- one JSON hash entry to place in `CORADINE_API_TOKEN_HASHES` on Render.

For multiple users, combine the generated hash entries into one JSON object, for example:

```json
{"adi":"HASH_1","friend-a":"HASH_2"}
```

## Activate the Render Blueprint

1. Sign in to Render and connect the GitHub account that owns this repository.
2. Create a new Blueprint and select `BukanSeti/bukanseti-logbook-hypotetically`.
3. Render detects the root-level `render.yaml` file.
4. Enter the four required private values when prompted.
5. Create the Blueprint and wait for the service health check to pass.
6. Copy the generated HTTPS URL, such as `https://coradine-private-reference-api.onrender.com`.

The default Blueprint uses Render's free web-service plan. This is suitable for initial
personal testing but can sleep when inactive. Change `plan: free` to `plan: starter` in
`render.yaml` when always-on response is required.

## Verify the deployment

Test an aircraft lookup:

```bash
python scripts/check_reference_api.py \
  --url "https://YOUR-SERVICE.onrender.com" \
  --token "PLAINTEXT-USER-TOKEN" \
  --registration "PK-LJF"
```

Expected response fields are exactly:

```json
{
  "registration": "PK-LJF",
  "aircraft_type": "B737-900ER"
}
```

Test a crew lookup:

```bash
python scripts/check_reference_api.py \
  --url "https://YOUR-SERVICE.onrender.com" \
  --token "PLAINTEXT-USER-TOKEN" \
  --crew-id "23133"
```

Expected response fields are exactly `employee_id` and `full_name`.

## Configure each logbook client

Each user receives only the service URL and their individual plaintext token:

```bash
export CORADINE_REFERENCE_API_URL="https://YOUR-SERVICE.onrender.com"
export CORADINE_REFERENCE_API_TOKEN="PLAINTEXT-USER-TOKEN"
```

The user does not receive the Google service-account credential, Google Sheet links, Crew
Bank workbook, or Aircraft Bank workbook.

## Revoke one user's access

Remove that user's hash entry from `CORADINE_API_TOKEN_HASHES` in Render and redeploy the
service. Other users' tokens remain valid.
