---
title: "Update API Client to Log Expected HTTP Statuses as INFO Walkthrough"
project_id: "coc-elt"
nyutu_uuid: "a9bed0f5-bf97-47f8-9938-a6a1051ae102"
artifact_type: "Business Logic Constraint"
tags:
  - "api-client"
  - "logging"
  - "http-errors"
  - "walkthrough"
source_uri: "specs/coc-elt_20260713_update-api-client-logging_walkthrough.md"
---

# Walkthrough: Update API Client to Log Expected HTTP Statuses as INFO

This document walks through the implementation and verification details for updating the Clash of Clans API client logging behavior. Non-OK status codes that are expected (such as 404 Not Found for league groups) are now logged as INFO instead of ERROR.

## 1. Implementation Details

### 1.1 Modifying `_get` Signature and Logging Logic
- Modified [src/coc_elt/api_client.py](file:///home/scheveningen/documents/proyectos/coc_elt/src/coc_elt/api_client.py) to import `List` from `typing`.
- Updated the signature of `_get` to:
  ```python
  def _get(self, endpoint: str, expected_statuses: Optional[List[int]] = None) -> Dict[str, Any]:
  ```
- Implemented a check inside `_get` to see if `response.status_code` is in `expected_statuses` when `not response.ok`.
- If the status code is expected, it logs using `logger.info("Failed to fetch data from Clash of Clans API (expected status)", ...)` to avoid cluttering error logs.
- Otherwise, it logs using `logger.error` as before.

### 1.2 Customizing League Group Fetch
- Passed `expected_statuses=[404]` to the `_get` call in `fetch_league_group` inside [src/coc_elt/api_client.py](file:///home/scheveningen/documents/proyectos/coc_elt/src/coc_elt/api_client.py) to ensure that 404 responses for league groups are logged at the `INFO` level.

## 2. Test Verification

### 2.1 Verification with Pytest
- Modified [tests/test_api_client.py](file:///home/scheveningen/documents/proyectos/coc_elt/tests/test_api_client.py) to:
  - Add unit tests verifying expected status code (like 404) logs at the `INFO` level and unexpected status code (like 500) logs at the `ERROR` level.
  - Update `test_fetch_league_group_404` to assert the correct `INFO` level logging behavior.
- Ran the test suite to verify everything passes:
  ```bash
  PYTHONPATH=. uv run pytest
  ```
  All 32 tests passed successfully.
