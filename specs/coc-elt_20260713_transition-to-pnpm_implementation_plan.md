---
title: "Transition Dataform Package Management from npm to pnpm"
project_id: "coc-elt"
nyutu_uuid: "de19cf39-ee03-42ad-93db-44066095695d"
artifact_type: "Architectural Decision"
tags:
  - "dataform"
  - "pnpm"
  - "package-manager"
  - "implementation_plan"
source_uri: "specs/coc-elt_20260713_transition-to-pnpm_implementation_plan.md"
---

# Implementation Plan: Transition Dataform Package Management from npm to pnpm

This plan outlines the steps required to transition the Dataform package management from npm to pnpm in the `coc-elt` repository, ensuring that dependencies are correctly installed and Dataform compiles successfully.

---

## 1. Requirements (WHAT is needed) - EARS Notation

- **R1 (NPM Lockfile Removal)**: The system MUST delete `dataform/package-lock.json` from the repository.
- **R2 (NPM Node Modules Removal)**: The system MUST delete the `dataform/node_modules/` directory to avoid conflicts.
- **R3 (PNPM Installation)**: WHEN installing dependencies inside the `dataform/` directory, the system MUST use `pnpm install` to resolve and install node modules.
- **R4 (PNPM Lockfile Generation)**: WHEN `pnpm install` is executed, the system MUST generate a `dataform/pnpm-lock.yaml` file.
- **R5 (Compilation Verification)**: The system MUST successfully compile the Dataform project using `pnpm exec dataform compile` inside the `dataform/` directory.
- **R6 (Version Control)**: The system MUST stage and commit the deletion of `dataform/package-lock.json` and the addition of `dataform/pnpm-lock.yaml` using Git.
- **R7 (Clean Environment Recovery - Sad Path)**: IF the `pnpm install` or compilation step fails, THEN the system MUST restore `dataform/package-lock.json` to its original state.

---

## 2. Technical Decisions (HOW it will be built)

### Files Impacted
- **Deleted**:
  - `dataform/package-lock.json`
- **Created**:
  - `dataform/pnpm-lock.yaml`
- **Modified**:
  - `dataform/node_modules/` (not tracked in Git)

### Signatures
- CLI Commands used:
  - Remove files: `rm -f dataform/package-lock.json` and `rm -rf dataform/node_modules/`
  - Install dependencies: `cd dataform && pnpm install`
  - Compile check: `cd dataform && pnpm exec dataform compile`

### Error Handling
- IF any step fails, the system rollback is performed using `git checkout -- dataform/package-lock.json`.

### Discarded Alternatives
- **Alternative 1: Keep both `package-lock.json` and `pnpm-lock.yaml`**
  - *Reason Discarded*: Maintaining duplicate lockfiles leads to build desynchronization, conflicts, and dependency mismatch across environments.
- **Alternative 2: Use yarn**
  - *Reason Discarded*: The project is adopting `pnpm` for faster, efficient workspace caching and strict node_modules handling.

---

## 3. Implementation Tasks (Concrete STEPS)

- [x] T1 — Delete `dataform/package-lock.json`.
- [x] T2 — Delete `dataform/node_modules/` directory.
- [x] T3 — Run `pnpm install` inside the `dataform/` directory to generate `pnpm-lock.yaml` and install dependencies.
- [x] T4 — Run `pnpm exec dataform compile` inside the `dataform/` directory to verify compilation.
- [x] T5 — Stage and commit the changes (`package-lock.json` deletion and `pnpm-lock.yaml` addition).
