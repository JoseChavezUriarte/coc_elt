---
title: "Update API Client to Log Expected HTTP Statuses as INFO"
project_id: "coc-elt"
nyutu_uuid: "82f3320f-b46d-4ab2-a178-7cf6a93f9ffa"
artifact_type: "Business Logic Constraint"
tags:
  - "api-client"
  - "logging"
  - "http-errors"
  - "implementation_plan"
source_uri: "specs/coc-elt_20260713_update-api-client-logging_implementation_plan.md"
---

# Implementation Plan: Update API Client to Log Expected HTTP Statuses as INFO

This document details the requirements, technical decisions, and concrete tasks to update the Clash of Clans API client logging behavior for expected non-OK status codes (such as 404 Not Found for league groups).

---

## 1. Requirements (WHAT is needed) - EARS Notation

- **R1 (Signature Update)**: The `CocApiClient._get` method signature MUST accept `expected_statuses: Optional[List[int]] = None`.
- **R2 (Expected Failure Logging)**: WHEN an HTTP request in `_get` fails (i.e. `response.ok` is `False`), IF the response status code is in `expected_statuses`, THEN the system MUST log an `INFO` message with details (`url`, `status_code`, `response_text`).
- **R3 (Unexpected Failure Logging)**: WHEN an HTTP request in `_get` fails (i.e. `response.ok` is `False`), IF the response status code is NOT in `expected_statuses` (or `expected_statuses` is `None`), THEN the system MUST log an `ERROR` message with details (`url`, `status_code`, `response_text`).
- **R4 (League Group Call)**: WHEN `fetch_league_group` calls `_get`, the system MUST pass `expected_statuses=[404]`.
- **R5 (Unit Tests Verification)**: The unit tests in `tests/test_api_client.py` MUST verify the signature, the custom log level (verifying `INFO` log on expected status and `ERROR` log on unexpected status), and the league group fetch logic behavior.

---

## 2. Technical Decisions (HOW it will be built)

### Files Impacted
- **Modify**:
  - `src/coc_elt/api_client.py`
  - `tests/test_api_client.py`

### Programmatic Signatures
- **In `src/coc_elt/api_client.py`**:
  - Add `List` to the typing imports.
  - Update `_get` signature to:
    ```python
    def _get(self, endpoint: str, expected_statuses: Optional[List[int]] = None) -> Dict[str, Any]:
    ```

### Log/Error Handling Logic
- In `_get`, check if `response.status_code` is in `expected_statuses` when `not response.ok`.
  ```python
  if not response.ok:
      if expected_statuses and response.status_code in expected_statuses:
          logger.info(
              "Failed to fetch data from Clash of Clans API (expected status)",
              extra={
                  "url": url,
                  "status_code": response.status_code,
                  "response_text": response.text
              }
          )
      else:
          logger.error(
              "Failed to fetch data from Clash of Clans API",
              extra={
                  "url": url,
                  "status_code": response.status_code,
                  "response_text": response.text
              }
          )
      response.raise_for_status()
  ```

### Discarded Alternatives
- **Alternative 1: Raise a custom exception and handle it in the caller instead of checking inside `_get`**
  - *Reason Discarded*: The error logging is done immediately within `_get` upon getting a non-OK status. Moving the logging out of `_get` would duplicate logging logic in every caller. Passing the expected status list down to `_get` keeps the logging logic centralized and unified.
- **Alternative 2: Check for 404 response in `fetch_league_group` and don't call raise_for_status at all**
  - *Reason Discarded*: It is safer to keep the exact same exception flow (raising HTTPError) so we don't break existing calling code or change the contract of `_get` other than the log level customization.

---

## 3. Implementation Tasks (Concrete STEPS)

- [x] T1 — Import `List` from `typing` in `src/coc_elt/api_client.py`.
- [x] T2 — Update the signature of `_get` in `src/coc_elt/api_client.py` to accept `expected_statuses: Optional[List[int]] = None`.
- [x] T3 — Update the logging conditional logic inside `_get` in `src/coc_elt/api_client.py` to log as INFO if the status code is in `expected_statuses`, and as ERROR otherwise.
- [x] T4 — Update `fetch_league_group` in `src/coc_elt/api_client.py` to pass `expected_statuses=[404]` to the `_get` call.
- [x] T5 — Add test `test_get_expected_status_logged_as_info` in `tests/test_api_client.py`.
- [x] T6 — Add test `test_get_unexpected_status_logged_as_error` in `tests/test_api_client.py`.
- [x] T7 — Update/augment test `test_fetch_league_group_404` in `tests/test_api_client.py` to assert INFO logging behavior.
- [x] T8 — Run `pytest` locally to ensure all tests pass.
