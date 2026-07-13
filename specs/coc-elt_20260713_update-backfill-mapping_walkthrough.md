---
title: "Update player mapping and truncate table in backfill Walkthrough"
project_id: "coc-elt"
nyutu_uuid: "f63a2125-6796-4686-b0ea-b51b419b2458"
artifact_type: "Technical Discovery"
tags:
  - "backfill"
  - "mongodb"
  - "bigquery"
  - "walkthrough"
source_uri: "specs/coc-elt_20260713_update-backfill-mapping_walkthrough.md"
---

# Walkthrough: Update Player Mapping and Truncate Table in Backfill

This document walks through the implementation, verification, and execution details for updating the historical MongoDB backfill script to map the full player profile payload and restrict target table loading.

## 1. Implementation Details

### 1.1 Support for `--table` CLI Argument
- Added `--table` argument to `argparse.ArgumentParser` in `main()` defaulting to `"all"`.
- Adapted `process_and_backfill` to accept a `table` string filter.
- Conditionally query and ingest MongoDB collections only if the targeted table requires them:
  - `coc_members` and `coc_clan` process the `clan` MongoDB collection. If `table` is set to `coc_members`, `coc_clan` payload creation and BQ loading are skipped.
  - `coc_current_war` processes the `warlog` MongoDB collection. Skip processing/loading if `table` restricts execution to `coc_members`.
  - `coc_capital_raids` processes the `capital_raids` MongoDB collection. Skip processing/loading if `table` restricts execution to `coc_members`.

### 1.2 Custom Write Disposition and Table Truncating
- Modified `load_table_data` to accept `write_disposition` as a parameter, defaulting to `WRITE_APPEND`.
- Passed the `write_disposition` to `bigquery.LoadJobConfig`.
- In `process_and_backfill`, called `load_table_data` with `write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE` when loading `coc_members`, while other tables default to `WRITE_APPEND`.

### 1.3 Full Player Profile Mapping (No Whitelist)
- Removed the player payload key whitelist (`keys_to_keep`).
- Directly mapped the entire `player` profile dictionary from the MongoDB BSON document, recursively cleaned via `clean_mongo_doc`.

## 2. Test Verification

Updated `tests/test_backfill_from_mongo.py` to:
- Test default and custom `write_disposition` logic inside `test_load_table_data`.
- Verify that `extra_field` (which was previously filtered out) is preserved in the player profile payload within `test_process_and_backfill_mapping`, and that `WRITE_TRUNCATE` is configured for `coc_members`.
- Add `test_process_and_backfill_table_filtering` to verify that when `--table coc_members` is passed, other tables are completely skipped and not loaded, and database queries for unrelated collections (`warlog` and `capital_raids`) are not executed.

Executed test suite:
```bash
PYTHONPATH=. uv run pytest tests/test_backfill_from_mongo.py
```
Output:
```
============================== 12 passed in 0.21s ==============================
```

## 3. Targeted Execution

Executed the backfill script for `coc_members` only:
```bash
PYTHONPATH=. uv run python scripts/backfill_from_mongo.py --table coc_members
```

### 3.1 Execution Logs
The task completed successfully with the following log output:
```
{"severity": "INFO", "message": "Extracting archive 'coc_db' to '/tmp/coc_mongo_backfill_kmb4640_'...", "timestamp": "2026-07-13T21:16:04.611333+00:00", ...}
{"severity": "INFO", "message": "Setting permissions 777 on directory '/tmp/coc_mongo_backfill_kmb4640_'...", "timestamp": "2026-07-13T21:16:06.361800+00:00", ...}
{"severity": "INFO", "message": "Starting container 'coc_mongo_backfill_b7a73a4b74204603a0db674f15014aee' using image 'mongo:latest'...", "timestamp": "2026-07-13T21:16:06.362217+00:00", ...}
{"severity": "INFO", "message": "Container port 27017 mapped to host port 32769", "timestamp": "2026-07-13T21:16:06.486786+00:00", ...}
{"severity": "INFO", "message": "MongoDB is ready to accept connections.", "timestamp": "2026-07-13T21:16:06.991110+00:00", ...}
{"severity": "INFO", "message": "Found Clash of Clans database: 'coc_db'", "timestamp": "2026-07-13T21:16:07.579583+00:00", ...}
{"severity": "INFO", "message": "Processing collection 'clan'...", "timestamp": "2026-07-13T21:16:07.579884+00:00", ...}
{"severity": "INFO", "message": "Preparing to load 10165 rows into BigQuery table 'swift-capsule-492817-a7.coc_bronze.coc_members'", "timestamp": "2026-07-13T21:16:10.182035+00:00", ...}
{"severity": "INFO", "message": "Successfully loaded 10165 rows into 'swift-capsule-492817-a7.coc_bronze.coc_members'", "timestamp": "2026-07-13T21:17:41.740740+00:00", ...}
{"severity": "INFO", "message": "MongoDB backfill process finished successfully.", "timestamp": "2026-07-13T21:17:41.759228+00:00", ...}
```
As verified, only `coc_members` was processed and loaded with 10,165 full player payload rows, leaving other tables untouched.
