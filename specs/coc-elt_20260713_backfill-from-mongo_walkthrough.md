---
title: "Historical MongoDB Data Backfill Walkthrough"
project_id: "coc-elt"
nyutu_uuid: "e3d82f32-fc1e-49d8-9b16-fde314b1e31a"
artifact_type: "Technical Discovery"
tags:
  - "backfill"
  - "mongodb"
  - "bigquery"
  - "walkthrough"
source_uri: "specs/coc-elt_20260713_backfill-from-mongo_walkthrough.md"
---

# Walkthrough: Backfill Script from Historical MongoDB Data

This document walks through the implementation, verification, and execution details for the historical MongoDB data backfill pipeline.

## 1. Implementation Steps Completed

### 1.1 Dependency Installation
- Run `uv add pymongo` to install the MongoDB Python client.
- Verified that `pymongo` and `dnspython` are added successfully to dependencies in `pyproject.toml`.

### 1.2 Backfill Script (`scripts/backfill_from_mongo.py`)
- **CLI Arguments**: Supports `--archive-path`, `--project-id`, `--dataset-id`, and `--mongo-image`.
- **Extraction**: Uses python's native `tarfile` module to extract the `coc_db` archive to a temporary directory in `/tmp`.
- **Permissions**: Recursively chmods the temp directory to `777` to guarantee read/write accessibility for the MongoDB Docker container.
- **Docker Container**: Spawns a temporary MongoDB container with the data directory mounted to `/data/db`. Uses a random host port to prevent port collisions.
- **Port Resolution**: Programmatically query container's random host port using `docker inspect` and queries the MongoClient's admin ping command with a timeout loop until MongoDB is ready.
- **Data Transformation**:
  - Drops metadata (`_id`, `players`) for the parent `coc_clan` table.
  - Flattens players under the `players` field and extracts only relevant keys for the `coc_members` table, inheriting the parent `extracted_at` timestamp.
  - Cleans and converts BSON types (like ObjectIds and datetime objects) to string/ISO8601 representations.
- **BigQuery Bulk Loading**: Loads all clean records via a temporary NDJSON file using `load_table_from_file` in a single job per target table (`coc_clan`, `coc_members`, `coc_current_war`, and `coc_capital_raids`).
- **Resource Cleanup**: Ensures MongoDB container is stopped and removed, and the temp directory is recursively deleted in a global `finally` block.

## 2. Test Verification (`tests/test_backfill_from_mongo.py`)
- Created comprehensive mock unit and integration tests using `unittest.mock` to mock `tarfile.open`, `subprocess.run` (for Docker run/inspect/stop/rm), `pymongo` client connections, and `bigquery.Client` load jobs.
- Executed and validated all 11 tests using:
  ```bash
  PYTHONPATH=. uv run pytest tests/test_backfill_from_mongo.py
  ```
- All tests completed successfully.
