---
title: "Resolve scripts module import error in Cloud Build"
project_id: "coc-elt"
nyutu_uuid: "73b30ff2-e61d-41dc-b955-bc247000d471"
artifact_type: "Infrastructure Pattern"
tags:
  - "testing"
  - "cloudbuild"
  - "pythonpath"
  - "implementation_plan"
source_uri: "specs/coc-elt_20260713_resolve-scripts-import-error_implementation_plan.md"
---

# Implementation Plan: Resolve scripts module import error in Cloud Build

This plan details the changes required to resolve the `ModuleNotFoundError: No module named scripts` error during the unit testing stage in Cloud Build, ensuring robust module resolution across both local and CI/CD environments.

---

## 1. Requirements (WHAT is needed)

### 1.1 Happy Path
- **R1** (Ubiquitous): The system MUST run unit tests successfully during Cloud Build.
- **R2** (Event): WHEN the test suite is executed in Cloud Build, the test runner MUST successfully resolve and import python modules from the `scripts/` directory.

### 1.2 Sad Path
- **R3** (Unwanted): IF the repository root is not present in `sys.path` when running the tests, THEN the test script MUST programmatically resolve the repository root and prepend it to `sys.path` to avoid `ModuleNotFoundError`.
- **R4** (Unwanted): IF the test runner is executed from a working directory other than the project root, THEN the environment MUST fallback to the programmatically resolved path in the test file to successfully import the `scripts` module.

### 1.3 Edge Cases
- **R5** (State): WHILE executing tests from a nested directory (e.g. inside `tests/`), the test script MUST still successfully locate and import the `scripts` module.

---

## 2. Technical Decisions (HOW it will be built)

### 2.1 Files Affected
- **Modify**: `tests/test_backfill_from_mongo.py`
- **Modify**: `cloudbuild.yaml`

### 2.2 Signatures & Changes
- In `tests/test_backfill_from_mongo.py`:
  Prepend the repository root path to `sys.path` before importing `scripts.backfill_from_mongo`.
  ```python
  import sys
  from pathlib import Path
  sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
  ```
- In `cloudbuild.yaml`:
  Modify step `run-tests` to execute:
  ```bash
  PYTHONPATH=. uv run pytest
  ```

### 2.3 Error Handling
- The programmatic modification of `sys.path` dynamically references `__file__`, guaranteeing path correctness regardless of where the runner is invoked (either at root or inside `tests/`).
- Setting `PYTHONPATH=.` acts as a fail-safe environment variable to direct the interpreter to the root directory for imports.

### 2.4 Discarded Alternatives
- **Discarded Option**: Packaging the application using `pyproject.toml` configuration (e.g. editable install `pip install -e .` or custom `src` layout) was discarded. Since the project operates primarily as a set of ELT pipelines and scripts, introducing packaging overhead is unnecessary for fixing test import paths.

---

## 3. Implementation Tasks (Concrete STEPS)

- [x] T1 — Modify `tests/test_backfill_from_mongo.py` to add repository root path to `sys.path` prior to importing scripts.
- [x] T2 — Update the test run step in `cloudbuild.yaml` to use `PYTHONPATH=. uv run pytest`.
- [x] T3 — Validate the changes locally by running `uv run pytest`.
