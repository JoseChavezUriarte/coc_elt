---
title: "Historical MongoDB Data Backfill Walkthrough for coc_league_group Table"
project_id: "coc-elt"
nyutu_uuid: "b6cfaac9-d2db-476b-971a-0dc2eb1f11ec"
artifact_type: "Technical Discovery"
tags:
  - "backfill"
  - "mongodb"
  - "bigquery"
  - "walkthrough"
source_uri: "specs/coc-elt_20260713_backfill-league-group_walkthrough.md"
---

# Walkthrough: Backfill coc_league_group Table from Historical MongoDB Data

This document walks through the implementation, verification, and execution details for backfilling the `coc_league_group` table from historical MongoDB data.

## 1. Implementation Steps Completed

### 1.1 Backfill Script Updates (`scripts/backfill_from_mongo.py`)
- **CLI Arguments**: Updated `--table` option choices to include `coc_league_group`.
- **Database Discovery**: Enhanced target database discovery to also check for `warleague` or `warleagues` collections.
- **Dynamic Collection Mapping**:
  - Dynamically detects if `'warleague'` or `'warleagues'` is in the database collections.
  - For each document, maps the `extracted_at` field (falling back to ObjectId generation time if missing) and recursively BSON cleans the rest of the fields into the `payload` field.
  - Skips processing for other tables if table filtering is restricted to `coc_league_group`.
- **BigQuery Write Disposition**: Loads mapped rows to `coc_league_group` using `WRITE_TRUNCATE` write disposition.

## 2. Test Verification (`tests/test_backfill_from_mongo.py`)
- Mapped a mock `warleague` and `warleagues` collection in mock database.
- Verified correct mapping and write disposition (`WRITE_TRUNCATE`) assertions for `coc_league_group`.
- Updated table filtering tests to cover `coc_league_group`.
- Executed and validated all tests successfully using:
  ```bash
  PYTHONPATH=. uv run pytest tests/test_backfill_from_mongo.py
  ```
- All 13 tests passed.

## 3. Backfill Execution Details
- Executed backfill using the following command:
  ```bash
  PYTHONPATH=. uv run python scripts/backfill_from_mongo.py --table coc_league_group
  ```
- **Execution Log Highlights**:
  - Dynamic discovery detected Clash of Clans database `'coc_db'`.
  - Found and processed collection `'warleagues'`.
  - Cleaned, mapped, and successfully loaded **93 rows** into `swift-capsule-492817-a7.coc_bronze.coc_league_group` using a single bulk load job.
