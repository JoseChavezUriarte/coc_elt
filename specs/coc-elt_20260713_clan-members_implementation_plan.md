---
title: "Create Daily Incremental Upsert Model for clan_members in Dataform"
project_id: "coc-elt"
nyutu_uuid: "0b685bf0-743b-4f0a-aae5-4fa11d7bc700"
artifact_type: "Architectural Decision"
tags:
  - "dataform"
  - "incremental-load"
  - "bigquery"
  - "implementation_plan"
source_uri: "specs/coc-elt_20260713_clan-members_implementation_plan.md"
---

# Implementation Plan: Daily Incremental Upsert Model `clan_members` in Dataform (Revised)

This plan details the creation of the SQLX model `clan_members` under the `coc_silver` schema. The model performs daily incremental updates and upserts on the member profile data fetched from the bronze dataset.

---

## 1. Requirements (WHAT is needed) - EARS Notation

The following requirements define the behavior and structure of the `clan_members` model:

*   **R1 (Incremental Model Type)**: The system MUST define a Dataform model configured with `type: "incremental"` to support incremental merge runs.
*   **R2 (Target Table & Schema)**: The system MUST write the output table named `clan_members` to the `coc_silver` schema.
*   **R3 (Unique Constraint)**: The system MUST enforce a unique composite key constraint using `["extracted_date", "ptag"]` for merge operations.
*   **R4 (BigQuery Partitioning & Clustering)**: The system MUST partition the target table on the `extracted_date` field AND cluster the table by `["ptag", "role"]` in BigQuery.
*   **R5 (Source Reference)**: WHEN compiling the Dataform model, the system MUST resolve the dependency to the bronze source `coc_members` using `${ref("coc_members")}`.
*   **R6 (Column Projections & Casting)**: The system MUST project and cast the following mapped columns from the JSON payload:
    *   `extracted_date` (as `DATE`)
    *   `ptag` (as `STRING`)
    *   `pname` (as `STRING`)
    *   `role` (as `STRING`)
    *   `exp_level` (as `INT64`)
    *   `trophies` (as `INT64`)
    *   `war_stars` (as `INT64`)
    *   `thl` (as `INT64`)
    *   `bhl` (as `INT64`)
    *   `capital_contrib` (as `INT64`)
    *   `btrophies` (as `INT64`, mapping either `builderBaseTrophies` or `versusTrophies`)
*   **R7 (FinOps Compliant Incremental Logic)**: WHEN running in incremental mode, the system MUST filter input records against the native timestamp column using a static 2-day lookback window: `${when(incremental(), "WHERE extracted_at >= TIMESTAMP(DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY))")}`. This ensures partition pruning is fully leveraged without function wraps on partition columns.
*   **R8 (Handling Missing/Null Keys)**: IF a required field like `ptag` or `extracted_date` is null in the input row, THEN the system MUST fail the uniqueness validation.

---

## 2. Technical Decisions (HOW it will be built)

### 2.1 Files Created
*   **Create**: `dataform/definitions/clan_members.sqlx`

### 2.2 Model Configuration (Signatures)
The model configuration block will be defined at the top of `dataform/definitions/clan_members.sqlx`:
```sql
config {
  type: "incremental",
  schema: "coc_silver",
  uniqueKey: ["extracted_date", "ptag"],
  bigquery: {
    partitionBy: "extracted_date",
    clusterBy: ["ptag", "role"],
    updatePartitionFilter: "extracted_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)"
  }
}
```

### 2.3 SQL Selection and Mapping
```sql
SELECT
  DATE(extracted_at) AS extracted_date,
  JSON_VALUE(payload.tag) AS ptag,
  JSON_VALUE(payload.name) AS pname,
  JSON_VALUE(payload.role) AS role,
  SAFE_CAST(JSON_VALUE(payload.expLevel) AS INT64) AS exp_level,
  SAFE_CAST(JSON_VALUE(payload.trophies) AS INT64) AS trophies,
  SAFE_CAST(JSON_VALUE(payload.warStars) AS INT64) AS war_stars,
  SAFE_CAST(JSON_VALUE(payload.townHallLevel) AS INT64) AS thl,
  SAFE_CAST(JSON_VALUE(payload.builderHallLevel) AS INT64) AS bhl,
  SAFE_CAST(JSON_VALUE(payload.clanCapitalContributions) AS INT64) AS capital_contrib,
  COALESCE(
    SAFE_CAST(JSON_VALUE(payload.builderBaseTrophies) AS INT64),
    SAFE_CAST(JSON_VALUE(payload.versusTrophies) AS INT64)
  ) AS btrophies
FROM
  ${ref("coc_members")}
${when(incremental(), "WHERE extracted_at >= TIMESTAMP(DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY))")}
```

### 2.4 Error Handling
*   **Missing Fields**: `SAFE_CAST` prevents query failure if fields such as `expLevel` or `trophies` contain non-integer string representations or are missing from the raw JSON payload.
*   **Schema Evolution**: `COALESCE` handles the mapping of Builder Base trophies, supporting both modern `builderBaseTrophies` and legacy `versusTrophies` structures.

### 2.5 Compilation, Testing, and Execution Guide
*   **Compilation**:
    *   To compile the project and check for syntax errors or unresolved dependencies, run:
        ```bash
        cd dataform
        dataform compile
        ```
*   **Execution**:
    *   To execute a dry-run to verify target permissions and syntax without mutating data, run:
        ```bash
        dataform run --actions clan_members --dry-run
        ```
    *   To execute the actual build and load the data, run:
        ```bash
        dataform run --actions clan_members
        ```
*   **Testing**:
    *   Add Dataform assertions to the config block of `clan_members.sqlx` to enforce quality:
        ```sql
        config {
          type: "incremental",
          schema: "coc_silver",
          uniqueKey: ["extracted_date", "ptag"],
          bigquery: {
            partitionBy: "extracted_date",
            clusterBy: ["ptag", "role"],
            updatePartitionFilter: "extracted_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)"
          },
          assertions: {
            uniqueKey: ["extracted_date", "ptag"],
            nonNull: ["extracted_date", "ptag"]
          }
        }
        ```

---

## 3. Implementation Tasks (Concrete STEPS)

*   [x] T1 — Create and configure `dataform/definitions/clan_members.sqlx` with target schema, partitioning, clustering, unique key, and data quality assertions.
*   [x] T2 — Implement the SQL query mapping fields from `coc_members` with SAFE_CAST and a static 2-day incremental filter.
*   [x] T3 — Compile the Dataform project locally using `dataform compile` to verify schema definitions and references.
*   [x] T4 — Execute a dry run of the model creation and verify the generated SQL compilation query.
*   [x] T5 — Execute a full build of `clan_members` and query the output to verify partitioned daily records.
