---
title: "Update player mapping and truncate table in backfill"
project_id: "coc-elt"
nyutu_uuid: "459bb725-4050-44dc-8fae-50786927fe64"
artifact_type: "Business Logic Constraint"
tags:
  - "backfill"
  - "mongodb"
  - "bigquery"
  - "implementation_plan"
source_uri: "specs/coc-elt_20260713_update-backfill-mapping_implementation_plan.md"
---

# Implementation Plan: Update Player Mapping and Truncate Table in Backfill

This document outlines the architectural plan to update the MongoDB historical data backfill script. It maps the full player profile payload instead of a filtered subset, sets the BigQuery loading strategy for `coc_members` to overwrite existing data, and adapts the test suite accordingly.

## 1. Requirements (WHAT is needed) - EARS Notation

- **R1 (Full Player Profile Mapping)**: The system MUST map the entire player profile document from the `players` array of the MongoDB `clan` collection as the payload for the `coc_members` BigQuery table, without filtering via a whitelist.
- **R2 (Truncate coc_members Table)**: WHEN loading the backfill data into the `coc_members` BigQuery table, the system MUST set the load job's `write_disposition` to `WRITE_TRUNCATE`.
- **R3 (Table Filtering CLI Argument)**: The system MUST support a CLI argument `--table` (default: `"all"`) to restrict backfill execution to a specific target table.
- **R3.1 (Only Process coc_members)**: WHEN `--table coc_members` is passed, the system MUST ONLY extract, map, and load data for the `coc_members` table, completely skipping the ingestion of `coc_clan`, `coc_current_war`, and `coc_capital_raids`.
- **R4 (Test Assertion Updates for Payload)**: The system MUST update the assertions in `tests/test_backfill_from_mongo.py` to verify that the full player profile (including previously filtered keys like `extra_field`) is preserved in the payload.
- **R5 (Test Assertion Updates for Write Disposition)**: The system MUST update the assertions in `tests/test_backfill_from_mongo.py` to verify that `load_table_data` is invoked with `WRITE_TRUNCATE` for the `coc_members` table and defaults to `WRITE_APPEND` for the other tables.
- **R6 (Cleanup on Failure)**: IF a BigQuery load job fails, THEN the system MUST raise an exception, aborting the process while ensuring cleanup of temporary Docker containers and directories.

## 2. Technical Decisions (HOW it will be built)

### Files Impacted
- **Modify**:
  - `scripts/backfill_from_mongo.py`
  - `tests/test_backfill_from_mongo.py`

### Programmatic Signatures
- **Modify** `load_table_data` function signature to accept a `write_disposition` parameter:
  ```python
  def load_table_data(
      bq_client: bigquery.Client,
      table_id: str,
      rows: List[Dict[str, Any]],
      write_disposition: str = bigquery.WriteDisposition.WRITE_APPEND
  ) -> None:
  ```
- **Modify** the logic in `process_and_backfill` to pass the entire player profile object:
  ```python
  # Instead of:
  # player_payload = {k: player[k] for k in keys_to_keep if k in player}
  # Use:
  player_payload = player
  ```
- **Modify** target load job execution for `coc_members`:
  ```python
  load_table_data(
      bq_client,
      f"{project_id}.{dataset_id}.coc_members",
      member_rows,
      write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
  )
  ```

### Discarded Alternatives
- **Alternative 1: Executing a separate `TRUNCATE TABLE` DDL statement prior to the load.**
  - *Reason Discarded*: Running separate truncate queries adds overhead, extra API calls, and increases vulnerability to failures. Setting `WRITE_TRUNCATE` natively on the BigQuery load job is atomic, standard, and highly robust.
- **Alternative 2: Disabling BSON serialization cleaning (`clean_mongo_doc`) for nested player structures.**
  - *Reason Discarded*: MongoDB player documents contain complex nested objects. Retaining `clean_mongo_doc` is essential to prevent serialization errors when writing to the temporary NDJSON file.

## 3. Implementation Tasks (Concrete STEPS)

- [x] T1 — Add `write_disposition` parameter to `load_table_data` in `scripts/backfill_from_mongo.py`.
- [x] T2 — Update player mapping in `process_and_backfill` inside `scripts/backfill_from_mongo.py` to map the entire player dict and set `WRITE_TRUNCATE` for the `coc_members` load job.
- [x] T3 — Update `test_process_and_backfill_mapping` and other tests in `tests/test_backfill_from_mongo.py` to reflect the full mapping changes and verify that the previously discarded fields are now part of the payload.
- [x] T4 — Update `test_load_table_data` and mock expectations in `tests/test_backfill_from_mongo.py` to assert the correct `write_disposition` argument is passed.
- [x] T5 — Run the pytest suite using `PYTHONPATH=. uv run pytest tests/test_backfill_from_mongo.py` to verify the modified tests pass.
- [x] T6 — Run the backfill script command `PYTHONPATH=. uv run python scripts/backfill_from_mongo.py` to reload the `coc_members` table.
