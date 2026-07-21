---
title: "Create clan_description Table in coc_silver Walkthrough"
project_id: "coc-elt"
nyutu_uuid: "30f1bae4-5ed2-4464-94d4-de6ee33e372d"
artifact_type: "Data Engineering Pattern"
tags:
  - "dataform"
  - "incremental-load"
  - "deduplication"
  - "walkthrough"
source_uri: "specs/coc-elt_20260721_create-clan-description-table_walkthrough.md"
---

### Execution Context
- **Timestamp**: 2026-07-21T13:36:05-05:00
- **Objective**: Implement the approved plan to create a denormalized, incremental Dataform table `coc_silver.clan_description` to process raw clan profile payloads from `coc_bronze.coc_clan` at clan tag granularity.

### Executed Commands
- `pnpm exec dataform compile` (in the repository root to verify SQLX compilation)

### State Mutations
- **Created**:
  - `definitions/clan_description.sqlx`
  - `specs/coc-elt_20260721_create-clan-description-table_walkthrough.md`
- **Modified**:
  - `specs/coc-elt_20260721_create-clan-description-table_implementation_plan.md`
  - `specs/nyutu_index.json`

### Architectural Decisions (ADR) and Logic Flow

#### 1. Schema Projection and Numeric/Boolean Casts
To protect the pipeline from failure on invalid data types, the SQLX model applies `SAFE_CAST` on numeric levels, points, members, and Boolean attributes (e.g., `isFamilyFriendly`, `isWarLogPublic`), projecting nested objects into flat attributes:
- `JSON_VALUE(payload.tag) AS tag`
- `SAFE_CAST(JSON_VALUE(payload.clanLevel) AS INT64) AS clanLevel`
- `SAFE_CAST(JSON_VALUE(payload.isFamilyFriendly) AS BOOL) AS isFamilyFriendly`

#### 2. Deduplication Strategy
To address raw data redundancies and multiple daily snapshots, the model implements daily deduplication:
- Partitioning by extraction date and clan tag:
  ```sql
  ROW_NUMBER() OVER (PARTITION BY extracted_date, tag ORDER BY extracted_at DESC) AS row_num
  ```
- Filtering in the final outer query with `WHERE row_num = 1`.
This ensures that only the latest API snapshot per clan tag is preserved for each day.

#### 3. FinOps and Partitioning
The table is partitioned daily on `extracted_date` (derived from `DATE(extracted_at)`) and clustered on `["extracted_date", "tag"]`. In incremental execution mode, partition updates are restricted to the last 2 days to optimize query scans and storage updates:
```sql
updatePartitionFilter: "extracted_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)"
```
And inside the CTE:
```sql
${when(incremental(), "WHERE extracted_at >= TIMESTAMP(DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY))")}
```

#### 4. Validation Assertions
The model configuration defines assertions to enforce the integrity of the unique composite key:
- **Unique Key Assertion**: Validates that `["extracted_date", "tag"]` is unique across all rows in the dataset.
- **Non-Null Assertion**: Asserts that `["extracted_date", "tag"]` does not contain null values.
