---
title: ETL Pipeline: Data Fetching and Ingestion Constraints
project_id: coc-elt
nyutu_uuid: 850f0c0d-7db6-41a6-9c8c-3aac25eeca62
artifact_type: Business Logic Constraint
tags:
  - python
  - clash-of-clans-api
  - error-handling
  - security
source_uri: proyectos/coc_analysis/etl_coc/src/etl_coc/scripts/fetch_coc_raw_data.py
---
# Data Fetching and Ingestion Details

The ETL pipeline pulls live game data daily from the Clash of Clans API using a JWT API key (`COC_APIKEY`) and localizes it before database ingestion:

## Fetching Specifics
- **Base URL:** `https://api.clashofclans.com/v1/`
- **Clan ID:** `#2CYG9CJQ` (requires URL encoding to `%232CYG9CJQ`).
- **Endpoint Schedules & Filtering:**
  - **Clan Info & Member List:** Fetched daily. Member details are retrieved individually by iterating through the clan's member list player tags.
  - **Current War (`/currentwar`):** Fetched daily. Data is only stored if the war state is active (i.e. not `notInWar`).
  - **Capital Raids (`/capitalraidseasons`):** Only fetched from Friday to Monday (days `4`, `5`, `6`, `0` of the week) during live raid periods.
  - **League Group (`/currentwar/leaguegroup` & `/wars/{wartag}`):** Fetched only when rounds are active, checking and persisting war logs for each active round.

## Ephemeral File Operations & Permissions
- The ETL container runs under an unprivileged `appuser` for security.
- Files cannot be written to static directories due to Unix permission restrictions. All raw JSON responses are saved to `/tmp/etl_coc_data/raw/`.
- Once the data is successfully parsed and loaded, the temporary folder is deleted (`cleanup_temporary_files`) to keep host storage clean.

## Timezone Processing
- The ETL process operates in UTC, but the dashboard or local environments may reside in other timezones.
- To prevent query mismatch issues, all dates (e.g. `extracted_at`) must be explicitly localized to UTC in Pandas/Pydantic before database ingestion:
  ```python
  if extracted_at.tzinfo is None:
      extracted_at = extracted_at.tz_localize('UTC')
  ```
