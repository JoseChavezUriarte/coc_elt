---
title: "Filter Duplicate Clan Members and Retrieve Latest Daily Update"
project_id: "coc-elt"
nyutu_uuid: "b75c87ca-7314-4a7c-85b6-5e6621159159"
artifact_type: "Architectural Decision"
tags:
  - "dataform"
  - "bigquery"
  - "clan-members"
  - "deduplication"
  - "implementation_plan"
source_uri: "specs/coc-elt_20260714_filter-clan-members-duplicates_implementation_plan.md"
---

# Implementation Plan - Filter Duplicate Clan Members and Retrieve Latest Daily Update

This implementation plan details the query rewrite of `definitions/clan_members.sqlx` to filter duplicate daily records and retrieve only the latest update of the day for each player.

---

## 1. Requirements (WHAT is needed) - EARS Notation

The following requirements define the behavior and structure of the updated model:

*   **R1 (Deduplication Logic)**: The system MUST filter daily records to retrieve only the latest update of the day for each player based on their extraction timestamp in descending order.
*   **R2 (Parsing CTE)**: The system MUST define a common table expression (CTE) named `parsed_members` to extract and cast fields from the raw JSON payload of `coc_members`.
*   **R3 (Incremental Partition Pruning Filter)**: WHILE in incremental mode, the system MUST filter input records in `parsed_members` using a 2-day lookback window: `WHERE extracted_at >= TIMESTAMP(DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY))`.
*   **R4 (Ranking CTE)**: The system MUST define a common table expression (CTE) named `ranked_members` utilizing `ROW_NUMBER() OVER (PARTITION BY extracted_date, ptag ORDER BY extracted_at DESC)` to rank duplicate player records within each day.
*   **R5 (Filtering Ranked Records)**: The system MUST select only the rows from `ranked_members` where `row_num = 1`.
*   **R6 (Output Columns)**: The final selection MUST return the columns: `extracted_date`, `ptag`, `pname`, `role`, `exp_level`, `trophies`, `war_stars`, `thl`, `bhl`, `capital_contrib`, and `btrophies`.
*   **R7 (Unique Key Assertion)**: The system MUST enforce a unique composite key assertion using `["extracted_date", "ptag"]`.
*   **R8 (Compilation Verification)**: The system MUST successfully compile using `pnpm exec dataform compile` at the project root.
*   **R9 (Uniqueness Validation Failure)**: IF there is more than one record with the same `(extracted_date, ptag)` combination after filtering, THEN the unique key assertion of the model MUST fail.

---

## 2. Technical Decisions (HOW it will be built)

### 2.1 Files Modified
*   **Modify**: `definitions/clan_members.sqlx`

### 2.2 Model Configuration (Signatures)
The model configuration remains the same:
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

### 2.3 SQL Query Refactoring
The query inside `definitions/clan_members.sqlx` will be updated to:
```sql
WITH parsed_members AS (
  SELECT
    extracted_at,
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
),

ranked_members AS (
  SELECT
    *,
    ROW_NUMBER() OVER (PARTITION BY extracted_date, ptag ORDER BY extracted_at DESC) AS row_num
  FROM
    parsed_members
)

SELECT
  extracted_date,
  ptag,
  pname,
  role,
  exp_level,
  trophies,
  war_stars,
  thl,
  bhl,
  capital_contrib,
  btrophies
FROM
  ranked_members
WHERE
  row_num = 1
```

### 2.4 Error Handling
*   **Payload Schema Anomaly**: `SAFE_CAST` and `COALESCE` are used to prevent query failures when unexpected payload structures or data formats occur.
*   **Uniqueness Validation**: Configured Dataform assertions `uniqueKey` and `nonNull` will validate that after deduplication there are no duplicate players per day.

### 2.5 Discarded Alternatives
*   **Alternative 1: Using `GROUP BY` and `MAX(extracted_at)`**
    *   *Discard Reason*: Discarded because `ROW_NUMBER() OVER (...)` is much cleaner and avoids a self-join back to the source table on `extracted_at` and `ptag` to retrieve the rest of the attributes (like name, trophies, role, etc.). A self-join on a large dataset is computationally expensive and hard to optimize.
*   **Alternative 2: Using `QUALIFY ROW_NUMBER() OVER (...) = 1`**
    *   *Discard Reason*: Using explicit CTEs (`parsed_members` and `ranked_members`) makes the query logic more readable, directly satisfies the user's specific CTE structure request, and complies with standard Dataform SQL parser support.

---

## 3. Implementation Tasks (Concrete STEPS)

- [x] T1 — Refactor query in `definitions/clan_members.sqlx` to use `parsed_members` and `ranked_members` CTEs.
- [x] T2 — Run `pnpm exec dataform compile` at the project root to verify compilation.
- [x] T3 — Verify unique assertions and dry-run query.
