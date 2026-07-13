---
title: "Bronze Tables, Player and League Group/War Endpoints and Pipeline Steps Walkthrough"
project_id: "coc-elt"
nyutu_uuid: "66deb950-9317-4a81-9feb-0b57895fc29b"
artifact_type: "Walkthrough"
tags:
  - "bigquery"
  - "python"
  - "elt"
  - "walkthrough"
source_uri: "specs/coc_elt_20260713_add-bronze-tables-and-endpoints_walkthrough.md"
---

# Walkthrough - Bronze Tables, Player and League Group/War Endpoints and Pipeline Steps

This walkthrough details the changes implemented to support fetching player data and current war league group/war details, normalizing them, loading them into BigQuery bronze tables, and testing the pipeline execution.

## Changes Implemented

### 1. Terraform Infrastructure Additions
In [bigquery.tf](file:///home/scheveningen/documents/proyectos/coc_elt/terraform/bigquery.tf), we updated `local.tables` to include `"league_group"` and `"warleague_war"`.
This automatically provisions two new BigQuery tables:
- `coc_league_group`
- `coc_warleague_war`

The changes were successfully applied via `terraform apply -auto-approve`:
```
google_bigquery_table.tables["league_group"]: Creation complete after 0s
google_bigquery_table.tables["warleague_war"]: Creation complete after 0s
```

### 2. API Client Endpoints
We updated [api_client.py](file:///home/scheveningen/documents/proyectos/coc_elt/src/coc_elt/api_client.py) with the following methods:
- `fetch_player(self, player_tag: str) -> Dict[str, Any]` to retrieve player profiles from `/players/{player_tag}`.
- `fetch_league_group(self) -> Optional[Dict[str, Any]]` to retrieve the current war league group. It catches `requests.HTTPError` and returns `None` on `404` status code.
- `fetch_warleague_war(self, war_tag: str) -> Dict[str, Any]` to retrieve details of a specific war from `/clanwarleagues/wars/{war_tag}`.

### 3. Pydantic Models
In [models.py](file:///home/scheveningen/documents/proyectos/coc_elt/src/coc_elt/models.py), we added Pydantic models for validation:
- `LeagueGroupRecord` with validation for `state` and `season` (and `extra='allow'`).
- `WarLeagueWarRecord` with validation for `state` (and `extra='allow'`).

### 4. Main Pipeline Refactoring
In [main.py](file:///home/scheveningen/documents/proyectos/coc_elt/src/coc_elt/main.py):
- We refactored the members step to loop over the clan's `memberList`, fetch each player's profile via `api_client.fetch_player()`, validate using `MemberRecord`, and batch-load them into the `coc_members` table.
- We implemented the League Group & War League step to fetch the active league group. If rounds exist, we load the league group metadata, iterate over all round war tags (skipping `#0`), call `fetch_warleague_war()` for each, validate the responses, and batch-load them into `coc_warleague_war`.

### 5. Verification & Tests
Updated the unit test suites:
- [test_api_client.py](file:///home/scheveningen/documents/proyectos/coc_elt/tests/test_api_client.py) to cover the new endpoints including 404 response handling.
- [test_bq_client.py](file:///home/scheveningen/documents/proyectos/coc_elt/tests/test_bq_client.py) to assert that table routing functions correctly for the new tables.
- [test_main.py](file:///home/scheveningen/documents/proyectos/coc_elt/tests/test_main.py) to test end-to-end flow with mocks for the new API calls and verify correct batch ingestion counts.

All 29 tests pass successfully via `PYTHONPATH=. uv run pytest`.
