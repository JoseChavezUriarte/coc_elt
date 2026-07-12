---
title: "Resolve BigQuery Load Job Text Mode Error"
project_id: "coc-elt"
nyutu_uuid: "bdd4925a-aceb-4812-9cb3-bda1f3e6933c"
artifact_type: "Bug Fix Logic"
tags:
  - "bigquery"
  - "bug-fix"
  - "implementation_plan"
source_uri: "specs/coc_elt_20260712_resolve_bq_load_binary_mode_implementation_plan.md"
---

# Implementation Plan: Resolve BigQuery Load Job Text Mode Error

This implementation plan outlines the steps required to resolve the BigQuery load job error caused by opening a temporary file in text mode instead of binary mode.

---

## 1. Requirements (WHAT is needed)

*   **R1 (Ubiquitous):** The system MUST open the temporary file in binary read/write mode using `mode='w+b'` in [bq_client.py](file:///home/scheveningen/documents/proyectos/coc_elt/src/coc_elt/bq_client.py).
*   **R2 (Ubiquitous):** The system MUST write records to the temporary file as UTF-8 encoded bytes in [bq_client.py](file:///home/scheveningen/documents/proyectos/coc_elt/src/coc_elt/bq_client.py).
*   **R3 (Event):** WHEN capturing file content in tests in [test_bq_client.py](file:///home/scheveningen/documents/proyectos/coc_elt/tests/test_bq_client.py), the testing framework MUST decode the binary data to a UTF-8 string before parsing it as JSON.
*   **R4 (Ubiquitous):** The system MUST pass all test cases in the test suite when executing `uv run pytest`.
*   **R5 (Unwanted):** IF encoding of a record fails, THEN the system MUST raise the underlying exception.

---

## 2. Technical Decisions (HOW it will be built)

### Files to Modify
*   `src/coc_elt/bq_client.py`
*   `tests/test_bq_client.py`

### Code Changes

#### 1. In `src/coc_elt/bq_client.py`
Change the file open mode to `w+b` and encode the JSON lines to UTF-8 before writing.

```python
# Change
with tempfile.NamedTemporaryFile(mode='w+', suffix='.json') as tmp_file:
# To
with tempfile.NamedTemporaryFile(mode='w+b', suffix='.json') as tmp_file:

# Change
tmp_file.write(json.dumps(row) + "\n")
# To
tmp_file.write((json.dumps(row) + "\n").encode("utf-8"))
```

#### 2. In `tests/test_bq_client.py`
Decode `captured_content` before parsing with `json.loads()`.

```python
# Change
parsed = json.loads(captured_content.strip())
# To
parsed = json.loads(captured_content.decode("utf-8").strip())
```

### Signatures
*   No new public signatures or CLI flags are introduced. Existing interface methods remain unchanged.

### Error Handling
*   No new custom error classes are introduced. If `json.dumps()` or byte encoding throws an error, the exception will propagate up, maintaining current error isolation design.

### Discarded Alternatives
*   **Alternative 1:** Using `tempfile.TemporaryFile` instead of `tempfile.NamedTemporaryFile`.
    *   *Reason for Discarding:* `NamedTemporaryFile` ensures compatibility with the Google Cloud client library, which may require a filesystem-backed descriptor or a file with a named attribute.
*   **Alternative 2:** Retaining `mode='w+'` and using an in-memory wrapper like `io.BytesIO`.
    *   *Reason for Discarding:* It introduces unnecessary memory overhead and complex streaming conversions. Directly using binary mode is the native and standard solution recommended by the BigQuery client library error message.

---

## 3. Implementation Tasks

- [x] T1 — Modify `src/coc_elt/bq_client.py` to use `mode='w+b'` in `tempfile.NamedTemporaryFile`.
- [x] T2 — Modify `src/coc_elt/bq_client.py` to write UTF-8 encoded bytes to `tmp_file`.
- [x] T3 — Modify `tests/test_bq_client.py` to decode `captured_content` from bytes to a UTF-8 string before calling `json.loads`.
- [x] T4 — Execute `uv run pytest` to verify the local unit tests pass.
