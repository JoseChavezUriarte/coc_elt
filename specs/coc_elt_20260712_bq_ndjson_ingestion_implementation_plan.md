---
title: "BigQuery NDJSON Batch Loading Ingestion with Pydantic Data Contracts"
project_id: "coc-elt"
nyutu_uuid: "a6999029-13fa-49b0-8051-4572f84eb575"
artifact_type: "Business Logic Constraint"
tags:
  - "bigquery"
  - "pydantic"
  - "python"
  - "ingestion"
  - "implementation_plan"
source_uri: "specs/coc_elt_20260712_bq_ndjson_ingestion_implementation_plan.md"
---

# Implementation Plan - BigQuery NDJSON Batch Ingestion and Pydantic Data Contracts

This document details the architectural plan for combining Pydantic Data Contracts with BigQuery NDJSON batch loading. Pydantic acts as a fail-fast circuit breaker right after extraction, preventing malformed payloads from reaching the batch loader.

---

## 1. Requirements (WHAT is needed) - EARS Notation

- **R1 (Pydantic Data Contracts)**: In `src/coc_elt/models.py`, the system MUST define flexible Pydantic `BaseModel` classes using baseline schemas:
  - `ClanRecord`: tag (str, mandatory), name (str, mandatory), other fields Optional, extra='allow'.
  - `MemberRecord`: tag (str, mandatory), name (str, mandatory), other fields Optional, extra='allow'.
  - `MemberListResponse`: items (List[MemberRecord], mandatory), with `@model_validator(mode='before')` that delegates to a shared validation function to normalize pagination envelopes.
  - `WarRecord`: state (str, mandatory), other fields Optional, extra='allow'.
  - `CapitalRaidRecord`: state (str, mandatory), startTime (str, mandatory), other fields Optional, extra='allow'.
  - `CapitalRaidListResponse`: items (List[CapitalRaidRecord], mandatory), with `@model_validator(mode='before')` that delegates to a shared validation function to normalize pagination envelopes.
- **R2 (DRY Model Validation)**: The system MUST define a single, reusable validation function for pagination envelopes and apply it to both list response models in `models.py` to eliminate code duplication.
- **R3 (Endpoint & Schema Separation)**: The system MUST completely separate the `ClanRecord` schema from the `Player` / `Member` details schemas. The schemas MUST be strictly limited to the fields returned by their respective API endpoints; `ClanRecord` MUST NOT import, depend on, or embed player profile schemas (e.g. `Player` or `PlayerAchievement`).
- **R4 (Ingest Batch Method)**: In `src/coc_elt/bq_client.py`, the system MUST remove `ingest_record` and implement `ingest_batch(self, table_name: str, records: List[Dict[str, Any]], extracted_at: datetime) -> None`.
- **R5 (Context Manager Ephemeral Storage)**: In `ingest_batch`, the system MUST write records as NDJSON using `tempfile.NamedTemporaryFile(mode='w+', suffix='.json')` within a `with` context block to guarantee immediate cleanup from the ephemeral `/tmp/` filesystem.
- **R6 (BigQuery Load Job)**: The system MUST load the temporary file into BigQuery using `self.client.load_table_from_file` with a `LoadJobConfig` configured with `source_format = bigquery.SourceFormat.NEWLINE_DELIMITED_JSON` and `write_disposition = bigquery.WriteDisposition.WRITE_APPEND`.
- **R7 (Error Handling)**: The system MUST call `job.result()` to await completion, and IF the load job fails with errors, THEN the system MUST raise a `RuntimeError`.
- **R8 (Fault Isolation Orchestration)**: In `src/coc_elt/main.py`, the pipeline MUST isolate the extraction, validation, and ingestion cycle per data domain (Clan, Members, Current War, Capital Raids) using independent `try...except pydantic.ValidationError` blocks:
  - IF a domain fails validation, the system MUST log the error as severe (flagging the Cloud Run execution) but continue the execution of the other domains.
- **R9 (Unit Tests)**: The test suite MUST verify correct functionality using unit tests in `tests/test_bq_client.py` and `tests/test_main.py` to assert both happy path batch ingestion and fail-fast circuit breaker validation errors per data domain.

---

## 2. Technical Decisions (HOW it will be built)

### DRY Model Validation
A reusable helper function `normalize_envelope` is declared at the module level in `models.py` and used inside `@model_validator(mode='before')` in both `MemberListResponse` and `CapitalRaidListResponse` to enforce strict envelope parsing without duplicating logic.

### Fault Isolation and Partial Success Orchestration
The orchestration in `main.py` is structured in isolated sequential domain steps. A validation error in `fetch_members` will be logged as severe, but the pipeline will continue to fetch, validate, and ingest `fetch_current_war` and `fetch_capital_raids`.

### Proposed New File: `src/coc_elt/models.py`
```python
from typing import Any, List
from pydantic import BaseModel, ConfigDict, model_validator

def normalize_envelope(data: Any) -> Any:
    if isinstance(data, dict):
        if "items" in data:
            return data
        raise ValueError(f"Expected pagination envelope with an 'items' array. Received keys: {list(data.keys())}")
    if isinstance(data, list):
        return {"items": data}
    raise ValueError(f"Root payload must be a dictionary envelope or a list. Received type: {type(data).__name__}")

class ClanRecord(BaseModel):
    model_config = ConfigDict(extra='allow')
    tag: str
    name: str

class MemberRecord(BaseModel):
    model_config = ConfigDict(extra='allow')
    tag: str
    name: str

class MemberListResponse(BaseModel):
    items: List[MemberRecord]

    @model_validator(mode='before')
    @classmethod
    def validate_envelope(cls, data: Any) -> Any:
        return normalize_envelope(data)

class WarRecord(BaseModel):
    model_config = ConfigDict(extra='allow')
    state: str

class CapitalRaidRecord(BaseModel):
    model_config = ConfigDict(extra='allow')
    state: str
    startTime: str

class CapitalRaidListResponse(BaseModel):
    items: List[CapitalRaidRecord]

    @model_validator(mode='before')
    @classmethod
    def validate_envelope(cls, data: Any) -> Any:
        return normalize_envelope(data)
```

### Proposed File Modifications

#### 1. Modify `src/coc_elt/bq_client.py`
*   Remove `ingest_record`.
*   Implement `ingest_batch(self, table_name: str, records: List[Dict[str, Any]], extracted_at: datetime) -> None` using `NamedTemporaryFile` in a `with` block, formatting row dicts as `{"extracted_at": extracted_at.isoformat(), "payload": r}`.

#### 2. Modify `src/coc_elt/main.py`
*   Separate extraction, validation, and ingestion per domain with isolated try-except blocks:
    ```python
    from pydantic import ValidationError
    from coc_elt.models import ClanRecord, MemberListResponse, WarRecord, CapitalRaidListResponse

    # 1. Clan Domain
    try:
        logger.info("Processing Clan domain", extra={"step": "domain_clan"})
        clan_raw = api_client.fetch_clan()
        clan_val = ClanRecord.model_validate(clan_raw)
        ingester.ingest_batch("coc_clan", [clan_val.model_dump(mode="json")], now_utc)
    except ValidationError as e:
        logger.error("Validation failed for Clan domain. Skipping ingestion.", exc_info=e)

    # 2. Members Domain
    try:
        logger.info("Processing Members domain", extra={"step": "domain_members"})
        members_raw = api_client.fetch_members()
        members_val = MemberListResponse.model_validate(members_raw)
        members_records = [m.model_dump(mode="json") for m in members_val.items]
        ingester.ingest_batch("coc_members", members_records, now_utc)
    except ValidationError as e:
        logger.error("Validation failed for Members domain. Skipping ingestion.", exc_info=e)

    # 3. Current War Domain
    try:
        logger.info("Processing Current War domain", extra={"step": "domain_war"})
        war_raw = api_client.fetch_current_war()
        if war_raw is not None:
            war_val = WarRecord.model_validate(war_raw)
            ingester.ingest_batch("coc_current_war", [war_val.model_dump(mode="json")], now_utc)
    except ValidationError as e:
        logger.error("Validation failed for Current War domain. Skipping ingestion.", exc_info=e)

    # 4. Capital Raids Domain
    if is_capital_raid_day(now_utc):
        try:
            logger.info("Processing Capital Raids domain", extra={"step": "domain_raids"})
            raids_raw = api_client.fetch_capital_raids()
            raids_val = CapitalRaidListResponse.model_validate(raids_raw)
            raids_records = [r.model_dump(mode="json") for r in raids_val.items]
            ingester.ingest_batch("coc_capital_raids", raids_records, now_utc)
        except ValidationError as e:
            logger.error("Validation failed for Capital Raids domain. Skipping ingestion.", exc_info=e)
    ```

#### 3. Modify `tests/test_bq_client.py`
*   Update unit tests to test `ingest_batch` with `load_table_from_file` mock.

#### 4. Modify `tests/test_main.py`
*   Assert `ingest_batch` call behavior and dynamic error cases.
*   Add unit tests mocking single API endpoint failures to assert that the remaining domains are successfully processed (partial success).

---

## 3. Implementation Tasks

- [x] T1 — Create `src/coc_elt/models.py` with DRY Pydantic envelope validators.
- [x] T2 — Refactor `src/coc_elt/bq_client.py` to implement `ingest_batch` with context-managed temporary NDJSON files.
- [x] T3 — Refactor `src/coc_elt/main.py` to implement isolated domain processing loops with try-except blocks.
- [x] T4 — Refactor unit tests in `tests/test_bq_client.py` to test batch loading.
- [x] T5 — Refactor pipeline tests in `tests/test_main.py` to assert correct mock ingestion counts, partial success fault isolation, and validation failures.
- [x] T6 — Run unit tests (`uv run pytest`) to confirm all changes are correct and pass successfully.
