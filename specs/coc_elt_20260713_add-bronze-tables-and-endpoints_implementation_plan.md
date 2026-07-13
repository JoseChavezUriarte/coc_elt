---
title: "Add Bronze Tables, Player and League Group/War Endpoints and Pipeline Steps"
project_id: "coc-elt"
nyutu_uuid: "81cef334-7439-4641-9b3b-f71141a32b1f"
artifact_type: "Architectural Decision"
tags:
  - "bigquery"
  - "python"
  - "elt"
  - "implementation_plan"
source_uri: "specs/coc_elt_20260713_add-bronze-tables-and-endpoints_implementation_plan.md"
---

# Implementation Plan - Add Bronze Tables, Player and League Group/War Endpoints and Pipeline Steps

This plan details the implementation steps required to add new bronze tables, support new Clash of Clans API endpoints, update/add pipeline ingestion steps, and add corresponding unit tests.

## 1. Requirements (WHAT is needed) - EARS Notation
- **R1**: The system MUST deploy two new BigQuery Bronze tables: `coc_league_group` and `coc_warleague_war`.
- **R2**: The `CocApiClient` MUST fetch player data from the `/players/{player_tag}` endpoint.
- **R3**: The `CocApiClient` MUST fetch current war league group data from the `/clans/{clan_tag}/currentwar/leaguegroup` endpoint.
- **R4**: IF the league group request returns a 404 response, THEN the `CocApiClient` MUST return `None`.
- **R5**: The `CocApiClient` MUST fetch war league war data from the `/clanwarleagues/wars/{war_tag}` endpoint.
- **R6**: The Pydantic model `LeagueGroupRecord` MUST validate `state` and `season` with `extra='allow'`.
- **R7**: The Pydantic model `WarLeagueWarRecord` MUST validate `state` with `extra='allow'`.
- **R8**: WHEN running the members step, the pipeline MUST fetch `clan_raw` if not already retrieved.
- **R9**: WHEN running the members step, the pipeline MUST fetch player details for each member in `clan_raw["memberList"]`.
- **R10**: WHEN running the members step, the pipeline MUST validate each player response using `MemberRecord`.
- **R11**: WHEN running the members step, the pipeline MUST load all validated player profiles as a batch into the `coc_members` table.
- **R12**: WHEN running the league group step, the pipeline MUST fetch the current league group.
- **R13**: WHEN running the league group step, the pipeline MUST load the validated league group into `coc_league_group`.
- **R14**: WHEN running the league group step, the pipeline MUST iterate over the round war tags.
- **R15**: WHILE iterating over round war tags, the pipeline MUST ignore the tag `#0`.
- **R16**: WHEN running the league group step, the pipeline MUST fetch and validate each war league war using `WarLeagueWarRecord`.
- **R17**: WHEN running the league group step, the pipeline MUST load all validated war league wars as a batch into the `coc_warleague_war` table.
- **R18**: The test suite MUST verify all new API endpoints (`fetch_player`, `fetch_league_group`, `fetch_warleague_war`) and their response/error handling.
- **R19**: The test suite MUST verify that BigQuery ingestion operates correctly for the new tables.
- **R20**: The test suite MUST verify the end-to-end pipeline execution flow including the updated members step and the new league group/war league step.

## 2. Technical Decisions (HOW it will be built)

### Files to Modify
- `terraform/bigquery.tf`: Update `local.tables` to include `"league_group"` and `"warleague_war"`.
- `src/coc_elt/api_client.py`:
  - Add `fetch_player` method.
  - Add `fetch_league_group` method (handling 404 response to return `None`).
  - Add `fetch_warleague_war` method.
- `src/coc_elt/models.py`:
  - Add `LeagueGroupRecord` Pydantic class.
  - Add `WarLeagueWarRecord` Pydantic class.
- `src/coc_elt/main.py`:
  - Refactor `Members Domain` section.
  - Add `League Group & War League Domain` section.
- `tests/test_api_client.py`:
  - Add mock tests for the new API functions.
- `tests/test_bq_client.py`:
  - Add/ensure mock tests for ingesting new tables.
- `tests/test_main.py`:
  - Update `test_run_pipeline_success`, `test_run_pipeline_partial_success_api_failure`, and `test_run_pipeline_partial_success_validation_failure` to mock the new API calls and assert the additional `ingest_batch` operations.

### New Signatures
- `def fetch_player(self, player_tag: str) -> Dict[str, Any]` in `api_client.py`
- `def fetch_league_group(self) -> Optional[Dict[str, Any]]` in `api_client.py`
- `def fetch_warleague_war(self, war_tag: str) -> Dict[str, Any]` in `api_client.py`
- `class LeagueGroupRecord(BaseModel)` in `models.py`
- `class WarLeagueWarRecord(BaseModel)` in `models.py`

### Error Handling
- Capture `requests.HTTPError` with `response.status_code == 404` in `fetch_league_group()` and return `None`. Other HTTP errors will be reraised.
- Use the existing try/except block structure in `src/coc_elt/main.py` per domain step to catch validation/pipeline errors, log them, and prevent pipeline execution from failing for other domains.

### Discarded Alternatives
- **Alternative**: Performing concurrent requests using threads or async io for fetching player profile tag details to speed up.
  - **Reason for rejection**: The clan size is small (max 50) and simplicity and reliability of synchronous execution are preferred.
- **Alternative**: Storing CWL round wars within the league group table dynamically.
  - **Reason for rejection**: Normalizing/keeping tables separated at the bronze landing layer makes parsing easier in Dataform later and keeps schemas flat.
- **Alternative**: Automatic auto-applying of terraform updates without prompt.
  - **Reason for rejection**: Infra changes need safe plan & manual confirmation before deploying.

## 3. Implementation Tasks (Concrete STEPS)
- [x] T1 — Add `"league_group"` and `"warleague_war"` to `local.tables` list in `terraform/bigquery.tf`.
- [x] T2 — Implement `fetch_player` in `src/coc_elt/api_client.py` using URL encoding for the tag.
- [x] T3 — Implement `fetch_league_group` in `src/coc_elt/api_client.py` with 404 response handling.
- [x] T4 — Implement `fetch_warleague_war` in `src/coc_elt/api_client.py` using URL encoding for the tag.
- [x] T5 — Define `LeagueGroupRecord` in `src/coc_elt/models.py`.
- [x] T6 — Define `WarLeagueWarRecord` in `src/coc_elt/models.py`.
- [x] T7 — Refactor the members step in `src/coc_elt/main.py` to loop over member list, fetch player profile, validate, and batch load.
- [x] T8 — Add League Group & War League step in `src/coc_elt/main.py` to fetch, validate, and load league groups and round wars.
- [x] T9 — Add mock unit tests for the new client methods in `tests/test_api_client.py`.
- [x] T10 — Add/update unit tests in `tests/test_bq_client.py` to include ingestion validation for new tables.
- [x] T11 — Update pipeline execution test assertions in `tests/test_main.py`.
- [x] T12 — Run Terraform validation (`terraform validate`) and planning (`terraform plan`) to prepare infrastructure.
- [x] T13 — Apply Terraform changes (`terraform apply`) with explicit confirmation.
