---
title: "Resolve BigQuery Load Job Text Mode Error Walkthrough"
project_id: "coc-elt"
nyutu_uuid: "42f069bc-2fd6-42ed-b4c3-96a851ebc36b"
artifact_type: "Bug Fix Walkthrough"
tags:
  - "bigquery"
  - "bug-fix"
  - "walkthrough"
source_uri: "specs/coc_elt_20260712_resolve_bq_load_binary_mode_walkthrough.md"
---

# Walkthrough: Resolve BigQuery Load Job Text Mode Error

This document details the changes and actions performed to implement the fix for the BigQuery load job text mode error.

---

## 1. Modifications in Codebase

### Source Code: [bq_client.py](file:///home/scheveningen/documents/proyectos/coc_elt/src/coc_elt/bq_client.py)
*   **File Open Mode:** Modified `tempfile.NamedTemporaryFile` mode from `'w+'` to `'w+b'` to open the temporary file in binary read/write mode.
*   **Encoding Rows:** Encoded the JSON-serialized row string to a UTF-8 byte representation before writing to the binary file.

```diff
-        with tempfile.NamedTemporaryFile(mode='w+', suffix='.json') as tmp_file:
+        with tempfile.NamedTemporaryFile(mode='w+b', suffix='.json') as tmp_file:
             for record in records:
                 row = {
                     "extracted_at": extracted_at.isoformat(),
                     "payload": record
                 }
-                tmp_file.write(json.dumps(row) + "\n")
+                tmp_file.write((json.dumps(row) + "\n").encode("utf-8"))
```

### Test Suite: [test_bq_client.py](file:///home/scheveningen/documents/proyectos/coc_elt/tests/test_bq_client.py)
*   **Decoding Content:** Since `captured_content` is now read as bytes from the binary file, updated the test assertions to decode `captured_content` to a UTF-8 string prior to stripping and parsing with `json.loads`.

```diff
@@ -32,3 +32,3 @@
     
-    parsed = json.loads(captured_content.strip())
+    parsed = json.loads(captured_content.decode("utf-8").strip())
     assert parsed["extracted_at"] == "2026-07-11T12:00:00+00:00"
@@ -65,3 +65,3 @@
     
-    parsed = json.loads(captured_content.strip())
+    parsed = json.loads(captured_content.decode("utf-8").strip())
     assert parsed["extracted_at"] == "2026-07-11T12:00:00+00:00"
```

---

## 2. Test Verification

The unit test suite was executed using `uv run pytest`. All tests passed successfully:

```text
============================= test session starts ==============================
platform linux -- Python 3.13.9, pytest-9.1.1, pluggy-1.6.0
rootdir: /home/scheveningen/documents/proyectos/coc_elt
configfile: pyproject.toml
plugins: cov-7.1.0
collecting ... collected 13 items

tests/test_api_client.py ....                                            [ 30%]
tests/test_bq_client.py ....                                             [ 61%]
tests/test_logging.py ..                                                 [ 76%]
tests/test_main.py ...                                                   [100%]

============================== 13 passed in 0.19s ==============================
```

---

## 3. Implementation Plan Verification

All tasks outlined in [coc_elt_20260712_resolve_bq_load_binary_mode_implementation_plan.md](file:///home/scheveningen/documents/proyectos/coc_elt/specs/coc_elt_20260712_resolve_bq_load_binary_mode_implementation_plan.md) have been completed and marked as checked off:

*   [x] **T1** — Modify `src/coc_elt/bq_client.py` to use `mode='w+b'` in `tempfile.NamedTemporaryFile`.
*   [x] **T2** — Modify `src/coc_elt/bq_client.py` to write UTF-8 encoded bytes to `tmp_file`.
*   [x] **T3** — Modify `tests/test_bq_client.py` to decode `captured_content` from bytes to a UTF-8 string before calling `json.loads`.
*   [x] **T4** — Execute `uv run pytest` to verify the local unit tests pass.
