---
title: "Relocate Dataform definitions Folder to Root to Resolve 400 Bad Request Error"
project_id: "coc-elt"
nyutu_uuid: "6de4f31a-a83a-4634-9cb4-7004acaaa52d"
artifact_type: "Architectural Decision"
tags:
  - "dataform"
  - "project-structure"
  - "bug-fix"
  - "implementation_plan"
source_uri: "specs/coc-elt_20260714_relocate-definitions-to-root_implementation_plan.md"
---

# Implementation Plan: Relocate Dataform definitions Folder to Root

This implementation plan details the relocation of the `definitions/` directory from `dataform/definitions/` to the repository root. This ensures that the Dataform compiler natively discovers and compiles the SQLX models, resolving the 400 Bad Request error ("At least one action must be selected").

---

## 1. Requirements (WHAT is needed) - EARS Notation

### 1.1 Happy Path Scenarios
- **R1 (Ubiquitous):** The system MUST relocate the `dataform/definitions/` directory to the root of the repository as `definitions/`.
  - *Verification:* Check that the directory `definitions/` exists at the project root and contains `sources.js` and `clan_members.sqlx`.
- **R2 (Ubiquitous):** The system MUST delete the `dataform/` directory and any remaining contents within it.
  - *Verification:* Verify that the `dataform/` directory no longer exists in the project root.
- **R3 (Ubiquitous):** The system MUST keep the `.dataformignore` configuration file at the root of the project to isolate Python (`src/`, `tests/`, `scripts/`, `.venv/`) and Terraform (`terraform/`, `.terraform/`) directories from being scanned by the Dataform compiler.
  - *Verification:* Ensure the file `.dataformignore` remains at the root and its content remains unchanged.
- **R4 (Ubiquitous):** The system MUST execute package installation using `pnpm install` at the root of the project.
  - *Verification:* Verify that the `node_modules` directory exists at the root and dependencies are fully resolved.
- **R5 (Ubiquitous):** The system MUST compile exactly 3 Dataform actions successfully when running `pnpm exec dataform compile` at the project root.
  - *Verification:* Run `pnpm exec dataform compile` at the project root and verify the output displays success with 3 compiled actions.

### 1.2 Sad Path Scenarios (Unwanted Events)
- **R6 (Unwanted):** IF the Dataform local compilation fails, THEN the system MUST report the compilation errors and halt.
  - *Verification:* Intentionally introduce a syntax error in a `.sqlx` file, run the compile command, and verify that the command fails with a non-zero exit code and output logs are printed.

### 1.3 Edge Cases
- **R7 (State):** WHILE checking out or building in external environments, the system MUST NOT require symlinks or path aliases to locate the `definitions/` directory.
  - *Verification:* Ensure no symbolic links exist in the repository structure.

---

## 2. Technical Decisions (HOW it will be built)

### 2.1 Files Impacted
*   **Moved**:
    *   `dataform/definitions/` directory to `definitions/`
*   **Deleted**:
    *   `dataform/` directory
*   **Preserved**:
    *   `.dataformignore` (at root)
    *   `dataform.json` (at root)
    *   `package.json` (at root)
    *   `pnpm-lock.yaml` (at root)
    *   `pnpm-workspace.yaml` (at root)

### 2.2 Analysis and Design
The Dataform compiler expects the `definitions/` directory to be located in the same directory as `dataform.json`. Since `dataform.json` was previously moved to the root to satisfy GCP's repository root requirement, leaving `definitions/` under `dataform/definitions/` led to an empty compilation (0 actions). When executing an empty compilation in Dataform, the API returns a 400 Bad Request error. Relocating `definitions/` to the root solves this.

### 2.3 Discarded Alternatives
*   **Alternative 1: Configured path override in `dataform.json`**
    *   *Reason for Discarding:* Dataform does not support customizing the name or path of the `definitions/` folder via config settings; it hardcodes the search for `definitions/` relative to the root project configuration.
*   **Alternative 2: Creating a symlink from `definitions` to `dataform/definitions`**
    *   *Reason for Discarding:* Symbolic links are not consistently resolved or supported when cloned by the managed Google Cloud Dataform service and can cause cross-platform permission or path resolution errors.

---

## 3. Implementation Tasks (Concrete STEPS)

- [x] T1 — Move the `dataform/definitions/` directory to the root of the repository as `definitions/`.
- [x] T2 — Delete the `dataform/` directory and any of its contents.
- [x] T3 — Run `pnpm install` at the root of the project to configure dependencies.
- [x] T4 — Execute `pnpm exec dataform compile` at the project root to verify all 3 actions compile successfully.
- [x] T5 — Stage and commit all changes using Git.
