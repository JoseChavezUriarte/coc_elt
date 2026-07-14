---
title: "Resolve BigQuery Access Denied in Dataform Sources via Dynamic Database Resolution"
project_id: "coc-elt"
nyutu_uuid: "601b1686-8899-4d03-bcec-667b19ff3528"
artifact_type: "Bug Fix Logic"
tags:
  - "dataform"
  - "bigquery"
  - "implementation_plan"
source_uri: "specs/coc-elt_20260714_resolve-bigquery-access-denied-sources_implementation_plan.md"
---

# Implementation Plan: Resolve BigQuery Access Denied in Dataform Sources (Revised)

This implementation plan details the steps required to resolve the BigQuery access denied error in production by refactoring Dataform source definitions to leverage implicit database resolution.

---

## 1. Requirements (WHAT is needed) - EARS Notation

The system must satisfy the following requirements:

*   **R1 (Implicit Database Reference)**: The system MUST resolve the source databases implicitly by omitting the `database` parameter from the `declare()` blocks in `definitions/sources.js`.
*   **R2 (Happy Path Compilation)**: WHEN the compile command `pnpm exec dataform compile` is executed in the project root, the system MUST compile successfully without any compilation errors.
*   **R3 (Compilation Failure Handler)**: IF compilation fails due to syntactic or configuration issues, THEN the system MUST print the error logs and return a non-zero exit code.
*   **R4 (Dynamic Runtime Overrides)**: WHILE executing under runtime environments (such as GCP Workflows), the system MUST evaluate the source database to the active compilation `defaultDatabase`.

---

## 2. Technical Decisions (HOW it will be built)

### 2.1 Files Modified/Created
*   **Modify**: `definitions/sources.js` at [definitions/sources.js](file:///home/scheveningen/documents/proyectos/coc_elt/definitions/sources.js).
*   **Create**: `specs/coc-elt_20260714_resolve-bigquery-access-denied-sources_implementation_plan.md` (this implementation plan).

### 2.2 Analysis and Design
*   **Problem**: In production, Dataform is executed under a specific service account that does not have permissions to the `coc-data-analytics-project` BigQuery project. Instead, the actual data/tables reside in the workflow's own data project database: `swift-capsule-492817-a7`. Because `definitions/sources.js` hardcoded `database: "coc-data-analytics-project"`, Dataform ignored any compile-time or runtime project overrides and attempted to query `coc-data-analytics-project`, resulting in a BigQuery `Access Denied` error.
*   **Solution**: Completely omit the `database` parameter from the four `declare()` blocks in `definitions/sources.js`.
This leverages Dataform's implicit fallback mechanism, which naturally forces Dataform to fallback to the active compilation `defaultDatabase`. This ensures that:
  1. During local runs, it defaults to the value inside `dataform.json` (`coc-data-analytics-project`).
  2. During production GCP Workflow runs, it correctly resolves to the overridden default database passed by the workflow (i.e. `swift-capsule-492817-a7`).

### 2.3 Signatures & Code Changes

#### 2.3.1 Modify `definitions/sources.js`
Completely remove the `database` property from all declarations.

```diff
declare({
- database: "coc-data-analytics-project",
  schema: "coc_bronze",
  name: "coc_clan"
});
declare({
- database: "coc-data-analytics-project",
  schema: "coc_bronze",
  name: "coc_members"
});
declare({
- database: "coc-data-analytics-project",
  schema: "coc_bronze",
  name: "coc_current_war"
});
declare({
- database: "coc-data-analytics-project",
  schema: "coc_bronze",
  name: "coc_capital_raids"
});
```

---

## 3. Implementation Tasks (Concrete STEPS)

- [x] T1 — Create implementation plan file `specs/coc-elt_20260714_resolve-bigquery-access-denied-sources_implementation_plan.md`.
- [x] T2 — Refactor `definitions/sources.js` to delete the `database` parameter from all four `declare()` blocks.
- [x] T3 — Run compilation verification using `pnpm exec dataform compile` at the project root.
