---
title: "Configure BigQuery Client Project"
project_id: "coc-elt"
nyutu_uuid: "475b61dc-ac6b-4dbf-9438-c771d6b825e6"
artifact_type: "Architectural Decision"
tags:
  - "bigquery"
  - "python"
  - "testing"
  - "implementation_plan"
source_uri: "specs/coc_elt_20260712_configure_bq_client_project_implementation_plan.md"
---

# Implementation Plan - Configure BigQuery Client Project

This document details the architectural plan to configure the Google Cloud BigQuery client inside `BigQueryIngester` with the target `project_id`. This ensures that load jobs are explicitly executed within the configured Data Project rather than the default project resolved from the ambient credentials.

---

## 1. Requirements (WHAT is needed) - EARS Notation

- **R1 (Configure BigQuery Client)**: In `src/coc_elt/bq_client.py`, the system MUST configure `bigquery.Client` by passing the parameter `project=project_id` during instantiation within `BigQueryIngester.__init__`.
- **R2 (Happy Path Client Validation)**: WHEN `BigQueryIngester` is initialized, the system MUST verify that the BigQuery client is instantiated with the correct project identifier (`project_id`).
- **R3 (Unit Test Robustness)**: In `tests/test_bq_client.py`, the unit tests MUST assert that `bigquery.Client` is constructed with the `project` argument.
- **R4 (Verification)**: The test suite execution via `uv run pytest` MUST run successfully without failures.

---

## 2. Technical Decisions (HOW it will be built)

### File Modifications

#### 1. Modify `src/coc_elt/bq_client.py`
Change the instantiation of `bigquery.Client` inside the `BigQueryIngester` constructor:
```python
# Before:
self.client = bigquery.Client()

# After:
self.client = bigquery.Client(project=project_id)
```

#### 2. Modify `tests/test_bq_client.py`
Add assertions to verify that `mock_bq_client_cls` was called with the correct `project` argument:
```python
mock_bq_client_cls.assert_called_once_with(project="test-project")
```

### Discarded Alternatives
- **Setting Project via Environment Variables**: Discarded because passing the project explicitly to the client constructor ensures that the application behaves predictably regardless of ambient environment configurations or credentials setup.

---

## 3. Implementation Tasks

- [x] T1 — Modify `__init__` in `src/coc_elt/bq_client.py` to pass `project=project_id` to `bigquery.Client`.
- [x] T2 — Update unit tests in `tests/test_bq_client.py` to assert that `bigquery.Client` constructor was called with `project="test-project"`.
- [x] T3 — Run `uv run pytest` to verify all tests pass successfully.
