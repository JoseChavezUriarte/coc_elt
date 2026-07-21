---
title: "Create wars Table in coc_silver Walkthrough"
project_id: "coc-elt"
nyutu_uuid: "3a26943b-1dca-48dc-80ed-114fb416190d"
artifact_type: "Data Engineering Pattern"
tags:
  - "dataform"
  - "incremental-load"
  - "unnesting"
  - "deduplication"
  - "walkthrough"
source_uri: "specs/coc-elt_20260721_create-wars-table_walkthrough.md"
---

### Execution Context
- **Timestamp**: 2026-07-21T11:40:43-05:00
- **Objective**: Implement the approved plan to create a denormalized, incremental Dataform table `coc_silver.wars` to process raw clan war payloads from `coc_bronze.coc_current_war` at attack-level granularity.

### Executed Commands
- `pnpm exec dataform compile` (in the repository root to verify SQLX compilation)

### State Mutations
- **Created**:
  - `definitions/wars.sqlx`
  - `specs/coc-elt_20260721_create-wars-table_walkthrough.md`
- **Modified**:
  - `specs/coc-elt_20260721_create-wars-table_implementation_plan.md`
  - `specs/nyutu_index.json`

### Architectural Decisions (ADR) and Logic Flow

#### 1. Unnesting Mechanism
To project records at the **attack level**, the JSON arrays containing members and their attacks must be unnested. We use implicit `CROSS JOIN UNNEST` (comma syntax) for both member lists and attack lists:
- For clan member attacks:
  ```sql
  UNNEST(JSON_QUERY_ARRAY(payload.clan.members)) AS member,
  UNNEST(JSON_QUERY_ARRAY(member.attacks)) AS attack
  ```
- For opponent member attacks:
  ```sql
  UNNEST(JSON_QUERY_ARRAY(payload.opponent.members)) AS member,
  UNNEST(JSON_QUERY_ARRAY(member.attacks)) AS attack
  ```
Using `CROSS JOIN UNNEST` ensures that only players who actually performed attacks are included, aligning with the target table granularity. The `bestOpponentAttack` field is ignored during unnesting as required.

#### 2. Deduplication Strategy
To address raw data redundancies and multiple API snapshots per day, a two-stage deduplication strategy is employed:
- **Stage 1 (War Payload Level)**: In the `latest_war_payloads` CTE, payloads are partitioned by the extraction date, home clan tag, and opponent tag:
  ```sql
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY
      DATE(extracted_at),
      JSON_VALUE(payload.clan.tag),
      JSON_VALUE(payload.opponent.tag)
    ORDER BY
      extracted_at DESC
  ) = 1
  ```
  This selects only the latest snapshot of the war for any given day.
- **Stage 2 (Attack Level)**: After unioning clan and opponent attacks, a final `QUALIFY` clause is applied:
  ```sql
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY extracted_date, ptag, defender_tag
    ORDER BY extracted_at DESC, attack_order DESC
  ) = 1
  ```
  This filters out any duplicate records resulting from overlapping daily snapshots of the same attack, preserving the latest state based on `extracted_at` and `attack_order`.

#### 3. FinOps and Partitioning
The table is partitioned daily on `extracted_date` and clustered on `["extracted_date", "ptag", "state", "teamSize"]`. In incremental mode, partition lookback is limited to the last 2 days to optimize costs:
```sql
updatePartitionFilter: "extracted_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)"
```
And inside the CTE:
```sql
${when(incremental(), "WHERE extracted_at >= TIMESTAMP(DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY))")}
```

#### 4. Validation Assertions
The Dataform model defines assertions in the config block to enforce the integrity of the unique composite key:
- **Unique Key Assertion**: Validates that `["extracted_date", "ptag", "defender_tag"]` is unique across all rows in the dataset.
- **Non-Null Assertion**: Asserts that `["extracted_date", "ptag", "defender_tag"]` do not contain null values.
These assertions prevent duplicate or malformed attack entries from propagating downstream.
