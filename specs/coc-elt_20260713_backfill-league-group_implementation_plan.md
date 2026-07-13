---
title: "Backfill coc_league_group table from historical MongoDB data"
project_id: "coc-elt"
nyutu_uuid: "15ceb4d3-5960-466b-87df-596e1e60b4e8"
artifact_type: "Business Logic Constraint"
tags:
  - "backfill"
  - "mongodb"
  - "bigquery"
  - "implementation_plan"
source_uri: "specs/coc-elt_20260713_backfill-league-group_implementation_plan.md"
---

# Implementation Plan - Backfill coc_league_group table from historical MongoDB data

This document outlines the architectural plan to backfill the `coc_league_group` BigQuery table using historical data from MongoDB. It identifies the target MongoDB collections, updates the CLI and mappings in the backfill script, and defines corresponding unit tests.

## 1. Requirements (WHAT is needed) - EARS Notation

- **R1 (Arg Option)**: The system MUST accept `coc_league_group` as a valid `--table` option in the CLI arguments of `scripts/backfill_from_mongo.py`.
- **R2 (Target Collection Discovery)**: The system MUST dynamically discover whether the collection is named `'warleague'` or `'warleagues'` in the Clash of Clans MongoDB database.
- **R3 (Mapping)**: WHEN mapping the warleague collection, the system MUST map each document to the BigQuery `coc_league_group` table schema:
  - `extracted_at`: The extraction ISO timestamp (extracted from the document's `extracted_at` or fallback BSON ObjectId generation time).
  - `payload`: The cleaned JSON document representing the LeagueGroupRecord model (excluding the `_id` field).
- **R4 (BSON Cleaning)**: The system MUST clean BSON types recursively in the payload using `clean_mongo_doc`.
- **R5 (Write Disposition)**: WHEN loading data into the `coc_league_group` BigQuery table, the system MUST set the write disposition to `WRITE_TRUNCATE`.
- **R6 (Table Filtering)**: WHEN `--table coc_league_group` is specified, the system MUST only process the warleague collection and write to the `coc_league_group` table, completely skipping `coc_clan`, `coc_members`, `coc_current_war`, and `coc_capital_raids`.
- **R7 (Test Mocking)**: The test suite MUST define mock data for the warleague/warleagues collection and verify proper mapping, payload cleaning, table filtering, and the `WRITE_TRUNCATE` write disposition.

## 2. Technical Decisions (HOW it will be built)

### Files Impacted
- **Modify**:
  - `scripts/backfill_from_mongo.py`
  - `tests/test_backfill_from_mongo.py`

### Programmatic Signatures & Logic
- **Modify** `process_and_backfill` to check database collections dynamically:
  ```python
  # Process 'warleague' / 'warleagues' collection
  warleague_col = next((c for c in ("warleague", "warleagues") if c in cols), None)
  if warleague_col and table in ("all", "coc_league_group"):
      league_group_rows: List[Dict[str, Any]] = []
      logger.info("Processing collection '%s'...", warleague_col)
      for doc in db[warleague_col].find():
          extracted_at_str = get_extracted_at(doc).isoformat()
          payload = {k: v for k, v in doc.items() if k != "_id"}
          league_group_rows.append({
              "extracted_at": extracted_at_str,
              "payload": clean_mongo_doc(payload)
          })
      load_table_data(
          bq_client,
          f"{project_id}.{dataset_id}.coc_league_group",
          league_group_rows,
          write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
      )
  ```
- **Modify** `main` CLI options parser to add `"coc_league_group"` to targets.

### Discarded Alternatives
- **Alternative**: Hardcoding a single collection name (like `"warleague"`).
  - *Reason Discarded*: The MongoDB archive might have either `"warleague"` or `"warleagues"` depending on the historical crawl run. A dynamic check ensures compatibility.
- **Alternative**: Appending records instead of truncating.
  - *Reason Discarded*: Truncating ensures clean backfills, avoiding duplication of records during rerun scenarios.

## 3. Implementation Tasks (Concrete STEPS)

- [x] T1 — Add `"coc_league_group"` to the `--table` choices and CLI help in `scripts/backfill_from_mongo.py`.
- [x] T2 — Implement dynamic discovery of `"warleague"` vs. `"warleagues"` collection name in `process_and_backfill` of `scripts/backfill_from_mongo.py`.
- [x] T3 — Add collection mapping logic for the warleague collection to BigQuery payload format and load with `WRITE_TRUNCATE` in `scripts/backfill_from_mongo.py`.
- [x] T4 — Add mock collection and documents for warleague in `tests/test_backfill_from_mongo.py`.
- [x] T5 — Implement `test_process_and_backfill_mapping_league_group` and update table filtering test in `tests/test_backfill_from_mongo.py`.
- [x] T6 — Run test suite to verify implementation correctness: `PYTHONPATH=. uv run pytest tests/test_backfill_from_mongo.py`.
- [x] T7 — Execute the backfill command to run backfill specifically for `coc_league_group`: `PYTHONPATH=. uv run python scripts/backfill_from_mongo.py --table coc_league_group`.

## 4. Validation and Execution Commands

- **Validation Command**:
  ```bash
  PYTHONPATH=. uv run pytest tests/test_backfill_from_mongo.py
  ```
- **Execution Command**:
  ```bash
  PYTHONPATH=. uv run python scripts/backfill_from_mongo.py --table coc_league_group
  ```
