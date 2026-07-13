---
title: "Backfill Script from historical MongoDB data"
project_id: "coc-elt"
nyutu_uuid: "e2b429f5-66c2-4793-b238-0c4023409a3c"
artifact_type: "Business Logic Constraint"
tags:
  - "backfill"
  - "mongodb"
  - "bigquery"
  - "docker"
  - "implementation_plan"
source_uri: "specs/coc-elt_20260713_backfill-from-mongo_implementation_plan.md"
---

# Implementation Plan: Backfill Script from Historical MongoDB Data

This document details the architecture, requirements, and steps for implementing a backfill script to migrate historical Clash of Clans MongoDB data into BigQuery Bronze tables.

---

## 1. Requirements (WHAT is needed) - EARS Notation

- **R1 (Archive Extraction)**: WHEN the script executes, the system MUST extract the `coc_db` gzipped tar archive to a temporary directory under `/tmp`.
- **R2 (Directory Permissions)**: The system MUST recursive-chmod the extracted directory to `777` permission to allow the Docker container user to read and write database files.
- **R3 (Docker Container Setup)**: WHEN launching the MongoDB database, the system MUST spin up a temporary Docker container using the specified MongoDB image, mounting the extracted database directory as `/data/db`, exposing port 27017 on a random host port, and using a unique container name to avoid name collision.
- **R4 (Container Port Resolution)**: The system MUST programmatically query the host port mapped to the container's port 27017 and retry if the container is not fully started.
- **R5 (Database Discovery)**: The system MUST discover the MongoDB database containing the Clash of Clans collections (by checking which database contains collections like `clan` or `warlog`).
- **R6 (Clan Collection Mapping)**: WHEN mapping the `clan` collection:
  - The system MUST construct a `coc_clan` record from each document by stripping the `_id` and `players` fields.
  - The system MUST construct `coc_members` records by iterating over each player in the `players` array (which represents the members with detailed profiles) and inheriting the parent document's `extracted_at` timestamp.
- **R7 (Warlog Collection Mapping)**: WHEN mapping the `warlog` collection, the system MUST construct a `coc_current_war` record from each document by stripping the `_id` field.
- **R8 (Capital Raids Collection Mapping)**: WHEN mapping the `capital_raids` collection, the system MUST construct a `coc_capital_raids` record from each document by stripping the `_id` field.
- **R9 (Record Serialization)**: The system MUST serialize BSON fields (such as ObjectId and Datetime) to JSON-compatible types (ObjectId to its hex string, Datetime to UTC ISO8601 string) before writing to NDJSON.
- **R10 (BigQuery Single Load Job)**: For each target table, the system MUST write all transformed records to a single temporary NDJSON file where each line is `{"extracted_at": <isoformat>, "payload": <cleaned_payload>}` and perform exactly one load job per table to load them into BigQuery.
- **R11 (Resource Cleanup)**: The system MUST guarantee that the MongoDB container is stopped and removed, and the temporary extraction directory is deleted, even if execution succeeds, fails, or is interrupted.
- **R12 (Pytest Validation)**: The system MUST verify the backfill script's extraction, mapping, container-lifecycle, and BQ-loading logic using a comprehensive unit test suite in `tests/test_backfill_from_mongo.py`.

---

## 2. Technical Decisions (HOW it will be built)

### Files Impacted
- **Create**:
  - `scripts/backfill_from_mongo.py`
  - `tests/test_backfill_from_mongo.py`
- **Modify**:
  - `pyproject.toml` (add `pymongo` dependency)

### Python Package Addition
We need to add `pymongo` as a project dependency to handle the MongoDB database connection. We will use the subprocess CLI tool for Docker container management to keep dependencies lightweight.

### Programmatic Signatures
The script `scripts/backfill_from_mongo.py` will have the following structure:
- **CLI Arguments**:
  - `--archive-path`: Path to `coc_db` archive (default: `"coc_db"`).
  - `--project-id`: BigQuery project ID (default: read from settings, fallback: `"swift-capsule-492817-a7"`).
  - `--dataset-id`: BigQuery dataset ID (default: read from settings, fallback: `"coc_bronze"`).
  - `--mongo-image`: MongoDB Docker image to use (default: `"mongo:latest"`).
- **Core Functions**:
  - `get_extracted_at(doc: dict) -> datetime`: Resolves the extraction time. Prioritizes the `extracted_at` field (as datetime or parsed string) and falls back to BSON `ObjectId` generation time.
  - `clean_mongo_doc(doc: Any) -> Any`: Recursively cleans MongoDB-specific objects (like converting `ObjectId`s to strings, `datetime`s to ISO strings) to prevent JSON serialization errors.
  - `extract_archive(archive_path: str) -> str`: Extracts the gzipped tarball to a temporary directory under `/tmp`.
  - `make_dir_writable_for_docker(path: str) -> None`: Modifies the temporary directory and all files inside to be read/write/executable for all (chmod 777).
  - `run_mongo_container(db_path: str, image: str) -> tuple[str, int]`: Spawns a docker container, parses the host port mapping, and returns the container ID and host port.
  - `stop_and_remove_container(container_id: str) -> None`: Stops and removes the Docker container.
  - `load_table_data(bq_client, table_id: str, rows: list[dict]) -> None`: Generates a temporary NDJSON file, loads it into BigQuery via `load_table_from_file`, and ensures the file is closed and cleaned up.

### Error Handling & Safeguards
- The script will use a global `try...finally` block. The `finally` clause guarantees that the container is stopped and removed, and the temporary extraction directory is deleted, preserving host environment cleanliness.
- Port collision avoidance is achieved by exposing MongoDB's default `27017` port on a random host port (using `-p 27017` instead of `-p 27017:27017`).

### Discarded Alternatives
- **Alternative 1: Use Docker Python SDK (`docker` package)**
  - *Reason Discarded*: Introducing a Docker SDK dependency adds environment setup complexity (requiring user group configurations, mounting socket paths, etc.). Using `subprocess` to trigger the Docker CLI is direct, lightweight, and leverages existing developer setup.
- **Alternative 2: Streaming Inserts (`insert_rows_json`)**
  - *Reason Discarded*: The backfill involves importing a massive volume of historical logs. Streaming inserts are slow, risk hitting quota limitations, and are more expensive. Using a single `load_table_from_file` load job for each table is faster and follows BigQuery batch ingestion best practices.

---

## 3. Implementation Tasks (Concrete STEPS)

- [x] T1 — Add `pymongo` to `pyproject.toml` dependencies.
- [x] T2 — Implement helper functions (`get_extracted_at`, `clean_mongo_doc`) in `scripts/backfill_from_mongo.py`.
- [x] T3 — Implement directory extraction and permissions handling (`extract_archive`, `make_dir_writable_for_docker`) in `scripts/backfill_from_mongo.py`.
- [x] T4 — Implement container lifecycle functions (`run_mongo_container`, `stop_and_remove_container`) in `scripts/backfill_from_mongo.py`.
- [x] T5 — Implement mapping and BQ bulk loading logic in `scripts/backfill_from_mongo.py`.
- [x] T6 — Implement CLI argparse and main orchestration block with try/finally cleanup in `scripts/backfill_from_mongo.py`.
- [x] T7 — Add unit tests in `tests/test_backfill_from_mongo.py` mocking PyMongo, Docker commands, and BigQuery loading.
- [x] T8 — Run pytest to validate correctness of the test suite and ensure no regressions.
