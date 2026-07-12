---
title: "Configure BigQuery Client Project - Walkthrough"
project_id: "coc-elt"
nyutu_uuid: "db4bb2e6-a2de-426c-9c02-e22ff2754c0e"
artifact_type: "Walkthrough"
tags:
  - "bigquery"
  - "python"
  - "testing"
  - "walkthrough"
source_uri: "specs/coc_elt_20260712_configure_bq_client_project_walkthrough.md"
---

# Walkthrough - Configure BigQuery Client Project

This walkthrough document records the completed tasks to configure the Google Cloud BigQuery client with the target `project_id` to ensure load jobs run in the configured Data Project.

## Steps Executed

### 1. Code Modification in `src/coc_elt/bq_client.py`
The `BigQueryIngester` constructor was updated to pass the `project_id` to the `bigquery.Client` constructor:

```python
# src/coc_elt/bq_client.py
class BigQueryIngester:
    def __init__(self, project_id: str, dataset_id: str):
        self.client = bigquery.Client(project=project_id)
        self.project_id = project_id
        self.dataset_id = dataset_id
```

### 2. Test Verification in `tests/test_bq_client.py`
Assertions were added to all relevant tests in `tests/test_bq_client.py` to verify that `bigquery.Client` was instantiated with `project="test-project"`:

* `test_ingest_batch_success`
* `test_ingest_batch_timezone_localization`
* `test_ingest_batch_load_job_exception`
* `test_ingest_batch_load_job_errors`

For example:
```python
mock_bq_client_cls.assert_called_once_with(project="test-project")
```

### 3. Test Execution and Validation
The test suite was executed locally using `uv run pytest`:

```bash
$ uv run pytest
============================= test session starts ==============================
...
tests/test_api_client.py ....                                            [ 30%]
tests/test_bq_client.py ....                                             [ 61%]
tests/test_logging.py ..                                                 [ 76%]
tests/test_main.py ...                                                   [100%]

============================== 13 passed in 0.18s ==============================
```

All 13 tests passed successfully.
