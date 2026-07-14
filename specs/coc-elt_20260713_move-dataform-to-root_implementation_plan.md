---
title: "Resolve Dataform Compile 404 Not Found by Moving Configuration to Project Root"
project_id: "coc-elt"
nyutu_uuid: "0d6fc81a-cf90-4333-af46-ce388a9ed56a"
artifact_type: "Architectural Decision"
tags:
  - "dataform"
  - "project-structure"
  - "package-management"
  - "implementation_plan"
source_uri: "specs/coc-elt_20260713_move-dataform-to-root_implementation_plan.md"
---

# Implementation Plan: Move Dataform Configuration to Project Root (Final - Hybrid Isolation Strategy)

This plan details the steps required to resolve the 404 Not Found error during the Dataform compilation step in GCP Workflows. By relocating only the configuration and package management files to the project root and isolating infrastructure/Python directories via `.dataformignore`, Dataform will natively recurse into and compile the analytical models inside the preserved `dataform/definitions/` directory without requiring path-resolution aliases.

---

## 1. Requirements (WHAT is needed) - EARS Notation

The system must satisfy the following Dataform structural and isolation requirements:

*   **R1 (Package JSON Relocation)**: The system MUST relocate `dataform/package.json` to the project root path `package.json`.
*   **R2 (Dataform JSON Relocation)**: The system MUST relocate `dataform/dataform.json` to the project root path `dataform.json`.
*   **R3 (PNPM Lockfile Relocation)**: The system MUST relocate `dataform/pnpm-lock.yaml` to the project root path `pnpm-lock.yaml`.
*   **R4 (PNPM Workspace Relocation)**: The system MUST relocate `dataform/pnpm-workspace.yaml` to the project root path `pnpm-workspace.yaml`.
*   **R5 (Subdirectory Preservation)**: The system MUST NOT relocate the physical `dataform/definitions/` directory or delete the `dataform/` directory.
*   **R6 (Compiler Isolation)**: The system MUST create a `.dataformignore` file at the root of the project to prevent the Dataform compiler from scanning Python, Terraform, and other infrastructure directories.
*   **R7 (Compiler Ignore Scope)**: The `.dataformignore` file MUST contain, at minimum, the following patterns:
    *   `terraform/`
    *   `.terraform/`
    *   `src/`
    *   `scripts/`
    *   `tests/`
    *   `specs/`
    *   `__pycache__/`
    *   `.venv/`
*   **R8 (Local Dependency Installation)**: WHEN executing dependency installation, the system MUST run `pnpm install` at the project root.
*   **R9 (Compilation Verification)**: WHEN verifying compilation, the system MUST run `pnpm exec dataform compile` at the project root.
*   **R10 (Clean Environment Recovery)**: IF the local dependency installation or compilation verification fails, THEN the system MUST revert all changes using Git to restore the original project structure.

---

## 2. Technical Decisions (HOW it will be built)

### 2.1 Files Impacted
*   **Relocated / Created**:
    *   `package.json` (from `dataform/package.json`)
    *   `dataform.json` (from `dataform/dataform.json`)
    *   `pnpm-lock.yaml` (from `dataform/pnpm-lock.yaml`)
    *   `pnpm-workspace.yaml` (from `dataform/pnpm-workspace.yaml`)
    *   `.dataformignore` (new file at root)
*   **Preserved**:
    *   `dataform/` (containing `definitions/` and its SQLX analytical models)

### 2.2 Analysis and Design
The 404 Not Found error occurs because the GCP Dataform service requires `package.json` and `dataform.json` to reside at the root of the connected Git repository. Specifying a subdirectory is not supported.

By placing the configuration files at the project root and creating a `.dataformignore` file, we establish a secure project boundary. Dataform's compiler recursively scans the workspace directory. Since the `dataform/` folder is not ignored in `.dataformignore`, the compiler will naturally traverse the folder structure and discover the analytical `.sqlx` models residing inside `dataform/definitions/` without requiring symbolic links. This eliminates path-resolution risks and cross-platform compatibility issues in managed cloud environments.

### 2.3 CLI Commands and Operations
*   Moving config and lockfiles:
    ```bash
    mv dataform/package.json package.json
    mv dataform/dataform.json dataform.json
    mv dataform/pnpm-lock.yaml pnpm-lock.yaml
    mv dataform/pnpm-workspace.yaml pnpm-workspace.yaml
    ```
*   Creating `.dataformignore` at root:
    ```text
    terraform/
    .terraform/
    src/
    scripts/
    tests/
    specs/
    __pycache__/
    .venv/
    ```
*   Installing packages and compiling:
    ```bash
    pnpm install
    pnpm exec dataform compile
    ```

### 2.4 Error Handling and Rollback
*   If installation or verification fails, the project state will be reverted to the last clean Git commit:
    ```bash
    git checkout -- .
    rm -f .dataformignore
    git clean -fd
    ```

---

## 3. Implementation Tasks (Concrete STEPS)

- [x] T1 — Relocate `dataform/package.json` to `package.json` at root.
- [x] T2 — Relocate `dataform/dataform.json` to `dataform.json` at root.
- [x] T3 — Relocate `dataform/pnpm-lock.yaml` to `pnpm-lock.yaml` at root.
- [x] T4 — Relocate `dataform/pnpm-workspace.yaml` to `pnpm-workspace.yaml` at root.
- [x] T5 — Create `.dataformignore` at the root of the project with the required compiler exclusion patterns.
- [x] T6 — Run `pnpm install` at the project root.
- [x] T7 — Run `pnpm exec dataform compile` at the project root to verify compilation.
- [x] T8 — Stage and commit all changes using Git.
- [x] T9 — Register and document the walkthrough in specs/nyutu_index.json and save as cornerstone in Nyutu.
