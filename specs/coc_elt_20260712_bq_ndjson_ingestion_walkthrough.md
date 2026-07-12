---
title: "BigQuery NDJSON Ingestion and Pydantic Data Contracts Walkthrough"
project_id: "coc-elt"
nyutu_uuid: "97a29c6a-9c3d-4659-b266-016e11b678e3"
artifact_type: "Business Logic Constraint"
tags:
  - "bigquery"
  - "pydantic"
  - "python"
  - "ingestion"
  - "walkthrough"
source_uri: "specs/coc_elt_20260712_bq_ndjson_ingestion_walkthrough.md"
---

### Execution Context
- **Timestamp**: 2026-07-12T12:24:56-05:00
- **Objective**: Implement BigQuery NDJSON batch loading and robust Pydantic data contract validation for the Clash of Clans ELT pipeline.

### Executed Commands
- `uv run pytest` (verified all 13 tests passed successfully)
- `git commit`

### State Mutations
- **Created**:
  - `src/coc_elt/models.py`
  - `specs/coc_elt_20260712_bq_ndjson_ingestion_walkthrough.md`
- **Modified**:
  - `src/coc_elt/bq_client.py`
  - `src/coc_elt/main.py`
  - `tests/test_bq_client.py`
  - `tests/test_main.py`
  - `specs/coc_elt_20260712_bq_ndjson_ingestion_implementation_plan.md`

### Architectural Decisions (ADR) and SOLID
- **Single Responsibility Principle (SRP)**: Separated API data schema validation into `models.py` and ingestion logic into `bq_client.py`.
- **Fault Isolation (Circuit Breaker)**: Isolated step validation/ingestion loops per domain (Clan, Members, War, Raids) in `main.py` so validation or API failure in one domain does not stop processing of other domains.
- **DRY Principle**: Created a common modules-level `normalize_envelope` function in `models.py` reused by multiple response schemas.

### Validation Artifacts
- Output of `uv run pytest`:
  ```
  tests/test_api_client.py ....                                            [ 30%]
  tests/test_bq_client.py ....                                             [ 61%]
  tests/test_logging.py ..                                                 [ 76%]
  tests/test_main.py ...                                                   [100%]
  13 passed in 0.18s
  ```

### Technical Debt
- None.
